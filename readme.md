# MediScan: Voice-Assisted Prescription and Medicine Label Scanner for Reminders and Expiry Alerts (MS-VA)

## Overview

**MediScan MS-VA** is a comprehensive medicine management solution built with Streamlit and Python. It leverages advanced OCR, natural language processing, and voice technologies to help users scan medicine labels and prescriptions, extract structured information, set reminders, track expiry, and receive voice notifications. The app is designed for ease of use, reliability, and extensibility.

---

## Requirements

```txt
streamlit>=1.28.0
opencv-python-headless>=4.8.0
numpy>=1.24.0
pillow>=10.0.0
pytesseract>=0.3.10
easyocr>=1.7.0
pyttsx3>=2.90
gtts>=2.3.2
pygame>=2.5.0
pandas>=2.0.0
plotly>=5.15.0
```

---

## Installation

1. **Install Tesseract OCR:**
   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
   - Linux: `sudo apt install tesseract-ocr`
   - macOS: `brew install tesseract`

2. **Clone and setup:**
```bash
git clone <your-repo-url>
cd mediscan-ms-va
pip install -r requirements.txt
```

---

# Complete Project Structure and Required Datasets for MediScan MS-VA

Below is a detailed structure for your project, including all main code files, folders, and recommended datasets for development, testing, and demonstration.

---

## Project Directory Structure

```
mediscan-ms-va/
├── App.py                      # Main Streamlit application frontend
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── backend/                    # Core backend modules
│   ├── __init__.py             # Backend package initialization
│   ├── ocr_processor.py        # OCR processing (EasyOCR/Tesseract)
│   ├── medicine_extractor.py   # Extracts medicine info from OCR text
│   ├── reminder_system.py      # Medicine reminders & notifications
│   ├── voice_assistant.py      # Text-to-speech and voice feedback
│   └── database_handler.py     # Data persistence (JSON-based)
├── data/                       # Application data (auto-created)
│   ├── medicines.json          # Medicine inventory (auto-generated)
│   ├── reminders.json          # Reminder settings (auto-generated)
│   └── settings.json           # App/user settings (auto-generated)
├── dataset/                    # Required datasets for testing/demo
│   ├── labels/                 # Sample medicine label images (JPEG/PNG)
│   ├── prescriptions/          # Sample prescription images (JPEG/PNG)
│   └── medicines.csv           # Structured medicine info (CSV, optional)
└── .gitignore                  # (Optional) Ignore data/dataset files in git
```

---

## Required Datasets

### 1. `dataset/labels/`
- **Purpose:** Store sample images of medicine labels for OCR and extraction testing.
- **Content:** JPEG/PNG images of medicine strips, bottles, boxes, etc.
- **Example Files:**
  - `paracetamol_strip.jpg`
  - `amoxicillin_bottle.png`
  - `ibuprofen_box.jpeg`

### 2. `dataset/prescriptions/`
- **Purpose:** Store sample images of prescriptions for multi-medicine and instruction extraction.
- **Content:** JPEG/PNG scans or photos of handwritten or printed prescriptions.
- **Example Files:**
  - `prescription_01.jpg`
  - `prescription_dr_singh.png`
  - `prescription_child_fever.jpeg`

### 3. `dataset/medicines.csv` (optional but recommended)
- **Purpose:** Provide a structured reference database for medicine validation and extraction accuracy.
- **Content:** CSV file with columns such as:
  - `medicine_name`
  - `generic_name`
  - `category`
  - `manufacturer`
  - `expiry_date`
  - `batch_number`
  - `dosage_form`
  - `strength`
- **Example Row:**
  ```
  Paracetamol,Acetaminophen,Analgesic,ABC Pharma,2025-12-31,B12345,Tablet,500mg
  ```

---

## Notes on Dataset Usage

- **OCR Testing:** Use images in `labels/` and `prescriptions/` for validating OCR extraction and medicine info parsing.
- **Extraction Validation:** Use `medicines.csv` to cross-check extracted names, dosages, expiry dates, and other fields.
- **Demo & Documentation:** Reference these datasets in your documentation and demo scripts to show real-world usage.
- **Unit Testing:** Write automated tests using these sample files to ensure extraction and reminder logic works as expected.

