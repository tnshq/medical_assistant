# MediScan: Voice-Assisted Medicine Scanner 💊🔊

## Overview

MediScan is a comprehensive voice-assisted prescription and medicine label scanner designed specifically for elderly users. It combines advanced OCR technology with user-friendly voice feedback to help seniors manage their medications safely and effectively.

## Features

### 🔍 Advanced OCR Scanning
- **Medicine Label Recognition**: Automatically extracts medicine names, dosages, expiry dates, batch numbers, and manufacturer information
- **Prescription Processing**: Reads both handwritten and printed prescriptions
- **Dual OCR Engine**: Google Vision API for high accuracy + EasyOCR as fallback
- **Smart Text Processing**: Intelligent text extraction and structure recognition

### 🔊 Voice-Assisted Interface
- **Elderly-Friendly Voice**: Clear, slow speech optimized for senior users
- **Automatic Announcements**: Reads scan results and medicine information aloud
- **Voice Reminders**: Spoken medicine reminders at scheduled times
- **Customizable Voice Settings**: Adjustable speed, volume, and voice selection

### ⏰ Smart Reminder System
- **Flexible Scheduling**: Daily, twice daily, three times daily, weekly reminders
- **Visual & Audio Alerts**: Both on-screen notifications and voice announcements
- **Compliance Tracking**: Monitor taken vs missed medications
- **Expiry Warnings**: Automatic alerts for expired or soon-to-expire medicines

### 📊 Medicine Database
- **Comprehensive Storage**: Save all scanned medicines with detailed information
- **Search & Filter**: Find medicines by name, manufacturer, or other criteria
- **Expiry Management**: Track expiry dates and get proactive warnings
- **Export Capabilities**: Export data to CSV for external use

## Project Structure

```
mediscan-ms-va/
├── App.py                      # Main Streamlit application frontend
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── backend/                    # Core backend modules
│   ├── __init__.py            # Backend package initialization
│   ├── ocr_processor.py       # OCR processing (Google Vision + EasyOCR)
│   ├── medicine_extractor.py  # Medicine info extraction from OCR text
│   ├── reminder_system.py     # Medicine reminders & notifications
│   ├── voice_assistant.py     # Text-to-speech and voice feedback
│   └── database_handler.py    # Data persistence (JSON-based)
├── data/                      # Application data (auto-created)
│   ├── medicines.json         # Medicine inventory
│   ├── reminders.json         # Reminder settings
│   ├── settings.json          # App settings
│   └── scan_history.json      # Scan history
└── dataset/                   # Sample data for testing
    ├── labels/                # Sample medicine label images
    ├── prescriptions/         # Sample prescription images
    └── medicines.csv          # Sample medicine data
```

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Google Vision API key (optional, for enhanced OCR)

### Step 1: Clone or Download
```bash
# If using git
git clone <repository-url>
cd mediscan-ms-va

# Or download and extract the project files
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Set Up Google Vision API (Optional)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the Vision API
4. Create API credentials (API key)
5. Set environment variable:
   ```bash
   export GOOGLE_VISION_API_KEY="your-api-key-here"
   ```
   Or enter it in the app settings

### Step 4: Run the Application
```bash
streamlit run App.py
```

The application will open in your default web browser at `http://localhost:8501`

## Usage Guide

### 🔍 Scanning Medicines

1. **Navigate to "Scan Medicine/Prescription"**
2. **Upload Image**: Click "Choose an image file" and select a clear photo
3. **Select Scan Type**: Choose between:
   - Medicine Label
   - Handwritten Prescription  
   - Printed Prescription
4. **Process**: Click "Scan and Extract"
5. **Review Results**: Check extracted information
6. **Save**: Save medicines to database or set reminders

### ⏰ Setting Up Reminders

1. **Go to "Medicine Reminders" tab**
2. **Add New Reminder**: Fill in medicine details
3. **Set Schedule**: Choose frequency and times
4. **Configure**: Add special instructions if needed
5. **Activate**: Create the reminder

### 🔊 Voice Features

1. **Enable Voice**: Toggle voice assistant in sidebar
2. **Adjust Settings**: Go to Settings to modify voice speed/volume
3. **Test Voice**: Use "Test Voice" button to verify functionality
4. **Automatic Announcements**: Voice reads scan results automatically

## Configuration

### Voice Settings
- **Speech Rate**: 100-250 words per minute (default: 150)
- **Volume**: 0.0-1.0 (default: 0.9)
- **Language**: English (US/UK), Hindi
- **Voice Type**: Automatically selects clearest voice for elderly users

### OCR Settings  
- **Primary Engine**: Google Vision API (high accuracy) or EasyOCR (offline)
- **API Key**: Google Vision API key for premium OCR features
- **Fallback**: Automatic fallback to EasyOCR if Vision API unavailable

### Reminder Settings
- **Default Time**: Default reminder time for new medications
- **Expiry Alerts**: Days before expiry to show warnings (default: 7)
- **Notifications**: Enable/disable various notification types

## API Keys & External Services

### Google Vision API (Recommended)
- **Purpose**: High-accuracy OCR for medicine labels and prescriptions
- **Setup**: Get API key from Google Cloud Console
- **Cost**: Pay-per-use (first 1000 requests/month free)
- **Fallback**: EasyOCR used if not available

