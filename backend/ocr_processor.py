"""
OCR Processor Module for MediScan
Handles optical character recognition for medicine labels and prescriptions
Uses Google Cloud Vision API and EasyOCR as fallback
"""

import logging
import numpy as np
from PIL import Image
import io
import os
import re
import base64
import requests
from typing import Dict, List, Optional
import cv2

# Try to import EasyOCR as fallback
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCRProcessor:
    """
    OCR processor with multiple backends (Google Vision API + EasyOCR fallback)
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OCR processor

        Args:
            api_key: Google Vision API key (if not set in environment)
        """
        self.api_key = api_key or os.getenv("GOOGLE_VISION_API_KEY")
        self.endpoint = f"https://vision.googleapis.com/v1/images:annotate?key={self.api_key}" if self.api_key else None
        self.google_available = bool(self.api_key)

        # Initialize EasyOCR as fallback
        self.easyocr_reader = None
        if EASYOCR_AVAILABLE:
            try:
                self.easyocr_reader = easyocr.Reader(['en'])
                logger.info("EasyOCR initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR: {e}")

        if self.google_available:
            logger.info("Google Vision API key loaded successfully")
        elif self.easyocr_reader:
            logger.info("Using EasyOCR as primary OCR engine")
        else:
            logger.warning("No OCR engines available")

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results
        """
        try:
            # Convert PIL to OpenCV format
            img_array = np.array(image)
            if len(img_array.shape) == 3:
                img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            else:
                img_cv = img_array

            # Convert to grayscale
            if len(img_cv.shape) == 3:
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            else:
                gray = img_cv

            # Apply noise reduction
            denoised = cv2.medianBlur(gray, 3)

            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            # Convert back to PIL
            return Image.fromarray(thresh)

        except Exception as e:
            logger.warning(f"Image preprocessing failed, using original: {e}")
            return image

    def image_to_base64(self, image: Image.Image) -> str:
        """
        Convert image to base64 string for Vision API
        """
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        img_bytes = img_buffer.getvalue()
        return base64.b64encode(img_bytes).decode("utf-8")

    def extract_text_google_vision(self, image: Image.Image) -> Dict[str, any]:
        """
        Extract text using Google Vision API
        """
        if not self.google_available:
            logger.error("Google Vision API not available (missing API key)")
            return {'text': '', 'confidence': 0.0, 'structured_data': {}, 'raw_response': None}

        try:
            img_b64 = self.image_to_base64(image)
            payload = {
                "requests": [{
                    "image": {"content": img_b64},
                    "features": [
                        {"type": "DOCUMENT_TEXT_DETECTION"},
                        {"type": "TEXT_DETECTION"}
                    ]
                }]
            }

            resp = requests.post(self.endpoint, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()

            # Check for errors
            if "error" in data.get("responses", [{}])[0]:
                error = data["responses"][0]["error"]
                logger.error(f"Google Vision API error: {error}")
                return {'text': '', 'confidence': 0.0, 'structured_data': {}, 'raw_response': data}

            # Extract text - prefer fullTextAnnotation for better structure
            text = ""
            try:
                text = data["responses"][0]["fullTextAnnotation"]["text"]
            except (KeyError, IndexError):
                # Fallback to textAnnotations
                try:
                    annotations = data["responses"][0].get("textAnnotations", [])
                    if annotations:
                        text = annotations[0]["description"]
                except (KeyError, IndexError):
                    pass

            structured_data = self.structure_text(text)

            logger.info("Google Vision OCR extraction successful")
            return {
                'text': text,
                'confidence': 0.95,  # Vision API generally high confidence
                'structured_data': structured_data,
                'raw_response': data,
                'engine': 'google_vision'
            }

        except Exception as e:
            logger.error(f"Google Vision OCR extraction failed: {e}")
            return {'text': '', 'confidence': 0.0, 'structured_data': {}, 'raw_response': None}

    def extract_text_easyocr(self, image: Image.Image) -> Dict[str, any]:
        """
        Extract text using EasyOCR as fallback
        """
        if not self.easyocr_reader:
            logger.error("EasyOCR not available")
            return {'text': '', 'confidence': 0.0, 'structured_data': {}, 'raw_response': None}

        try:
            # Convert PIL to numpy array
            img_array = np.array(image)

            # Use EasyOCR
            results = self.easyocr_reader.readtext(img_array, detail=1)

            # Combine all text
            text_parts = []
            total_confidence = 0

            for (bbox, text, confidence) in results:
                if confidence > 0.3:  # Filter low confidence results
                    text_parts.append(text)
                    total_confidence += confidence

            text = '\n'.join(text_parts)
            avg_confidence = total_confidence / len(results) if results else 0

            structured_data = self.structure_text(text)

            logger.info("EasyOCR extraction successful")
            return {
                'text': text,
                'confidence': avg_confidence,
                'structured_data': structured_data,
                'raw_response': results,
                'engine': 'easyocr'
            }

        except Exception as e:
            logger.error(f"EasyOCR extraction failed: {e}")
            return {'text': '', 'confidence': 0.0, 'structured_data': {}, 'raw_response': None}

    def process_image(self, image_path: str = None, image: Image.Image = None, scan_type: str = "Medicine Label") -> Dict[str, any]:
        """
        Main method to process image and extract text

        Args:
            image_path: Path to image file (optional)
            image: PIL Image object (optional)  
            scan_type: Type of scan (Medicine Label, Prescription, etc.)

        Returns:
            Dictionary with extraction results
        """
        try:
            # Load image if path provided
            if image_path and not image:
                image = Image.open(image_path)
            elif not image:
                raise ValueError("Either image_path or image must be provided")

            # Preprocess image
            processed_image = self.preprocess_image(image)

            # Try Google Vision first, then EasyOCR as fallback
            if self.google_available:
                logger.info("Attempting Google Vision OCR...")
                result = self.extract_text_google_vision(processed_image)
                if result['text'] and result['confidence'] > 0.5:
                    return result
                else:
                    logger.warning("Google Vision returned low confidence, trying EasyOCR...")

            # Use EasyOCR as fallback
            if self.easyocr_reader:
                logger.info("Using EasyOCR...")
                result = self.extract_text_easyocr(processed_image)
                return result

            # No OCR engines available
            logger.error("No OCR engines available")
            return {
                'text': '', 
                'confidence': 0.0, 
                'structured_data': {}, 
                'raw_response': None,
                'engine': 'none',
                'error': 'No OCR engines available'
            }

        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return {
                'text': '', 
                'confidence': 0.0, 
                'structured_data': {}, 
                'raw_response': None,
                'engine': 'error',
                'error': str(e)
            }

    def structure_text(self, text: str) -> Dict[str, any]:
        """
        Extract structured information from OCR text
        """
        def extract_field(patterns, text, flags=re.IGNORECASE):
            for pattern in patterns:
                match = re.search(pattern, text, flags)
                if match:
                    return match.group(1).strip()
            return None

        structured = {}

        # Medicine name patterns
        name_patterns = [
            r'(?:name|medicine|drug)[:\s]*([^\n]+)',
            r'^([A-Z][A-Za-z\s]+)(?:\n|$)',  # First capitalized line
        ]
        structured['medicine_name'] = extract_field(name_patterns, text)

        # Dosage patterns
        dosage_patterns = [
            r'(?:dosage|dose|strength)[:\s]*([^\n]+)',
            r'(\d+\s*(?:mg|ml|g|mcg|units?))',
        ]
        structured['dosage'] = extract_field(dosage_patterns, text)

        # Expiry date patterns
        expiry_patterns = [
            r'(?:exp|expiry|expires?)[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
            r'(?:exp|expiry|expires?)[:\s]*([a-z]{3,9}\s*[0-9]{2,4})',
        ]
        structured['expiry_date'] = extract_field(expiry_patterns, text)

        # Manufacturing date patterns
        mfg_patterns = [
            r'(?:mfg|manufactured?|mfd)[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
            r'(?:mfg|manufactured?|mfd)[:\s]*([a-z]{3,9}\s*[0-9]{2,4})',
        ]
        structured['mfg_date'] = extract_field(mfg_patterns, text)

        # Batch number patterns
        batch_patterns = [
            r'(?:batch|lot)\s*(?:no|number)?[:\s]*([a-z0-9\-]+)',
            r'(?:b\.?no|l\.?no)[:\s]*([a-z0-9\-]+)',
        ]
        structured['batch_number'] = extract_field(batch_patterns, text)

        # Manufacturer patterns
        manufacturer_patterns = [
            r'(?:mfr?|manufacturer?|made\s*by)[:\s]*([^\n]+)',
        ]
        structured['manufacturer'] = extract_field(manufacturer_patterns, text)

        # Quantity patterns
        quantity_patterns = [
            r'(?:qty|quantity|count)[:\s]*(\d+)',
            r'(\d+)\s*(?:tablets?|capsules?|pills?)',
        ]
        structured['quantity'] = extract_field(quantity_patterns, text)

        return structured

    def is_available(self) -> Dict[str, bool]:
        """Check availability of OCR engines"""
        return {
            'google_vision': self.google_available,
            'easyocr': self.easyocr_reader is not None,
            'any_available': self.google_available or (self.easyocr_reader is not None)
        }

    def get_processing_stats(self) -> Dict[str, any]:
        """Get processing statistics and capabilities"""
        availability = self.is_available()

        primary_engine = 'none'
        if availability['google_vision']:
            primary_engine = 'google_vision'
        elif availability['easyocr']:
            primary_engine = 'easyocr'

        return {
            'primary_engine': primary_engine,
            'capabilities': {
                'high_accuracy': availability['google_vision'],
                'multilingual': availability['google_vision'] or availability['easyocr'],
                'structured_data': True,
                'confidence_scores': True
            },
            'availability': availability
        }
