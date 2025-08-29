"""
MediScan: Voice-Assisted Prescription and Medicine Label Scanner
Main Streamlit Application Frontend
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
from PIL import Image
import io
import sys
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import backend modules
try:
    from backend.ocr_processor import OCRProcessor
    # Create the OCRProcessor object
    ocr_processor = OCRProcessor(api_key="AIzaSyBn2sq8Zj6V9hPiUHfkh7ps6FpPdFp2tvQ")
    from backend.medicine_extractor import MedicineExtractor
    from backend.reminder_system import ReminderSystem
    from backend.voice_assistant import VoiceAssistant
    from backend.database_handler import DatabaseHandler
except ImportError as e:
    st.error(f"Failed to import backend modules: {e}")
    st.info("Please ensure all backend files are in the 'backend' directory")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="MediScan: Voice-Assisted Medicine Scanner",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        text-align: center;
        background: linear-gradient(90deg, #1e3a8a, #3b82f6);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }
    .medicine-card {
        background: #f8fafc;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        margin: 10px 0;
    }
    .expiry-warning {
        background: #fef2f2;
        border-left: 4px solid #ef4444;
        padding: 10px;
        margin: 5px 0;
        border-radius: 4px;
    }
    .expiry-safe {
        background: #f0fdf4;
        border-left: 4px solid #22c55e;
        padding: 10px;
        margin: 5px 0;
        border-radius: 4px;
    }
    .voice-status {
        position: fixed;
        top: 10px;
        right: 10px;
        background: #1e40af;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'medicines': [],
        'reminders': [],
        'voice_enabled': True,
        'scan_results': None,
        'current_page': 'scan',
        'setup_medicine': None,
        'redirect_to_reminders': False,
        'last_scan_time': None,
        'error_message': None,
        'success_message': None
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# Initialize backend components
@st.cache_resource
def initialize_backend():
    """Initialize backend components with caching"""
    try:
        # Get API key from environment or use placeholder
        api_key = os.getenv("GOOGLE_VISION_API_KEY", "AIzaSyBn2sq8Zj6V9hPiUHfkh7ps6FpPdFp2tvQ")

        components = {
            'ocr_processor': OCRProcessor(api_key=api_key),
            'medicine_extractor': MedicineExtractor(),
            'reminder_system': ReminderSystem(),
            'voice_assistant': VoiceAssistant(),
            'database_handler': DatabaseHandler()
        }

        logger.info("Backend components initialized successfully")
        return components

    except Exception as e:
        logger.error(f"Failed to initialize backend: {e}")
        st.error(f"Failed to initialize backend components: {e}")
        return None

def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()

    # Initialize backend
    backend = initialize_backend()
    if not backend:
        st.error("❌ Failed to initialize application backend")
        return

    # Display header
    st.markdown("""
    <div class="main-header">
        <h1>💊 MediScan: MS-VA</h1>
        <p>Voice-Assisted Prescription and Medicine Label Scanner for Elderly Care</p>
    </div>
    """, unsafe_allow_html=True)

    # Voice status indicator
    voice_status = "🔊 ON" if st.session_state.voice_enabled else "🔇 OFF"
    st.markdown(f'<div class="voice-status">Voice: {voice_status}</div>', unsafe_allow_html=True)

    # Sidebar navigation
    with st.sidebar:
        st.header("🎯 Navigation")

        pages = {
            "📸 Scan Medicine/Prescription": "scan",
            "⏰ Medicine Reminders": "reminders", 
            "🔊 Voice Assistant": "voice",
            "📊 Medicine Database": "database",
            "⚙️ Settings": "settings"
        }

        selected_page = st.radio("Choose Function:", list(pages.keys()))
        current_page = pages[selected_page]

        st.markdown("---")

        # Quick voice toggle
        if st.button("🔊/🔇 Toggle Voice"):
            st.session_state.voice_enabled = not st.session_state.voice_enabled
            if st.session_state.voice_enabled:
                backend['voice_assistant'].speak("Voice assistant enabled")
            st.rerun()

        # Quick statistics
        st.subheader("📈 Quick Stats")
        try:
            stats = backend['database_handler'].get_statistics()
            st.metric("Total Medicines", stats.get('total_medicines', 0))
            st.metric("Expiring Soon", stats.get('expiring_soon', 0))
            st.metric("Recent Scans", stats.get('scans_last_30_days', 0))
        except Exception as e:
            st.warning("Could not load statistics")

    # Display messages
    if st.session_state.get('error_message'):
        st.error(st.session_state.error_message)
        st.session_state.error_message = None

    if st.session_state.get('success_message'):
        st.success(st.session_state.success_message)
        st.session_state.success_message = None

    # Route to appropriate page
    if current_page == "scan":
        scan_page(backend)
    elif current_page == "reminders":
        reminders_page(backend)
    elif current_page == "voice":
        voice_assistant_page(backend)
    elif current_page == "database":
        database_page(backend)
    elif current_page == "settings":
        settings_page(backend)

def scan_page(backend):
    """Medicine and prescription scanning page"""
    st.header("📸 Scan Medicine Labels or Prescriptions")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📤 Upload Image")

        # File uploader
        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=['png', 'jpg', 'jpeg'],
            help="Upload a clear image of medicine label or handwritten/printed prescription"
        )

        # Scan type selection
        scan_type = st.selectbox(
            "Select scan type:",
            ["Medicine Label", "Handwritten Prescription", "Printed Prescription"],
            help="Choose the type of document you're scanning"
        )

        if uploaded_file is not None:
            # Display uploaded image
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)

            # Process button
            if st.button("🔍 Scan and Extract", type="primary"):
                process_scan(backend, image, scan_type, uploaded_file.name)

    with col2:
        st.subheader("📋 Extracted Information")
        display_scan_results(backend)

def process_scan(backend, image, scan_type, filename):
    """Process the uploaded image for OCR and medicine extraction"""
    start_time = time.time()

    with st.spinner("🔍 Processing image... Please wait"):
        try:
            # OCR Processing
            ocr_result = backend['ocr_processor'].process_image(image=image, scan_type=scan_type)

            if not ocr_result.get('text'):
                st.error("❌ Could not extract text from image. Please try with a clearer image.")
                if st.session_state.voice_enabled:
                    backend['voice_assistant'].speak_error_message('scan_failed')
                return

            # Medicine extraction
            medicine_info = backend['medicine_extractor'].extract_medicines(ocr_result, scan_type)

            # Store results in session state
            st.session_state.scan_results = {
                'medicine_info': medicine_info,
                'ocr_result': ocr_result,
                'scan_type': scan_type,
                'filename': filename,
                'processed_at': datetime.now().isoformat()
            }

            # Save scan history
            processing_time = time.time() - start_time
            scan_history_entry = {
                'scan_type': scan_type,
                'success': bool(medicine_info.get('medicines')),
                'medicines_found': len(medicine_info.get('medicines', [])),
                'confidence': ocr_result.get('confidence', 0.0),
                'ocr_engine': ocr_result.get('engine', 'unknown'),
                'processing_time': processing_time,
                'filename': filename
            }
            backend['database_handler'].save_scan_history(scan_history_entry)

            # Voice feedback
            if st.session_state.voice_enabled and medicine_info.get('medicines'):
                medicine_count = len(medicine_info['medicines'])
                if medicine_count == 1:
                    medicine_name = medicine_info['medicines'][0].get('name', 'unknown medicine')
                    backend['voice_assistant'].speak_scan_result(medicine_info['medicines'][0])
                else:
                    voice_text = f"Found {medicine_count} medicines in the scan"
                    backend['voice_assistant'].speak(voice_text)

            st.success("✅ Image processed successfully!")

        except Exception as e:
            error_msg = f"Error processing image: {str(e)}"
            logger.error(error_msg)
            st.error(f"❌ {error_msg}")

            if st.session_state.voice_enabled:
                backend['voice_assistant'].speak_error_message('scan_failed', str(e))

def display_scan_results(backend):
    """Display the results of the last scan"""
    scan_results = st.session_state.get('scan_results')

    if not scan_results:
        st.info("📷 Upload and scan an image to see extracted information here.")
        return

    medicine_info = scan_results['medicine_info']

    # Display patient information if available
    if medicine_info.get('patient_info'):
        st.subheader("👤 Patient Information")
        patient_info = medicine_info['patient_info']
        for key, value in patient_info.items():
            if value:
                st.write(f"**{key.title()}:** {value}")
        st.markdown("---")

    # Display medicines
    medicines = medicine_info.get('medicines', [])
    if medicines:
        st.subheader(f"💊 Detected Medicines ({len(medicines)})")

        for i, medicine in enumerate(medicines):
            with st.expander(f"Medicine {i+1}: {medicine.get('name', 'Unknown')}", expanded=True):

                # Display medicine details in columns
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Name:** {medicine.get('name', 'N/A')}")
                    st.write(f"**Dosage:** {medicine.get('dosage', 'N/A')}")
                    st.write(f"**Form:** {medicine.get('form', 'N/A')}")

                with col2:
                    st.write(f"**Manufacturer:** {medicine.get('manufacturer', 'N/A')}")
                    st.write(f"**Batch No:** {medicine.get('batch_no', 'N/A')}")
                    st.write(f"**Expiry Date:** {medicine.get('expiry_date', 'N/A')}")

                # Additional fields for prescriptions
                if 'frequency' in medicine:
                    st.write(f"**Frequency:** {medicine.get('frequency', 'N/A')}")
                if 'duration' in medicine:
                    st.write(f"**Duration:** {medicine.get('duration', 'N/A')}")
                if 'instructions' in medicine:
                    st.write(f"**Instructions:** {medicine.get('instructions', 'N/A')}")

                # Action buttons
                col_btn1, col_btn2, col_btn3 = st.columns(3)

                with col_btn1:
                    if st.button(f"💾 Save", key=f"save_{i}"):
                        if backend['database_handler'].save_medicine(medicine):
                            st.success("Medicine saved!")
                            if st.session_state.voice_enabled:
                                backend['voice_assistant'].speak(f"Saved {medicine.get('name', 'medicine')} to database")
                        else:
                            st.error("Failed to save medicine")

                with col_btn2:
                    if st.button(f"⏰ Set Reminder", key=f"reminder_{i}"):
                        st.session_state.setup_medicine = medicine
                        st.session_state.redirect_to_reminders = True
                        st.rerun()

                with col_btn3:
                    if st.button(f"🔊 Read Aloud", key=f"speak_{i}"):
                        if st.session_state.voice_enabled:
                            backend['voice_assistant'].speak_scan_result(medicine)

        # Save all medicines button
        st.markdown("---")
        col_save_all, col_clear = st.columns(2)

        with col_save_all:
            if st.button("💾 Save All Medicines", type="primary"):
                saved_count = 0
                for medicine in medicines:
                    if backend['database_handler'].save_medicine(medicine):
                        saved_count += 1

                if saved_count > 0:
                    st.success(f"✅ Saved {saved_count} medicines to database!")
                    if st.session_state.voice_enabled:
                        backend['voice_assistant'].speak(f"Saved {saved_count} medicines to your database")
                else:
                    st.error("Failed to save medicines")

        with col_clear:
            if st.button("🗑️ Clear Results"):
                st.session_state.scan_results = None
                st.rerun()

    else:
        st.warning("⚠️ No medicines detected in the scan. Please try with a clearer image.")

def reminders_page(backend):
    """Medicine reminders management page"""
    st.header("⏰ Medicine Reminders")

    # Check if redirected from scan page
    if st.session_state.get('redirect_to_reminders'):
        st.session_state.redirect_to_reminders = False
        if st.session_state.get('setup_medicine'):
            st.info("🎯 Setting up reminder for scanned medicine...")

    # Create tabs
    tab1, tab2, tab3 = st.tabs(["➕ Add New Reminder", "📋 Active Reminders", "📅 Today's Schedule"])

    with tab1:
        create_reminder_form(backend)

    with tab2:
        display_active_reminders(backend)

    with tab3:
        display_todays_schedule(backend)

def create_reminder_form(backend):
    """Form to create a new reminder"""
    st.subheader("Set New Medicine Reminder")

    # Pre-fill if coming from scan
    default_medicine = st.session_state.get('setup_medicine', {})

    with st.form("new_reminder_form"):
        col1, col2 = st.columns(2)

        with col1:
            medicine_name = st.text_input(
                "Medicine Name", 
                value=default_medicine.get('name', ''),
                help="Enter the name of the medicine"
            )

            dosage = st.text_input(
                "Dosage", 
                value=default_medicine.get('dosage', ''),
                help="e.g., 1 tablet, 5ml, 500mg"
            )

            frequency = st.selectbox(
                "Frequency",
                ["Once daily", "Twice daily", "Three times daily", "Four times daily", "Weekly", "As needed"],
                help="How often should the medicine be taken?"
            )

        with col2:
            start_date = st.date_input(
                "Start Date", 
                value=datetime.now().date(),
                help="When to start the medication"
            )

            duration_days = st.number_input(
                "Duration (days)", 
                min_value=1, 
                max_value=365, 
                value=30,
                help="How many days to continue the medication"
            )

            # Time inputs based on frequency
            times = []
            if frequency == "Once daily":
                time1 = st.time_input("Time", value=datetime.strptime("09:00", "%H:%M").time())
                times = [time1.strftime("%H:%M")]
            elif frequency == "Twice daily":
                time1 = st.time_input("Morning", value=datetime.strptime("08:00", "%H:%M").time())
                time2 = st.time_input("Evening", value=datetime.strptime("20:00", "%H:%M").time())
                times = [time1.strftime("%H:%M"), time2.strftime("%H:%M")]
            elif frequency == "Three times daily":
                time1 = st.time_input("Morning", value=datetime.strptime("08:00", "%H:%M").time())
                time2 = st.time_input("Afternoon", value=datetime.strptime("14:00", "%H:%M").time())
                time3 = st.time_input("Evening", value=datetime.strptime("20:00", "%H:%M").time())
                times = [time1.strftime("%H:%M"), time2.strftime("%H:%M"), time3.strftime("%H:%M")]

        instructions = st.text_area(
            "Special Instructions (optional)",
            value=default_medicine.get('instructions', ''),
            help="Any special instructions for taking the medicine"
        )

        submitted = st.form_submit_button("⏰ Create Reminder", type="primary")

        if submitted:
            if not medicine_name or not dosage:
                st.error("Please fill in medicine name and dosage")
            else:
                # Create reminder data
                reminder_data = {
                    'medicine_name': medicine_name,
                    'dosage': dosage,
                    'frequency': frequency,
                    'times': times,
                    'start_date': start_date.isoformat(),
                    'duration_days': duration_days,
                    'instructions': instructions,
                    'active': True,
                    'created_at': datetime.now().isoformat()
                }

                if backend['reminder_system'].create_reminder(reminder_data):
                    st.success(f"✅ Reminder created for {medicine_name}!")

                    if st.session_state.voice_enabled:
                        backend['voice_assistant'].speak_medicine_reminder(
                            medicine_name, dosage, frequency, instructions
                        )

                    # Clear setup medicine from session
                    if 'setup_medicine' in st.session_state:
                        del st.session_state['setup_medicine']

                    st.rerun()
                else:
                    st.error("❌ Failed to create reminder. Please try again.")

def display_active_reminders(backend):
    """Display all active reminders"""
    st.subheader("Active Medicine Reminders")

    try:
        active_reminders = backend['reminder_system'].get_active_reminders()

        if active_reminders:
            for reminder in active_reminders:
                with st.expander(f"💊 {reminder['medicine_name']} - {reminder['frequency']}", expanded=False):
                    col1, col2, col3 = st.columns([3, 2, 1])

                    with col1:
                        st.write(f"**Dosage:** {reminder['dosage']}")
                        st.write(f"**Times:** {', '.join(reminder['times'])}")
                        if reminder.get('instructions'):
                            st.write(f"**Instructions:** {reminder['instructions']}")

                    with col2:
                        st.write(f"**Start Date:** {reminder['start_date']}")
                        st.write(f"**Duration:** {reminder['duration_days']} days")
                        st.write(f"**Status:** {'Active' if reminder.get('active') else 'Inactive'}")

                    with col3:
                        if st.button("🔇 Disable", key=f"disable_{reminder['id']}"):
                            if backend['reminder_system'].disable_reminder(reminder['id']):
                                st.success("Reminder disabled")
                                st.rerun()

                        if st.button("🗑️ Delete", key=f"delete_{reminder['id']}"):
                            if backend['reminder_system'].delete_reminder(reminder['id']):
                                st.success("Reminder deleted")
                                st.rerun()

                        if st.button("🔊 Test", key=f"test_{reminder['id']}"):
                            if st.session_state.voice_enabled:
                                backend['voice_assistant'].speak_medicine_reminder(
                                    reminder['medicine_name'],
                                    reminder['dosage'],
                                    instructions=reminder.get('instructions')
                                )
        else:
            st.info("📭 No active reminders found. Create your first reminder above!")

    except Exception as e:
        st.error(f"Error loading reminders: {e}")

def display_todays_schedule(backend):
    """Display today's medicine schedule"""
    st.subheader("📅 Today's Medicine Schedule")

    try:
        todays_reminders = backend['reminder_system'].get_todays_reminders()

        if todays_reminders:
            # Create schedule entries
            schedule_entries = []
            for reminder in todays_reminders:
                for time_slot in reminder['times']:
                    schedule_entries.append({
                        'time': time_slot,
                        'medicine': reminder['medicine_name'],
                        'dosage': reminder['dosage'],
                        'instructions': reminder.get('instructions', ''),
                        'reminder_id': reminder['id']
                    })

            # Sort by time
            schedule_entries.sort(key=lambda x: x['time'])

            # Display schedule
            for entry in schedule_entries:
                col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

                current_time = datetime.now().time()
                entry_time = datetime.strptime(entry['time'], "%H:%M").time()

                # Determine status
                if current_time >= entry_time:
                    time_status = "⏰ Time Now"
                    time_color = "🟢"
                else:
                    time_status = "⏳ Upcoming"
                    time_color = "🟡"

                with col1:
                    st.write(f"{time_color} **{entry['time']}**")
                    st.write(f"_{time_status}_")

                with col2:
                    st.write(f"**{entry['medicine']}**")
                    st.write(f"{entry['dosage']}")

                with col3:
                    if entry['instructions']:
                        st.write(f"_{entry['instructions']}_")
                    else:
                        st.write("_No special instructions_")

                with col4:
                    if current_time >= entry_time:
                        if st.button("✅ Taken", key=f"taken_{entry['reminder_id']}_{entry['time']}"):
                            if backend['reminder_system'].mark_taken(entry['reminder_id']):
                                st.success("Marked as taken!")
                                if st.session_state.voice_enabled:
                                    backend['voice_assistant'].speak_reminder_confirmation(
                                        entry['medicine'], 'taken'
                                    )
                                st.rerun()

                        if st.button("❌ Missed", key=f"missed_{entry['reminder_id']}_{entry['time']}"):
                            if backend['reminder_system'].mark_missed(entry['reminder_id']):
                                st.warning("Marked as missed")
                                if st.session_state.voice_enabled:
                                    backend['voice_assistant'].speak_reminder_confirmation(
                                        entry['medicine'], 'missed'
                                    )
                                st.rerun()

                    if st.button("🔊 Announce", key=f"speak_{entry['reminder_id']}_{entry['time']}"):
                        if st.session_state.voice_enabled:
                            backend['voice_assistant'].speak_medicine_reminder(
                                entry['medicine'],
                                entry['dosage'],
                                entry['time'],
                                entry['instructions']
                            )

                st.markdown("---")

        else:
            st.info("📅 No medicines scheduled for today!")

    except Exception as e:
        st.error(f"Error loading today's schedule: {e}")

