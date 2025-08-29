"""
Medicine Extractor Module for MediScan
Extracts structured medicine information from OCR text
"""

import re
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MedicineExtractor:
    """
    Extracts structured medicine information from OCR text
    """

    def __init__(self):
        """Initialize the medicine extractor"""
        # Common medicine forms
        self.medicine_forms = [
            'tablet', 'capsule', 'syrup', 'injection', 'cream', 'ointment',
            'drops', 'spray', 'inhaler', 'patch', 'powder', 'solution'
        ]

        # Common dosage units
        self.dosage_units = ['mg', 'ml', 'g', 'mcg', 'units', 'iu', '%']

    def extract_medicines(self, ocr_result: Dict[str, Any], scan_type: str = "Medicine Label") -> Dict[str, Any]:
        """
        Extract medicines from OCR results

        Args:
            ocr_result: OCR processing result
            scan_type: Type of scan (Medicine Label, Prescription, etc.)

        Returns:
            Dictionary with extracted medicine information
        """
        try:
            text = ocr_result.get('text', '')
            structured_data = ocr_result.get('structured_data', {})

            if scan_type.lower() == "medicine label":
                return self._extract_from_label(text, structured_data)
            elif "prescription" in scan_type.lower():
                return self._extract_from_prescription(text, structured_data)
            else:
                # Default to label extraction
                return self._extract_from_label(text, structured_data)

        except Exception as e:
            logger.error(f"Error extracting medicines: {e}")
            return {'medicines': [], 'patient_info': {}, 'error': str(e)}

    def _extract_from_label(self, text: str, structured_data: Dict = None) -> Dict[str, Any]:
        """
        Extract medicine information from a medicine label
        """
        if structured_data is None:
            structured_data = {}

        # Extract main medicine info
        medicine = {
            'name': self._extract_medicine_name(text, structured_data),
            'dosage': self._extract_dosage(text, structured_data),
            'form': self._extract_form(text),
            'manufacturer': self._extract_manufacturer(text, structured_data),
            'batch_no': self._extract_batch_number(text, structured_data),
            'mfg_date': self._extract_mfg_date(text, structured_data),
            'expiry_date': self._extract_expiry_date(text, structured_data),
            'quantity': self._extract_quantity(text, structured_data),
            'instructions': self._extract_instructions(text),
            'scan_type': 'label',
            'confidence': self._calculate_confidence(text, structured_data)
        }

        return {
            'medicines': [medicine] if medicine['name'] else [],
            'patient_info': {},
            'scan_info': {
                'type': 'Medicine Label',
                'processed_at': datetime.now().isoformat()
            }
        }

    def _extract_from_prescription(self, text: str, structured_data: Dict = None) -> Dict[str, Any]:
        """
        Extract medicine information from a prescription
        """
        if structured_data is None:
            structured_data = {}

        medicines = []
        patient_info = {}

        # Extract patient information
        patient_info = self._extract_patient_info(text)

        # Extract multiple medicines from prescription
        medicine_lines = self._identify_medicine_lines(text)

        for line in medicine_lines:
            medicine = {
                'name': self._extract_medicine_name_from_line(line),
                'dosage': self._extract_dosage_from_line(line),
                'frequency': self._extract_frequency(line),
                'duration': self._extract_duration(line),
                'instructions': self._extract_instructions_from_line(line),
                'scan_type': 'prescription'
            }

            if medicine['name']:
                medicines.append(medicine)

        return {
            'medicines': medicines,
            'patient_info': patient_info,
            'scan_info': {
                'type': 'Prescription',
                'processed_at': datetime.now().isoformat()
            }
        }

    def _extract_medicine_name(self, text: str, structured_data: Dict = None) -> Optional[str]:
        """Extract medicine name from text"""
        # First try structured data
        if structured_data and structured_data.get('medicine_name'):
            return self._clean_text(structured_data['medicine_name'])

        lines = text.split('\n')

        # Look for medicine name patterns
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if len(line) > 2 and len(line) < 50:  # Reasonable length
                # Skip common non-medicine words
                skip_words = ['tablet', 'capsule', 'syrup', 'mg', 'ml', 'manufactured', 'expires']
                if not any(word in line.lower() for word in skip_words):
                    # Medicine names often have capital letters
                    if re.search(r'[A-Z]', line):
                        return self._clean_text(line)

        return None

    def _extract_dosage(self, text: str, structured_data: Dict = None) -> Optional[str]:
        """Extract dosage information"""
        # First try structured data
        if structured_data and structured_data.get('dosage'):
            return self._clean_text(structured_data['dosage'])

        # Pattern matching for dosage
        patterns = [
            r'(\d+\.?\d*\s*(?:mg|ml|g|mcg|units?|iu|%))',
            r'(?:dosage?|strength)[:\s]+(\d+\.?\d*\s*(?:mg|ml|g|mcg|units?|iu|%))',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_form(self, text: str) -> Optional[str]:
        """Extract medicine form (tablet, capsule, etc.)"""
        text_lower = text.lower()

        for form in self.medicine_forms:
            if form in text_lower:
                return form.title()

        return None

    def _extract_manufacturer(self, text: str, structured_data: Dict = None) -> Optional[str]:
        """Extract manufacturer information"""
        # First try structured data
        if structured_data and structured_data.get('manufacturer'):
            return self._clean_text(structured_data['manufacturer'])

        patterns = [
            r'(?:mfr?|manufacturer?|made\s*by)[:\s]+([^\n]+)',
            r'(?:by|®)\s+([A-Z][^\n]+(?:ltd|inc|corp|pharma|lab))',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._clean_text(match.group(1))

        return None

    def _extract_batch_number(self, text: str, structured_data: Dict = None) -> Optional[str]:
        """Extract batch number"""
        # First try structured data
        if structured_data and structured_data.get('batch_number'):
            return self._clean_text(structured_data['batch_number'])

        patterns = [
            r'(?:batch|lot)\s*(?:no|number)?[:\s]*([A-Za-z0-9\-]+)',
            r'(?:b\.?no|l\.?no)[:\s]*([A-Za-z0-9\-]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_expiry_date(self, text: str, structured_data: Dict = None) -> Optional[str]:
        """Extract expiry date"""
        # First try structured data
        if structured_data and structured_data.get('expiry_date'):
            return self._normalize_date(structured_data['expiry_date'])

        patterns = [
            r'(?:exp|expiry|expires?)[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
            r'(?:exp|expiry|expires?)[:\s]*([a-z]{3,9}\s*[0-9]{2,4})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._normalize_date(match.group(1).strip())

        return None

    def _extract_mfg_date(self, text: str, structured_data: Dict = None) -> Optional[str]:
        """Extract manufacturing date"""
        # First try structured data
        if structured_data and structured_data.get('mfg_date'):
            return self._normalize_date(structured_data['mfg_date'])

        patterns = [
            r'(?:mfg|manufactured?|mfd)[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
            r'(?:mfg|manufactured?|mfd)[:\s]*([a-z]{3,9}\s*[0-9]{2,4})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._normalize_date(match.group(1).strip())

        return None

    def _extract_quantity(self, text: str, structured_data: Dict = None) -> Optional[str]:
        """Extract quantity information"""
        # First try structured data
        if structured_data and structured_data.get('quantity'):
            return self._clean_text(structured_data['quantity'])

        patterns = [
            r'(?:qty|quantity|count)[:\s]*(\d+)',
            r'(\d+)\s*(?:tablets?|capsules?|pills?)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_instructions(self, text: str) -> Optional[str]:
        """Extract usage instructions"""
        instruction_patterns = [
            r'(?:take|use|apply)[^\n]*',
            r'(?:dosage|directions?)[:\s]+([^\n]+)',
            r'(?:once|twice|thrice)\s+(?:daily|a day)[^\n]*',
        ]

        for pattern in instruction_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._clean_text(match.group(0))

        return None

    def _extract_patient_info(self, text: str) -> Dict[str, str]:
        """Extract patient information from prescription"""
        patient_info = {}

        # Patient name
        name_pattern = r'(?:patient|name)[:\s]+([^\n]+)'
        name_match = re.search(name_pattern, text, re.IGNORECASE)
        if name_match:
            patient_info['name'] = self._clean_text(name_match.group(1))

        # Age
        age_pattern = r'(?:age)[:\s]+(\d+)'
        age_match = re.search(age_pattern, text, re.IGNORECASE)
        if age_match:
            patient_info['age'] = age_match.group(1)

        # Doctor name
        doctor_pattern = r'(?:dr|doctor)[:\s\.]+([^\n]+)'
        doctor_match = re.search(doctor_pattern, text, re.IGNORECASE)
        if doctor_match:
            patient_info['doctor'] = self._clean_text(doctor_match.group(1))

        return patient_info

    def _identify_medicine_lines(self, text: str) -> List[str]:
        """Identify lines that contain medicine information"""
        lines = text.split('\n')
        medicine_lines = []

        for line in lines:
            line = line.strip()
            if len(line) > 5:  # Minimum length
                # Check if line contains medicine indicators
                if any(unit in line.lower() for unit in self.dosage_units):
                    medicine_lines.append(line)
                elif re.search(r'\d+.*(?:times?|daily|twice|once)', line, re.IGNORECASE):
                    medicine_lines.append(line)

        return medicine_lines

    def _extract_medicine_name_from_line(self, line: str) -> Optional[str]:
        """Extract medicine name from a single line"""
        # Remove common prescription elements
        cleaned = re.sub(r'\b(?:take|tablet?s?|capsule?s?|mg|ml|once|twice|daily|\d+)\b', '', line, flags=re.IGNORECASE)
        cleaned = cleaned.strip()

        # Get the first substantial word(s)
        words = cleaned.split()
        if words:
            return words[0].title()

        return None

    def _extract_dosage_from_line(self, line: str) -> Optional[str]:
        """Extract dosage from a prescription line"""
        dosage_pattern = r'(\d+\.?\d*\s*(?:mg|ml|g|mcg|units?|iu|%))'
        match = re.search(dosage_pattern, line, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _extract_frequency(self, line: str) -> Optional[str]:
        """Extract frequency from prescription line"""
        frequency_patterns = [
            r'(once|twice|thrice)\s*(?:daily|a day|per day)',
            r'(\d+)\s*times?\s*(?:daily|a day|per day)',
            r'every\s*(\d+)\s*hours?',
        ]

        for pattern in frequency_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return None

    def _extract_duration(self, line: str) -> Optional[str]:
        """Extract duration from prescription line"""
        duration_patterns = [
            r'for\s*(\d+)\s*(?:days?|weeks?|months?)',
            r'(\d+)\s*(?:days?|weeks?|months?)\s*course',
        ]

        for pattern in duration_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return None

    def _extract_instructions_from_line(self, line: str) -> Optional[str]:
        """Extract instructions from prescription line"""
        instruction_keywords = ['after', 'before', 'with', 'food', 'meal', 'empty stomach']

        for keyword in instruction_keywords:
            if keyword in line.lower():
                # Extract the part containing the instruction
                parts = line.lower().split(keyword)
                if len(parts) > 1:
                    return f"{keyword} {parts[1].strip()}"

        return None

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""

        # Remove extra whitespace
        cleaned = ' '.join(text.split())

        # Remove special characters at start/end
        cleaned = cleaned.strip('.,;:-_()[]{}')

        return cleaned

    def _normalize_date(self, date_str: str) -> str:
        """Normalize date format to YYYY-MM-DD"""
        if not date_str:
            return ""

        try:
            # Try different date formats
            formats = ['%m/%Y', '%m-%Y', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d']

            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue

            # If no format matches, return as is
            return date_str

        except Exception:
            return date_str

    def _calculate_confidence(self, text: str, structured_data: Dict) -> float:
        """Calculate confidence score for extraction"""
        score = 0.0

        # Check if we found key fields
        if structured_data.get('medicine_name'):
            score += 0.3
        if structured_data.get('dosage'):
            score += 0.2
        if structured_data.get('expiry_date'):
            score += 0.2
        if structured_data.get('batch_number'):
            score += 0.1
        if structured_data.get('manufacturer'):
            score += 0.1

        # Check text quality
        if len(text) > 20:
            score += 0.1

        return min(1.0, score)