---

## Example Dataset Sources

- [RxImage API](https://rximage.nlm.nih.gov/) – Medicine label images
- [OpenFDA Drug Label Dataset](https://open.fda.gov/data/drug/label/) – Structured drug info
- [Kaggle Medical Prescription Datasets](https://www.kaggle.com/datasets) – Prescription images

---

## Best Practices

- **Anonymize sensitive data** in prescription images.
- **Use diverse samples** (different brands, forms, handwriting styles).
- **Document your dataset** (add a `README.md` in the `dataset/` folder describing sources and usage).

---

This structure ensures your project is organized, testable, and ready for real-world
---

## Features

### 🔍 OCR & Text Extraction
- **Dual Engine Support**: EasyOCR (default) and Tesseract OCR
- **Medicine Label Scanning**: Extract name, expiry date, batch number, dosage, manufacturer
- **Prescription Scanning**: Extract multiple medicines, doctor info, patient details
- **Image Preprocessing**: Noise reduction, contrast enhancement, text region detection, resizing for better accuracy
- **Multi-language Support**: English and Hindi text recognition

### 💊 Medicine Management
- **Smart Extraction**: Medicine names, dosages, forms (tablet/capsule/syrup/injection/cream/drops)
- **Expiry Tracking**: Automatic calculation of days until expiry, expiry alerts, and dashboard
- **Batch & Manufacturing Info**: Extract and store batch numbers, manufacturing dates, and use-by dates
- **Medicine Validation**: Built-in database for common medicines, generic names, and categories
- **Search & Filter**: Find medicines by name, expiry status, manufacturer, form, and batch number
- **Inventory Management**: Add, edit, delete medicines; backup and restore data

### ⏰ Reminder System
- **Flexible Scheduling**: Daily, twice daily, three times daily, weekly, custom times
- **Smart Notifications**: Expiry alerts, take medicine reminders, voice announcements
- **Compliance Tracking**: Track taken vs missed doses, history, and analytics
- **History & Analytics**: Detailed compliance reports, missed/taken counts, and trends
- **Pause/Resume/Delete Reminders**: Manage reminders for each medicine

### 🔊 Voice Assistant
- **Dual TTS Engines**: pyttsx3 (offline) and Google TTS (online)
- **Multi-language**: Support for English, Hindi, Spanish, French, German
- **Smart Announcements**: Scan results, reminders, expiry alerts, compliance feedback
- **Voice Feedback**: Confirmation of actions, medication instructions, expiry warnings
- **Customizable Speech Rate and Volume**: Adjust voice properties for accessibility

### 📊 Analytics & Insights
- **Expiry Dashboard**: Visual charts showing medicine status, expiring soon, expired
- **Compliance Metrics**: Track medication adherence over time, missed/taken doses
- **Timeline View**: See upcoming expirations and reminders
- **Statistics**: Total medicines, expired count, active reminders, by form/manufacturer

### 🗄️ Data Management
- **JSON-based Storage**: Simple file storage for easy backup/restore
- **Automatic Backup**: Optional daily backups of all data
- **Data Validation**: Ensure data integrity and handle corruption
- **Migration Support**: Easy upgrade path for future schema changes
- **User Data & Settings**: Store user preferences, voice settings, and reminder configurations

---

## Usage

1. **Start the application:**
```bash
streamlit run App.py
```

2. **Scan a Medicine or Prescription:**
   - Go to "📷 Scan Medicine" tab
   - Choose "Medicine Label" or "Prescription"
   - Upload image or take photo
   - Click "🔍 Process Image"
   - Review extracted information
   - Set reminders if needed

3. **Manage Medicines:**
   - View all scanned medicines in "💊 My Medicines"
   - Search and filter by various criteria
   - Get voice feedback on medicine details
   - Delete or edit medicine entries

4. **Setup Reminders:**
   - Configure reminder schedules for each medicine
   - Set daily reminder times
   - Track compliance in "⏰ Reminders" tab
   - Get voice notifications for due medicines

5. **Monitor Analytics:**
   - View expiry status charts in "📊 Analytics"
   - Track medication compliance over time
   - See upcoming expirations and alerts

---

## Configuration

### Voice Assistant Settings
- Enable/disable voice feedback
- Choose language (English, Hindi, etc.)
- Select TTS engine (pyttsx3 vs gTTS)
- Adjust speech rate and volume

### Reminder Settings  
- Set default reminder time
- Configure days before expiry to alert
- Choose notification preferences
- Pause, resume, or delete reminders

### OCR Settings
- Select OCR engine (EasyOCR recommended)
- Configure image preprocessing options
- Set confidence thresholds

### Data & Backup
- Automatic backup of medicines and reminders
- Restore from backup file
- Clean up old data by age

---

## Technical Details

### OCR Processing Pipeline
1. **Image Preprocessing**: Noise reduction, contrast enhancement, resizing
2. **Text Detection**: EasyOCR or Tesseract text region detection
3. **Text Extraction**: Multi-language OCR with confidence scoring
4. **Post-processing**: Text cleaning, error correction, field extraction

### Medicine Information Extraction
- **Regex Patterns**: Sophisticated patterns for dates, dosages, batch numbers
- **Context Analysis**: Smart field classification using surrounding text
- **Date Normalization**: Handle multiple date formats (DD/MM/YYYY, MM/YY, etc.)
- **Medicine Name Detection**: Filter out common words, validate against database
- **Manufacturer & Batch Extraction**: Identify and extract manufacturer and batch info

### Reminder System
- **Scheduling Algorithms**: Calculate next reminder time based on type (daily, weekly, etc.)
- **History Tracking**: Store taken/missed events for compliance analytics
- **Expiry Alerts**: Notify user before expiry based on settings

### Voice Assistant
- **pyttsx3**: Offline, customizable, supports multiple voices
- **gTTS**: Online, high-quality, supports many languages
- **Voice Feedback**: Announce reminders, expiry, scan results, and compliance

### Data Storage
- **JSON-based**: Simple file storage for easy backup/restore
- **Automatic Backup**: Optional daily backups of all data
- **Data Validation**: Ensure data integrity and handle corruption
- **Migration Support**: Easy upgrade path for future schema changes

---

## Troubleshooting

### Common Issues

1. **Tesseract not found:**
   ```bash
   # Linux/Mac
   which tesseract
   
   # Windows - update path in ocr_processor.py
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

2. **Poor OCR results:**
   - Ensure good image quality (high resolution, good lighting)
   - Try different OCR engines (EasyOCR vs Tesseract)
   - Check image preprocessing settings

3. **Voice not working:**
   - Install system TTS dependencies
   - For pyttsx3: Install espeak (Linux) or use built-in TTS
   - For gTTS: Ensure internet connection

4. **Missing dependencies:**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

---

## GitHub References

Similar projects for inspiration and comparison:

- **[VedantKale106/MediScan](https://github.com/VedantKale106/MediScan)**: Medicine scanner with OCR
- **[aayushdubey-codes/MediScanner](https://github.com/aayushdubey-codes/MediScanner)**: OCR-based medicine label reader
- **[sriphaniN/Prescription-Label-Reading](https://github.com/sriphaniN/Prescription-Label-Reading)**: Prescription to speech conversion
- **[Franky1/Streamlit-Tesseract](https://github.com/Franky1/Streamlit-Tesseract)**: Streamlit OCR example
- **[ameera3/OCR_Expiration_Date](https://github.com/ameera3/OCR_Expiration_Date)**: Expiry date extraction
- **[Naveen-S6/Data_Extraction_Healthcare_Project](https://github.com/Naveen-S6/Data_Extraction_Healthcare_Project)**: Medical data extraction
- **[LeadingIndiaAI/Extraction-of-Information-from-Medicines](https://github.com/LeadingIndiaAI/Extraction-of-Information-from-Medicines)**: Medicine info extraction

---

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Submit pull request with clear description

---

## License

MIT License - see LICENSE file for details

---

## Disclaimer

⚠️ **Important**: This application is for informational purposes only. Always consult healthcare professionals for medical advice. The OCR results may contain errors and should be verified manually.

---