def voice_assistant_page(backend):
    """Voice assistant interaction page"""
    st.header("🔊 Voice Assistant")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🎤 Voice Controls")

        # Voice status
        status = backend['voice_assistant'].get_status()
        if status['available']:
            st.success("✅ Voice assistant is ready")
        else:
            st.error("❌ Voice assistant not available")

        # Test voice button
        if st.button("🧪 Test Voice", type="primary"):
            if backend['voice_assistant'].test_voice():
                st.success("🎵 Voice test completed")
            else:
                st.error("❌ Voice test failed")

        st.markdown("---")

        # Text to speech
        st.subheader("📝 Text to Speech")
        text_input = st.text_area(
            "Enter text to speak:",
            height=100,
            placeholder="Type something for the voice assistant to say..."
        )

        col_speak, col_stop = st.columns(2)

        with col_speak:
            if st.button("🔊 Speak Text"):
                if text_input.strip():
                    if backend['voice_assistant'].speak(text_input):
                        st.success("🎵 Speaking...")
                    else:
                        st.error("Failed to speak text")
                else:
                    st.warning("⚠️ Please enter some text first")

        with col_stop:
            if st.button("⏸️ Stop Speaking"):
                backend['voice_assistant'].stop_speaking()
                st.info("🛑 Speech stopped")

    with col2:
        st.subheader("💡 Voice Commands Help")

        # Quick action buttons
        st.subheader("🚀 Quick Actions")

        if st.button("📊 Read Medicine Count"):
            try:
                stats = backend['database_handler'].get_statistics()
                total = stats.get('total_medicines', 0)
                expiring = stats.get('expiring_soon', 0)

                message = f"You have {total} medicines in your database."
                if expiring > 0:
                    message += f" {expiring} medicines are expiring soon."

                backend['voice_assistant'].speak(message)
            except Exception as e:
                st.error(f"Error reading statistics: {e}")

        if st.button("⏰ Read Today's Reminders"):
            try:
                todays_reminders = backend['reminder_system'].get_todays_reminders()
                if todays_reminders:
                    count = sum(len(r['times']) for r in todays_reminders)
                    message = f"You have {count} medicine doses scheduled for today."
                else:
                    message = "You have no medicines scheduled for today."

                backend['voice_assistant'].speak(message)
            except Exception as e:
                st.error(f"Error reading reminders: {e}")

        # Help information
        st.markdown("---")
        st.subheader("ℹ️ Voice Features")

        features = [
            "🔊 **Scan Results**: Automatically reads medicine names after scanning",
            "⏰ **Reminders**: Speaks medicine reminders at scheduled times",
            "📢 **Announcements**: Reads important information aloud",
            "🧪 **Testing**: Test voice functionality anytime",
            "⚙️ **Settings**: Adjust voice speed and volume in settings"
        ]

        for feature in features:
            st.markdown(feature)

        st.info("💡 **Tip**: Voice assistant is designed to be elderly-friendly with clear, slow speech.")

