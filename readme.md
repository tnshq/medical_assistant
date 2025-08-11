# MediScan: Voice-Assisted Prescription and Medicine Label Scanner for Reminders and Expiry Alerts (MS-VA)

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

## Project Structure

```
mediscan-ms-va/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── backend/
│   ├── __init__.py                # Backend module initialization
│   ├── ocr_processor.py           # OCR processing (EasyOCR/Tesseract)
│   ├── medicine_extractor.py      # Extract medicine info from OCR
│   ├── reminder_system.py         # Medicine reminders & notifications
│   ├── voice_assistant.py         # Text-to-speech functionality
│   └── database_handler.py        # Data persistence (JSON-based)
└── data/                          # Application data (auto-created)
    ├── medicines.json             # Medicine inventory
    ├── reminders.json             # Reminder settings
    └── settings.json              # App settings
```

## Features

### 🔍 OCR & Text Extraction
- **Dual Engine Support**: EasyOCR (default) and Tesseract OCR
- **Medicine Label Scanning**: Extract name, expiry date, batch number, dosage, manufacturer
- **Prescription Scanning**: Extract multiple medicines, doctor info, patient details
- **Image Preprocessing**: Noise reduction, contrast enhancement, text region detection
- **Multi-language Support**: English and Hindi text recognition

### 💊 Medicine Management
- **Smart Extraction**: Medicine names, dosages, forms (tablet/capsule/syrup)
- **Expiry Tracking**: Automatic calculation of days until expiry
- **Batch & Manufacturing Info**: Extract and store batch numbers, mfg dates
- **Medicine Validation**: Built-in database for common medicines
- **Search & Filter**: Find medicines by name, expiry status, manufacturer

### ⏰ Reminder System
- **Flexible Scheduling**: Daily, twice daily, three times daily, weekly, custom
- **Smart Notifications**: Expiry alerts, take medicine reminders
- **Compliance Tracking**: Track taken vs missed doses
- **History & Analytics**: Detailed compliance reports and trends

### 🔊 Voice Assistant
- **Dual TTS Engines**: pyttsx3 (offline) and Google TTS (online)
- **Multi-language**: Support for English, Hindi, Spanish, French, German
- **Smart Announcements**: Scan results, reminders, expiry alerts
- **Voice Feedback**: Confirmation of actions, medication instructions

### 📊 Analytics & Insights
- **Expiry Dashboard**: Visual charts showing medicine status
- **Compliance Metrics**: Track medication adherence over time
- **Timeline View**: See upcoming expirations and reminders
- **Statistics**: Total medicines, expired count, active reminders

## Usage

1. **Start the application:**
```bash
streamlit run app.py
```

2. **Scan a Medicine:**
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

## Configuration

### Voice Assistant Settings
- Enable/disable voice feedback
- Choose language (English, Hindi, etc.)
- Select TTS engine (pyttsx3 vs gTTS)

### Reminder Settings  
- Set default reminder time
- Configure days before expiry to alert
- Choose notification preferences

### OCR Settings
- Select OCR engine (EasyOCR recommended)
- Configure image preprocessing options
- Set confidence thresholds

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

### Data Storage
- **JSON-based**: Simple file storage for easy backup/restore
- **Automatic Backup**: Optional daily backups of all data
- **Data Validation**: Ensure data integrity and handle corruption
- **Migration Support**: Easy upgrade path for future schema changes

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

## GitHub References

Similar projects for inspiration and comparison:

- **[VedantKale106/MediScan](https://github.com/VedantKale106/MediScan)**: Medicine scanner with OCR
- **[aayushdubey-codes/MediScanner](https://github.com/aayushdubey-codes/MediScanner)**: OCR-based medicine label reader
- **[sriphaniN/Prescription-Label-Reading](https://github.com/sriphaniN/Prescription-Label-Reading)**: Prescription to speech conversion
- **[Franky1/Streamlit-Tesseract](https://github.com/Franky1/Streamlit-Tesseract)**: Streamlit OCR example
- **[ameera3/OCR_Expiration_Date](https://github.com/ameera3/OCR_Expiration_Date)**: Expiry date extraction
- **[Naveen-S6/Data_Extraction_Healthcare_Project](https://github.com/Naveen-S6/Data_Extraction_Healthcare_Project)**: Medical data extraction
- **[LeadingIndiaAI/Extraction-of-Information-from-Medicines](https://github.com/LeadingIndiaAI/Extraction-of-Information-from-Medicines)**: Medicine info extraction

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Submit pull request with clear description

## License

MIT License - see LICENSE file for details

## Disclaimer

⚠️ **Important**: This application is for informational purposes only. Always consult healthcare professionals for medical advice. The OCR results may contain errors and should be verified manually.