"""
OCR Processor Module for MediScan
Handles optical character recognition for medicine labels and prescriptions
"""

import cv2
import numpy as np
from PIL import Image
import pytesseract
import easyocr
import re
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCRProcessor:
    """
    OCR processor for extracting text from medicine labels and prescriptions
    """
    
    def __init__(self, use_easyocr: bool = True):
        """
        Initialize OCR processor
        
        Args:
            use_easyocr: Whether to use EasyOCR (True) or Tesseract (False)
        """
        self.use_easyocr = use_easyocr
        
        if use_easyocr:
            try:
                self.reader = easyocr.Reader(['en', 'hi'])
                logger.info("EasyOCR initialized successfully")
            except Exception as e:
                logger.warning(f"EasyOCR initialization failed: {e}. Falling back to Tesseract")
                self.use_easyocr = False
        
        # Configure Tesseract
        try:
            # Update this path based on your system
            # Windows: r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            # Linux/Mac: Usually just 'tesseract'
            pytesseract.pytesseract.tesseract_cmd = 'tesseract'
        except Exception as e:
            logger.error(f"Tesseract configuration failed: {e}")
    
    def preprocess_image(self, image: Image.Image) -> np.ndarray:
        """
        Preprocess image for better OCR results
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed image as numpy array
        """
        # Convert PIL image to OpenCV format
        img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply noise reduction
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Apply thresholding to get binary image
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Apply dilation and erosion to remove noise
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel)
        
        # Resize image if too small
        height, width = processed.shape
        if width < 1000:
            scale_factor = 1000 / width
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            processed = cv2.resize(processed, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        return processed
    
    def extract_text_tesseract(self, image: np.ndarray) -> str:
        """
        Extract text using Tesseract OCR
        
        Args:
            image: Preprocessed image array
            
        Returns:
            Extracted text
        """
        try:
            # Configure Tesseract parameters for better accuracy
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-/.,:() '
            
            text = pytesseract.image_to_string(image, config=custom_config)
            return text.strip()
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            return ""
    
    def extract_text_easyocr(self, image: np.ndarray) -> str:
        """
        Extract text using EasyOCR
        
        Args:
            image: Preprocessed image array
            
        Returns:
            Extracted text
        """
        try:
            results = self.reader.readtext(image)
            
            # Combine all detected text
            text_lines = []
            for (bbox, text, prob) in results:
                if prob > 0.5:  # Only include high-confidence text
                    text_lines.append(text)
            
            return ' '.join(text_lines)
        except Exception as e:
            logger.error(f"EasyOCR failed: {e}")
            return ""
    
    def detect_text_regions(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect text regions in the image
        
        Args:
            image: Input image array
            
        Returns:
            List of bounding boxes (x, y, w, h)
        """
        # Apply edge detection
        edges = cv2.Canny(image, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        text_regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter out small regions
            if w > 50 and h > 20:
                text_regions.append((x, y, w, h))
        
        return text_regions
    
    def process_image(self, image: Image.Image) -> Dict[str, any]:
        """
        Main method to process image and extract text
        
        Args:
            image: PIL Image object
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        logger.info("Starting image processing...")
        
        # Preprocess image
        processed_image = self.preprocess_image(image)
        
        # Extract text
        if self.use_easyocr:
            extracted_text = self.extract_text_easyocr(processed_image)
        else:
            extracted_text = self.extract_text_tesseract(processed_image)
        
        # Detect text regions for additional processing
        text_regions = self.detect_text_regions(processed_image)
        
        # Clean and structure the extracted text
        cleaned_text = self.clean_text(extracted_text)
        
        # Extract specific fields
        structured_data = self.structure_text(cleaned_text)
        
        result = {
            'raw_text': extracted_text,
            'cleaned_text': cleaned_text,
            'structured_data': structured_data,
            'text_regions': len(text_regions),
            'confidence': self.calculate_confidence(extracted_text)
        }
        
        logger.info(f"Image processing completed. Found {len(text_regions)} text regions")
        
        return result
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespaces
        text = ' '.join(text.split())
        
        # Fix common OCR errors
        replacements = {
            '0': 'O',  # Sometimes O is read as 0 in medicine names
            '1': 'I',  # Sometimes I is read as 1
            '|': 'I',
            '§': 'S',
        }
        
        # Apply replacements only for medicine names (not dates or numbers)
        words = text.split()
        cleaned_words = []
        
        for word in words:
            # Check if word is likely a date or number
            if not re.match(r'^\d+[-/]\d+[-/]\d+$', word) and not word.isdigit():
                for old, new in replacements.items():
                    word = word.replace(old, new)
            cleaned_words.append(word)
        
        return ' '.join(cleaned_words)
    
    def structure_text(self, text: str) -> Dict[str, Optional[str]]:
        """
        Structure extracted text into meaningful fields
        
        Args:
            text: Cleaned text
            
        Returns:
            Dictionary with structured data
        """
        structured = {
            'medicine_names': self.extract_medicine_names(text),
            'dates': self.extract_dates(text),
            'dosages': self.extract_dosages(text),
            'batch_numbers': self.extract_batch_numbers(text),
            'manufacturer': self.extract_manufacturer(text)
        }
        
        return structured
    
    def extract_medicine_names(self, text: str) -> List[str]:
        """
        Extract potential medicine names from text
        
        Args:
            text: Input text
            
        Returns:
            List of potential medicine names
        """
        # Common medicine name patterns
        patterns = [
            r'\b[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*\b',  # Capitalized words
            r'\b[A-Z]{2,}(?:[a-z]+)*\b',  # All caps or mixed case
        ]
        
        # Common words to exclude from medicine names
        exclusions = {
            'tablet', 'tablets', 'capsule', 'capsules', 'syrup', 'suspension',
            'injection', 'cream', 'ointment', 'gel', 'drops', 'powder',
            'expiry', 'exp', 'mfg', 'manufactured', 'batch', 'lot', 'company',
            'pharma', 'pharmaceuticals', 'ltd', 'limited', 'pvt', 'private',
            'india', 'mumbai', 'delhi', 'bangalore', 'hyderabad', 'chennai',
            'use', 'before', 'date', 'keep', 'store', 'temperature', 'room',
            'this', 'that', 'with', 'from', 'under', 'above', 'below'
        }
        
        medicine_names = []
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Filter out exclusions and short words
                if (len(match) >= 3 and 
                    match.lower() not in exclusions and
                    not re.match(r'^\d+$', match) and  # Not just numbers
                    not re.match(r'^[IVX]+$', match)):  # Not roman numerals
                    medicine_names.append(match)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_names = []
        for name in medicine_names:
            name_lower = name.lower()
            if name_lower not in seen:
                seen.add(name_lower)
                unique_names.append(name)
        
        return unique_names[:5]  # Return top 5 candidates
    
    def extract_dates(self, text: str) -> Dict[str, List[str]]:
        """
        Extract dates from text
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with different types of dates
        """
        date_patterns = [
            # DD/MM/YYYY or DD-MM-YYYY
            r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})\b',
            # DD/MM/YY or DD-MM-YY
            r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2})\b',
            # MM/YYYY or MM-YYYY
            r'\b(\d{1,2}[-/]\d{4})\b',
            # Month YYYY or Month DD, YYYY
            r'\b([A-Za-z]{3,9}\s+\d{1,2},?\s*\d{4})\b',
            # DD Month YYYY
            r'\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b'
        ]
        
        all_dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            all_dates.extend(matches)
        
        # Categorize dates based on context
        expiry_dates = []
        manufacturing_dates = []
        other_dates = []
        
        for date in all_dates:
            # Look for context around the date
            date_index = text.lower().find(date.lower())
            if date_index != -1:
                # Check 20 characters before and after
                context = text[max(0, date_index-20):date_index+len(date)+20].lower()
                
                if any(word in context for word in ['exp', 'expiry', 'expires', 'use by', 'best before']):
                    expiry_dates.append(date)
                elif any(word in context for word in ['mfg', 'manufactured', 'mfd', 'production']):
                    manufacturing_dates.append(date)
                else:
                    other_dates.append(date)
        
        return {
            'expiry': list(set(expiry_dates)),
            'manufacturing': list(set(manufacturing_dates)),
            'other': list(set(other_dates))
        }
    
    def extract_dosages(self, text: str) -> List[str]:
        """
        Extract dosage information from text
        
        Args:
            text: Input text
            
        Returns:
            List of dosage strings
        """
        dosage_patterns = [
            r'\b\d+\s*mg\b',
            r'\b\d+\s*mcg\b',
            r'\b\d+\s*g\b',
            r'\b\d+\s*ml\b',
            r'\b\d+\s*IU\b',
            r'\b\d+\s*units?\b',
            r'\b\d+(?:\.\d+)?\s*mg/ml\b',
            r'\b\d+(?:\.\d+)?\s*%\b'
        ]
        
        dosages = []
        for pattern in dosage_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dosages.extend(matches)
        
        return list(set(dosages))
    
    def extract_batch_numbers(self, text: str) -> List[str]:
        """
        Extract batch numbers from text
        
        Args:
            text: Input text
            
        Returns:
            List of batch numbers
        """
        batch_patterns = [
            r'(?:batch|lot|b\.no|l\.no)[\s:]+([A-Z0-9\-]+)',
            r'\bbatch[\s:]+([A-Z0-9\-]+)\b',
            r'\blot[\s:]+([A-Z0-9\-]+)\b'
        ]
        
        batch_numbers = []
        for pattern in batch_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            batch_numbers.extend(matches)
        
        return list(set(batch_numbers))
    
    def extract_manufacturer(self, text: str) -> Optional[str]:
        """
        Extract manufacturer information from text
        
        Args:
            text: Input text
            
        Returns:
            Manufacturer name or None
        """
        manufacturer_patterns = [
            r'(?:manufactured by|mfg by|company)[\s:]+([A-Za-z0-9\s,.-]+?)(?:\n|$|,)',
            r'([A-Za-z0-9\s]+(?:pharma|pharmaceuticals|ltd|limited|pvt))',
            r'by\s+([A-Za-z0-9\s,.-]+?)\s*(?:ltd|limited|pvt|pharma)'
        ]
        
        for pattern in manufacturer_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                manufacturer = match.group(1).strip()
                # Clean up the manufacturer name
                manufacturer = re.sub(r'[,.-]+$', '', manufacturer)
                if len(manufacturer) > 3:
                    return manufacturer
        
        return None
    
    def calculate_confidence(self, text: str) -> float:
        """
        Calculate confidence score based on extracted text quality
        
        Args:
            text: Extracted text
            
        Returns:
            Confidence score between 0 and 1
        """
        if not text:
            return 0.0
        
        score = 0.0
        
        # Length factor (longer text generally means better extraction)
        if len(text) > 20:
            score += 0.3
        elif len(text) > 10:
            score += 0.2
        
        # Presence of expected keywords
        medical_keywords = ['tablet', 'capsule', 'mg', 'ml', 'exp', 'mfg', 'batch', 'lot']
        keyword_count = sum(1 for keyword in medical_keywords if keyword in text.lower())
        score += min(keyword_count * 0.1, 0.4)
        
        # Date patterns
        if re.search(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', text):
            score += 0.2
        
        # Number patterns (dosage, batch numbers)
        if re.search(r'\d+\s*(mg|ml|g|mcg)', text, re.IGNORECASE):
            score += 0.1
        
        return min(score, 1.0)