def database_page(backend):
    """Medicine database and history page"""
    st.header("📊 Medicine Database & History")

    # Get database statistics
    try:
        stats = backend['database_handler'].get_statistics()

        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Medicines", stats.get('total_medicines', 0))
        with col2:
            st.metric("Expired", stats.get('expired_medicines', 0))
        with col3:
            st.metric("Expiring Soon", stats.get('expiring_soon', 0))
        with col4:
            st.metric("Recent Scans", stats.get('scans_last_30_days', 0))

        st.markdown("---")

        # Create tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "💊 All Medicines", 
            "⚠️ Expiry Alerts", 
            "📈 Analytics", 
            "📤 Export Data"
        ])

        with tab1:
            display_medicines_database(backend)

        with tab2:
            display_expiry_alerts(backend)

        with tab3:
            display_analytics(backend, stats)

        with tab4:
            display_export_options(backend)

    except Exception as e:
        st.error(f"Error loading database: {e}")

def display_medicines_database(backend):
    """Display all medicines in database"""
    st.subheader("💊 All Saved Medicines")

    try:
        medicines = backend['database_handler'].load_medicines()

        if medicines:
            # Search functionality
            search_term = st.text_input("🔍 Search medicines:", placeholder="Search by name, manufacturer, etc.")

            if search_term:
                medicines = backend['database_handler'].search_medicines(search_term)
                st.write(f"Found {len(medicines)} matches for '{search_term}'")

            # Display medicines
            for medicine in medicines:
                with st.expander(f"💊 {medicine.get('name', 'Unknown')} - {medicine.get('dosage', 'N/A')}"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"**Name:** {medicine.get('name', 'N/A')}")
                        st.write(f"**Dosage:** {medicine.get('dosage', 'N/A')}")
                        st.write(f"**Form:** {medicine.get('form', 'N/A')}")
                        st.write(f"**Manufacturer:** {medicine.get('manufacturer', 'N/A')}")

                    with col2:
                        st.write(f"**Batch No:** {medicine.get('batch_no', 'N/A')}")
                        st.write(f"**Expiry Date:** {medicine.get('expiry_date', 'N/A')}")
                        st.write(f"**MFG Date:** {medicine.get('mfg_date', 'N/A')}")

                        # Expiry status
                        status = medicine.get('expiry_status', 'unknown')
                        if status == 'expired':
                            st.error("🚨 EXPIRED")
                        elif status == 'expiring_soon':
                            st.warning("⚠️ Expiring Soon")
                        elif status == 'safe':
                            st.success("✅ Safe")
                        else:
                            st.info("❓ Unknown")

                    with col3:
                        if st.button("🗑️ Delete", key=f"del_{medicine.get('id')}"):
                            if backend['database_handler'].delete_medicine(medicine.get('id')):
                                st.success("Medicine deleted")
                                st.rerun()

                        if st.button("⏰ Add Reminder", key=f"rem_{medicine.get('id')}"):
                            st.session_state.setup_medicine = medicine
                            st.session_state.redirect_to_reminders = True
                            st.rerun()

                        if st.button("🔊 Read Info", key=f"speak_{medicine.get('id')}"):
                            if st.session_state.voice_enabled:
                                backend['voice_assistant'].speak_scan_result(medicine)

        else:
            st.info("📭 No medicines saved yet. Scan some medicines to build your database!")

    except Exception as e:
        st.error(f"Error displaying medicines: {e}")