### EasyOCR (Included)
- **Purpose**: Free, offline OCR processing
- **Setup**: Installed automatically with requirements
- **Accuracy**: Good for printed text, limited for handwriting
- **Performance**: Slower than Google Vision but free

## Troubleshooting

### Common Issues

**1. Import Errors**
```
Error: Failed to import backend modules
```
**Solution**: Ensure all files are in correct directories and dependencies installed

**2. OCR Not Working**
```
Error: Could not extract text from image
```
**Solutions**:
- Check image quality (clear, well-lit, high resolution)
- Verify API key if using Google Vision
- Try different OCR engine in settings

**3. Voice Not Working**
```
Error: Voice assistant not available
```
**Solutions**:
- Check audio drivers
- Try different voice in settings
- Restart application

**4. Reminder Issues**
```
Error: Failed to create reminder
```
**Solutions**:
- Check all required fields filled
- Verify date/time formats
- Check file permissions in data directory

### Performance Tips

1. **Image Quality**: Use clear, well-lit photos for best OCR results
2. **Google Vision**: Use API key for better accuracy on complex prescriptions
3. **Voice Settings**: Adjust speech rate for user comfort (slower for elderly)
4. **Regular Cleanup**: Use database cleanup features for old data

## Similar Projects & References

Here are some GitHub projects related to medical OCR and medicine management:

### Medical OCR Projects
1. **[Medical-OCR-Data-Extraction](https://github.com/Tanguy9862/Medical-OCR-Data-Extraction)** - OCR for medical documents
2. **[MediScribe-OCR](https://github.com/Shriram2005/MediScribe-OCR)** - Medical prescription OCR system
3. **[Medical-Data-Extraction](https://github.com/prathyyyyy/Medical-Data-Extraction)** - Extract data from medical documents
4. **[medical-data-extraction](https://github.com/abhijeetk597/medical-data-extraction)** - OCR project for medical data
5. **[Medical-Prescription-OCR](https://github.com/Aniket025/Medical-Prescription-OCR)** - Reading medical prescriptions

### Medicine Reminder Projects
6. **[medical-reminder](https://github.com/PMO-IT/medical-reminder)** - Java-based text-to-speech medicine reminder
7. **[medsched](https://github.com/BVNCodeTech/medsched)** - Self-hosted medical reminder app
8. **[Medecro_AI_PERSONALIZED_PLATFORM](https://github.com/GautamBytes/Medecro_AI_PERSONALIZED_PLATFORM)** - AI personalized medical platform

### OCR Technology Projects
9. **[easy-paddle-ocr](https://github.com/theos-ai/easy-paddle-ocr)** - Easy OCR using PaddleOCR
10. **[optical-character-recognition](https://github.com/limchiahooi/optical-character-recognition)** - OCR in Python
11. **[itsitgroup/ocr-streamlit-demo](https://github.com/itsitgroup/ocr-streamlit-demo)** - Streamlit OCR application

## Development Blueprint

### Core Technologies
- **Frontend**: Streamlit (Python web framework)
- **OCR**: Google Vision API + EasyOCR
- **Voice**: pyttsx3 (Text-to-speech)
- **Data**: JSON file storage
- **Images**: PIL/Pillow for image processing
- **UI**: HTML/CSS for custom styling

### Key Code Components

#### 1. OCR Processing (`ocr_processor.py`)
```python
class OCRProcessor:
    def __init__(self, api_key=None):
        # Initialize Google Vision API and EasyOCR

    def process_image(self, image, scan_type):
        # Process image with OCR engines
        # Return structured text results
```

#### 2. Medicine Extraction (`medicine_extractor.py`)
```python
class MedicineExtractor:
    def extract_medicines(self, ocr_result, scan_type):
        # Parse OCR text for medicine information
        # Return structured medicine data
```

#### 3. Voice Assistant (`voice_assistant.py`)
```python
class VoiceAssistant:
    def __init__(self, language="en-US"):
        # Initialize TTS engine with elderly-friendly settings

    def speak_medicine_reminder(self, medicine_name, dosage):
        # Speak medicine reminders clearly
```

#### 4. Reminder System (`reminder_system.py`)
```python
class ReminderSystem:
    def create_reminder(self, reminder_data):
        # Create and schedule medicine reminders

    def get_due_reminders(self):
        # Check for due reminders
```

#### 5. Database Handler (`database_handler.py`)
```python
class DatabaseHandler:
    def save_medicine(self, medicine_data):
        # Save medicine to JSON database

    def get_expiring_medicines(self, days_ahead):
        # Get medicines expiring soon
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature-name`
3. **Make changes** with proper documentation
4. **Test thoroughly** with various medicine images
5. **Submit pull request** with clear description

### Development Setup
```bash
# Clone repository
git clone <repo-url>
cd mediscan-ms-va

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run in development mode
streamlit run App.py --server.runOnSave true
```

## License

This project is open source and available under the MIT License.

## Support

For support, issues, or feature requests:
1. **Check troubleshooting section** above
2. **Review similar projects** for additional insights
3. **Create GitHub issue** with detailed description
4. **Include error logs** and system information

## Acknowledgments

- **Google Vision API** for advanced OCR capabilities
- **EasyOCR** for free OCR processing
- **Streamlit** for rapid web app development
- **pyttsx3** for text-to-speech functionality
- **Open source community** for inspiration and libraries

---

**Made with ❤️ for elderly care and medication safety**
