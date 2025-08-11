"""
Medicine Extractor Module for MediScan
Extracts and processes medicine information from OCR text
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class MedicineExtractor:
    """
    Extracts structured medicine information from OCR text
    """
    
    def __init__(self):
        """Initialize the medicine extractor"""
        self.medicine_database = self._load_medicine_database()
        
    def _load_medicine_database(self) -> Dict[str, Dict]:
        """
        Load a simple medicine database for validation
        This can be expanded to load from external sources
        """
        return {
            # Common medicines with their generic names
            'paracetamol': {'generic': 'Acetaminophen', 'category': 'Analgesic'},
            'aspirin': {'generic': 'Acetylsalicylic acid', 'category': 'NSAID'},
            'ibuprofen': {'generic': 'Ibuprofen', 'category': 'NSAID'},
            'amoxicillin': {'generic': 'Amoxicillin', 'category': 'Antibiotic'},
            'ciprofloxacin': {'generic': 'Ciprofloxacin', 'category': 'Antibiotic'},
            'metformin': {'generic': 'Metformin', 'category': 'Antidiabetic'},
            'omeprazole': {'generic': 'Omeprazole', 'category': 'PPI'},
            'losartan': {'generic': 'Losartan', 'category': 'ARB'},
            'atorvastatin': {'generic': 'Atorvastatin', 'category': 'Statin'},
        }
    
    def extract_from_label(self, ocr_result: Dict) -> Dict:
        """
        Extract medicine information from label OCR result
        
        Args:
            ocr_result: Dictionary containing OCR processing results
            
        Returns:
            Dictionary with structured medicine information
        """
        text = ocr_result.get('cleaned_text', '')
        structured_data = ocr_result.get('structured_data', {})
        
        # Extract basic information
        medicine_info = {
            'name': self._extract_medicine_name(structured_data.get('medicine_names', []), text),
            'manufacturer': structured_data.get('manufacturer'),
            'batch_no': self._get_first_or_none(structured_data.get('batch_numbers', [])),
            'dosage': self._extract_primary_dosage(structured_data.get('dosages', [])),
            'quantity': self._extract_quantity(text),
            'form': self._extract_medicine_form(text),
            'mfg_date': self._extract_manufacturing_date(structured_data.get('dates', {})),
            'expiry_date': self._extract_expiry_date(structured_data.get('dates', {})),
            'use_by_date': self._extract_use_by_date(structured_data.get('dates', {})),
            'storage_instructions': self._extract_storage_instructions(text),
            'warnings': self._extract_warnings(text),
            'scan_type': 'label',
            'scan_timestamp': datetime.now().isoformat(),
            'confidence': ocr_result.get('confidence', 0.0)
        }
        
        # Calculate days until expiry
        if medicine_info['expiry_date']:
            medicine_info['days_until_expiry'] = self._calculate_days_until_expiry(
                medicine_info['expiry_date']
            )
        elif medicine_info['use_by_date']:
            medicine_info['days_until_expiry'] = self._calculate_days_until_expiry(
                medicine_info['use_by_date']
            )
        
        # Validate against database
        medicine_info['validated'] = self._validate_medicine(medicine_info['name'])
        
        return medicine_info
    
    def extract_from_prescription(self, ocr_result: Dict) -> Dict:
        """
        Extract medicine information from prescription OCR result
        
        Args:
            ocr_result: Dictionary containing OCR processing results
            
        Returns:
            Dictionary with structured prescription information
        """
        text = ocr_result.get('cleaned_text', '')
        structured_data = ocr_result.get('structured_data', {})
        
        # Extract prescription-specific information
        prescription_info = {
            'medicines': self._extract_multiple_medicines(text),
            'doctor_name': self._extract_doctor_name(text),
            'patient_name': self._extract_patient_name(text),
            'prescription_date': self._extract_prescription_date(structured_data.get('dates', {})),
            'clinic_hospital': self._extract_clinic_info(text),
            'instructions': self._extract_dosage_instructions(text),
            'scan_type': 'prescription',
            'scan_timestamp': datetime.now().isoformat(),
            'confidence': ocr_result.get('confidence', 0.0)
        }
        
        return prescription_info
    
    def _extract_medicine_name(self, candidate_names: List[str], text: str) -> Optional[str]:
        """Extract the most likely medicine name"""
        if not candidate_names:
            return None
            
        # Score each candidate based on various factors
        scored_candidates = []
        
        for name in candidate_names:
            score = 0
            name_lower = name.lower()
            
            # Check if it's in our database
            if name_lower in self.medicine_database:
                score += 10
                
            # Check if it appears near dosage information
            if re.search(rf'{re.escape(name)}.*?\d+\s*mg', text, re.IGNORECASE):
                score += 5
                
            # Prefer longer, more specific names
            score += len(name) * 0.1
            
            # Check for common medicine suffixes
            if any(suffix in name_lower for suffix in ['tab', 'cap', 'syrup', 'inj']):
                score += 2
                
            scored_candidates.append((name, score))
        
        # Return the highest scoring candidate
        if scored_candidates:
            return max(scored_candidates, key=lambda x: x[1])[0]
            
        return None
    
    def _extract_primary_dosage(self, dosages: List[str]) -> Optional[str]:
        """Extract the primary dosage from list"""
        if not dosages:
            return None
            
        # Prefer mg dosages, then others
        mg_dosages = [d for d in dosages if 'mg' in d.lower()]
        if mg_dosages:
            return mg_dosages[0]
            
        return dosages[0] if dosages else None
    
    def _extract_quantity(self, text: str) -> Optional[str]:
        """Extract quantity information"""
        quantity_patterns = [
            r'(\d+)\s*tablets?',
            r'(\d+)\s*capsules?',
            r'(\d+)\s*ml\s*bottle',
            r'(\d+)\s*strips?',
            r'pack\s*of\s*(\d+)',
            r'(\d+)\s*pieces?'
        ]
        
        for pattern in quantity_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"{match.group(1)} units"
                
        return None
    
    def _extract_medicine_form(self, text: str) -> Optional[str]:
        """Extract medicine form (tablet, capsule, etc.)"""
        forms = {
            'tablet': ['tablet', 'tab'],
            'capsule': ['capsule', 'cap'],
            'syrup': ['syrup', 'liquid'],
            'injection': ['injection', 'inj'],
            'cream': ['cream', 'ointment'],
            'drops': ['drops', 'eye drops']
        }
        
        text_lower = text.lower()
        for form, keywords in forms.items():
            if any(keyword in text_lower for keyword in keywords):
                return form
                
        return None
    
    def _extract_manufacturing_date(self, dates: Dict) -> Optional[str]:
        """Extract manufacturing date"""
        mfg_dates = dates.get('manufacturing', [])
        return self._normalize_date(mfg_dates[0]) if mfg_dates else None
    
    def _extract_expiry_date(self, dates: Dict) -> Optional[str]:
        """Extract expiry date"""
        exp_dates = dates.get('expiry', [])
        return self._normalize_date(exp_dates[0]) if exp_dates else None
    
    def _extract_use_by_date(self, dates: Dict) -> Optional[str]:
        """Extract use by date"""
        # For now, treat as same as expiry date
        return self._extract_expiry_date(dates)
    
    def _extract_storage_instructions(self, text: str) -> Optional[str]:
        """Extract storage instructions"""
        storage_patterns = [
            r'store.*?(?:\.|$)',
            r'keep.*?(?:\.|$)',
            r'storage.*?(?:\.|$)',
            r'temperature.*?(?:\.|$)'
        ]
        
        for pattern in storage_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group().strip()
                
        return None
    
    def _extract_warnings(self, text: str) -> List[str]:
        """Extract warnings and precautions"""
        warning_patterns = [
            r'warning.*?(?:\.|$)',
            r'caution.*?(?:\.|$)',
            r'do not.*?(?:\.|$)',
            r'avoid.*?(?:\.|$)'
        ]
        
        warnings = []
        for pattern in warning_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            warnings.extend([match.strip() for match in matches])
            
        return warnings[:3]  # Return top 3 warnings
    
    def _extract_multiple_medicines(self, text: str) -> List[Dict]:
        """Extract multiple medicines from prescription text"""
        # This is a simplified implementation
        # In practice, this would be more sophisticated
        medicines = []
        
        # Look for numbered medicine entries
        medicine_patterns = [
            r'(\d+\.)\s*([A-Za-z][A-Za-z0-9\s]*)\s*(\d+\s*mg)',
            r'Tab\.\s*([A-Za-z][A-Za-z0-9\s]*)\s*(\d+\s*mg)',
            r'Cap\.\s*([A-Za-z][A-Za-z0-9\s]*)\s*(\d+\s*mg)'
        ]
        
        for pattern in medicine_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                medicine = {
                    'name': match[1] if len(match) > 1 else match[0],
                    'dosage': match[2] if len(match) > 2 else None,
                    'instructions': self._extract_single_medicine_instructions(text, match[1] if len(match) > 1 else match[0])
                }
                medicines.append(medicine)
        
        return medicines
    
    def _extract_doctor_name(self, text: str) -> Optional[str]:
        """Extract doctor name from prescription"""
        doctor_patterns = [
            r'dr\.?\s*([A-Za-z\s]+)',
            r'doctor\s*([A-Za-z\s]+)',
            r'physician\s*([A-Za-z\s]+)'
        ]
        
        for pattern in doctor_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
                
        return None
    
    def _extract_patient_name(self, text: str) -> Optional[str]:
        """Extract patient name from prescription"""
        patient_patterns = [
            r'patient\s*:?\s*([A-Za-z\s]+)',
            r'name\s*:?\s*([A-Za-z\s]+)',
            r'mr\.?\s*([A-Za-z\s]+)',
            r'mrs\.?\s*([A-Za-z\s]+)'
        ]
        
        for pattern in patient_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
                
        return None
    
    def _extract_prescription_date(self, dates: Dict) -> Optional[str]:
        """Extract prescription date"""
        all_dates = []
        all_dates.extend(dates.get('other', []))
        all_dates.extend(dates.get('expiry', []))
        
        # Return the first valid date as prescription date
        return self._normalize_date(all_dates[0]) if all_dates else None
    
    def _extract_clinic_info(self, text: str) -> Optional[str]:
        """Extract clinic or hospital information"""
        clinic_patterns = [
            r'(clinic.*?)(?:\n|$)',
            r'(hospital.*?)(?:\n|$)',
            r'(medical center.*?)(?:\n|$)'
        ]
        
        for pattern in clinic_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
                
        return None
    
    def _extract_dosage_instructions(self, text: str) -> List[str]:
        """Extract dosage instructions from prescription"""
        instruction_patterns = [
            r'(\d+\s*times?\s*(?:a\s*)?day)',
            r'(twice\s*(?:a\s*)?day)',
            r'(once\s*(?:a\s*)?day)',
            r'(before\s*meals?)',
            r'(after\s*meals?)',
            r'(with\s*meals?)',
            r'(at\s*bedtime)',
            r'(as\s*needed)'
        ]
        
        instructions = []
        for pattern in instruction_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            instructions.extend(matches)
            
        return list(set(instructions))  # Remove duplicates
    
    def _extract_single_medicine_instructions(self, text: str, medicine_name: str) -> Optional[str]:
        """Extract instructions for a specific medicine"""
        # Look for instructions near the medicine name
        medicine_index = text.lower().find(medicine_name.lower())
        if medicine_index == -1:
            return None
            
        # Get text around the medicine name
        context = text[medicine_index:medicine_index + 200]
        
        instruction_patterns = [
            r'(\d+\s*x\s*\d+)',
            r'(\d+\s*times?\s*(?:a\s*)?day)',
            r'(twice\s*daily)',
            r'(once\s*daily)'
        ]
        
        for pattern in instruction_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1)
                
        return None
    
    def _normalize_date(self, date_str: str) -> Optional[str]:
        """Normalize date string to YYYY-MM-DD format"""
        if not date_str:
            return None
            
        # Common date formats to try
        date_formats = [
            '%d/%m/%Y', '%d-%m-%Y',
            '%d/%m/%y', '%d-%m-%y',
            '%m/%d/%Y', '%m-%d-%Y',
            '%Y-%m-%d', '%Y/%m/%d',
            '%d %b %Y', '%d %B %Y',
            '%b %d %Y', '%B %d %Y'
        ]
        
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str.strip(), fmt)
                # Handle 2-digit years
                if date_obj.year < 1950:
                    date_obj = date_obj.replace(year=date_obj.year + 100)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
                
        # Try to extract date components using regex
        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', date_str)
        if date_match:
            day, month, year = date_match.groups()
            year = int(year)
            if year < 50:
                year += 2000
            elif year < 100:
                year += 1900
                
            try:
                date_obj = datetime(year, int(month), int(day))
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                # Try swapping day and month
                try:
                    date_obj = datetime(year, int(day), int(month))
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    pass
                    
        return None
    
    def _calculate_days_until_expiry(self, expiry_date: str) -> Optional[int]:
        """Calculate days until expiry"""
        if not expiry_date:
            return None
            
        try:
            expiry_obj = datetime.strptime(expiry_date, '%Y-%m-%d')
            today = datetime.now()
            delta = expiry_obj - today
            return delta.days
        except ValueError:
            return None
    
    def _validate_medicine(self, medicine_name: str) -> bool:
        """Validate medicine name against database"""
        if not medicine_name:
            return False
            
        return medicine_name.lower() in self.medicine_database
    
    def _get_first_or_none(self, items: List) -> Optional[any]:
        """Get first item from list or None if empty"""
        return items[0] if items else None