def display_expiry_alerts(backend):
    """Display medicines that are expired or expiring soon"""
    st.subheader("⚠️ Expiry Alerts")

    try:
        # Get expired medicines
        expired = backend['database_handler'].get_expired_medicines()
        expiring_soon = backend['database_handler'].get_expiring_medicines(days_ahead=30)

        if expired:
            st.error(f"🚨 **{len(expired)} Expired Medicines**")
            for medicine in expired:
                st.markdown(f"""
                <div class="expiry-warning">
                    <strong>{medicine.get('name', 'Unknown')}</strong><br>
                    Expired: {medicine.get('expiry_date', 'Unknown date')}<br>
                    Days overdue: {abs(medicine.get('days_until_expiry', 0))}
                </div>
                """, unsafe_allow_html=True)

        if expiring_soon:
            st.warning(f"⚠️ **{len(expiring_soon)} Medicines Expiring Soon**")
            for medicine in expiring_soon:
                days_left = medicine.get('days_until_expiry', 0)

                if days_left <= 7:
                    css_class = "expiry-warning"
                    urgency = "🔴 URGENT"
                else:
                    css_class = "expiry-safe"
                    urgency = "🟡 MODERATE"

                st.markdown(f"""
                <div class="{css_class}">
                    <strong>{medicine.get('name', 'Unknown')}</strong> - {urgency}<br>
                    Expires: {medicine.get('expiry_date', 'Unknown date')}<br>
                    Days remaining: {days_left}
                </div>
                """, unsafe_allow_html=True)

        if not expired and not expiring_soon:
            st.success("✅ All medicines are within safe expiry dates!")

    except Exception as e:
        st.error(f"Error checking expiry dates: {e}")

def display_analytics(backend, stats):
    """Display database analytics and charts"""
    st.subheader("📈 Medicine Analytics")

    try:
        # Medicine forms chart
        if stats.get('by_form'):
            st.subheader("Medicine Forms Distribution")
            form_data = stats['by_form']
            st.bar_chart(form_data)

        # Manufacturer distribution
        if stats.get('by_manufacturer'):
            st.subheader("Top Manufacturers")
            mfr_data = dict(sorted(stats['by_manufacturer'].items(), key=lambda x: x[1], reverse=True)[:10])
            st.bar_chart(mfr_data)

        # Recent scan activity
        scan_history = backend['database_handler'].get_scan_history(days=30)
        if scan_history:
            st.subheader("Recent Scan Activity")

            # Process scan data for visualization
            scan_by_date = {}
            for scan in scan_history:
                scan_date = scan['timestamp'][:10]  # Get date part
                scan_by_date[scan_date] = scan_by_date.get(scan_date, 0) + 1

            if scan_by_date:
                df_scans = pd.DataFrame(list(scan_by_date.items()), columns=['Date', 'Scans'])
                df_scans['Date'] = pd.to_datetime(df_scans['Date'])
                df_scans = df_scans.set_index('Date')
                st.line_chart(df_scans)

        # Success rate
        successful_scans = len([s for s in scan_history if s.get('success', False)])
        total_scans = len(scan_history)
        if total_scans > 0:
            success_rate = (successful_scans / total_scans) * 100
            st.metric("Scan Success Rate", f"{success_rate:.1f}%")

    except Exception as e:
        st.error(f"Error generating analytics: {e}")

def display_export_options(backend):
    """Display data export options"""
    st.subheader("📤 Export Your Data")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💊 Medicine Data")

        if st.button("📥 Export Medicines (CSV)"):
            try:
                medicines = backend['database_handler'].load_medicines()
                if medicines:
                    df = pd.DataFrame(medicines)
                    csv = df.to_csv(index=False)

                    st.download_button(
                        label="💾 Download Medicines CSV",
                        data=csv,
                        file_name=f"medicines_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("⚠️ No medicines to export")
            except Exception as e:
                st.error(f"Export failed: {e}")

    with col2:
        st.subheader("📊 Backup Data")

        if st.button("💾 Create Full Backup"):
            try:
                if backend['database_handler'].backup_data():
                    st.success("✅ Backup created successfully!")
                else:
                    st.error("❌ Backup failed")
            except Exception as e:
                st.error(f"Backup failed: {e}")

def settings_page(backend):
    """Application settings page"""
    st.header("⚙️ Application Settings")

    # Load current settings
    try:
        current_settings = backend['database_handler'].load_settings()

        # Voice settings
        st.subheader("🔊 Voice Settings")

        col1, col2 = st.columns(2)

        with col1:
            voice_enabled = st.checkbox(
                "Enable Voice Assistant", 
                value=current_settings.get('voice_enabled', True)
            )

            voice_rate = st.slider(
                "Speech Rate (words per minute)", 
                100, 250, 
                current_settings.get('voice_rate', 150)
            )

        with col2:
            voice_volume = st.slider(
                "Voice Volume", 
                0.0, 1.0, 
                current_settings.get('voice_volume', 0.9)
            )

            voice_language = st.selectbox(
                "Voice Language",
                ["en-US", "en-GB", "hi-IN"],
                index=0 if current_settings.get('voice_language', 'en-US') == 'en-US' else 1
            )

        # OCR settings
        st.markdown("---")
        st.subheader("📷 OCR Settings")

        ocr_engine = st.selectbox(
            "Primary OCR Engine",
            ["google_vision", "easyocr"],
            index=0 if current_settings.get('ocr_engine', 'google_vision') == 'google_vision' else 1
        )

        # API key input
        api_key = st.text_input(
            "Google Vision API Key",
            value="",
            type="password",
            help="Enter your Google Vision API key for enhanced OCR"
        )

        # Reminder settings
        st.markdown("---")
        st.subheader("⏰ Reminder Settings")

        col3, col4 = st.columns(2)

        with col3:
            reminder_days = st.number_input(
                "Days Before Expiry to Alert",
                min_value=1, max_value=30,
                value=current_settings.get('reminder_days_before_expiry', 7)
            )

        with col4:
            default_time = st.time_input(
                "Default Reminder Time",
                value=datetime.strptime(current_settings.get('default_reminder_time', '09:00'), '%H:%M').time()
            )

        # Save settings
        if st.button("💾 Save Settings", type="primary"):
            new_settings = {
                'voice_enabled': voice_enabled,
                'voice_rate': voice_rate,
                'voice_volume': voice_volume,
                'voice_language': voice_language,
                'ocr_engine': ocr_engine,
                'reminder_days_before_expiry': reminder_days,
                'default_reminder_time': default_time.strftime('%H:%M')
            }

            if api_key:
                # Update OCR processor with new API key
                backend['ocr_processor'] = OCRProcessor(api_key=api_key)

            if backend['database_handler'].save_settings(new_settings):
                # Update voice assistant settings
                backend['voice_assistant'].update_settings(
                    rate=voice_rate,
                    volume=voice_volume,
                    enabled=voice_enabled
                )

                # Update session state
                st.session_state.voice_enabled = voice_enabled

                st.success("✅ Settings saved successfully!")

                if voice_enabled:
                    backend['voice_assistant'].speak("Settings have been updated successfully")
            else:
                st.error("❌ Failed to save settings")

        # Test voice with new settings
        if st.button("🧪 Test Voice with Current Settings"):
            # Temporarily apply settings
            backend['voice_assistant'].set_speech_rate(voice_rate)
            backend['voice_assistant'].set_volume(voice_volume)
            backend['voice_assistant'].set_voice_enabled(voice_enabled)

            if backend['voice_assistant'].test_voice():
                st.success("🎵 Voice test completed with current settings")
            else:
                st.error("❌ Voice test failed")

    except Exception as e:
        st.error(f"Error loading settings: {e}")

if __name__ == "__main__":
    # Ensure required directories exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("dataset/labels", exist_ok=True)
    os.makedirs("dataset/prescriptions", exist_ok=True)

    # Run main application
    main()
