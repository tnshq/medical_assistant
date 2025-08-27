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
import base64

import sys
import importlib

def check_dependencies():
    """Check if all required modules are installed"""
    required_modules = [
        'streamlit', 'pandas', 'PIL', 'cv2', 
        'pytesseract', 'easyocr', 'pyttsx3'
    ]
    
    missing = []
    for module in required_modules:
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        st.error(f"Missing dependencies: {', '.join(missing)}")
        st.info("Run: pip install -r requirements.txt")
        sys.exit(1)
# Import backend modules
from backend.ocr_processor import OCRProcessor
from backend.medicine_extractor import MedicineExtractor
from backend.reminder_system import ReminderSystem
from backend.voice_assistant import VoiceAssistant
from backend.database_handler import DatabaseHandler

# Page configuration
st.set_page_config(
    page_title="MediScan: Voice-Assisted Medicine Scanner",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1e88e5;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        margin-bottom: 30px;
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5em;
    }
    .main-header p {
        color: #f0f0f0;
        margin: 10px 0 0 0;
    }
    .medicine-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        border-left: 4px solid #4caf50;
    }
    .expiry-warning {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .expiry-danger {
        background: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .reminder-active {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'medicines' not in st.session_state:
    st.session_state.medicines = []
if 'reminders' not in st.session_state:
    st.session_state.reminders = []
if 'voice_enabled' not in st.session_state:
    st.session_state.voice_enabled = False
if 'db_handler' not in st.session_state:
    st.session_state.db_handler = DatabaseHandler()
if 'ocr_processor' not in st.session_state:
    st.session_state.ocr_processor = OCRProcessor()
if 'medicine_extractor' not in st.session_state:
    st.session_state.medicine_extractor = MedicineExtractor()
if 'reminder_system' not in st.session_state:
    st.session_state.reminder_system = ReminderSystem()
if 'voice_assistant' not in st.session_state:
    st.session_state.voice_assistant = VoiceAssistant()

# Load existing data
st.session_state.medicines = st.session_state.db_handler.load_medicines()
st.session_state.reminders = st.session_state.reminder_system.load_reminders()

# Header
st.markdown("""
<div class="main-header">
    <h1>🏥 MediScan: MS-VA</h1>
    <p>Voice-Assisted Prescription and Medicine Label Scanner for Reminders and Expiry Alerts</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Voice Assistant Toggle
    st.session_state.voice_enabled = st.checkbox(
        "🔊 Enable Voice Assistant",
        value=st.session_state.voice_enabled
    )
    
    if st.session_state.voice_enabled:
        st.success("Voice Assistant Active")
        voice_language = st.selectbox(
            "Select Language",
            ["en-US", "hi-IN", "es-ES", "fr-FR", "de-DE"]
        )
        st.session_state.voice_assistant.set_language(voice_language)
    
    st.divider()
    
    # Reminder Settings
    st.subheader("🔔 Reminder Settings")
    reminder_days_before = st.number_input(
        "Days before expiry to alert",
        min_value=1,
        max_value=90,
        value=7
    )
    
    daily_reminder_time = st.time_input(
        "Daily reminder time",
        value=datetime.strptime("09:00", "%H:%M").time()
    )
    
    st.divider()
    
    # Statistics
    st.subheader("📊 Statistics")
    total_medicines = len(st.session_state.medicines)
    expiring_soon = sum(1 for m in st.session_state.medicines 
                       if m.get('days_until_expiry', float('inf')) <= reminder_days_before)
    active_reminders = len([r for r in st.session_state.reminders if r['active']])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Medicines", total_medicines)
    with col2:
        st.metric("Expiring Soon", expiring_soon)
    with col3:
        st.metric("Active Reminders", active_reminders)

# Main content area
tab1, tab2, tab3, tab4 = st.tabs(["📷 Scan Medicine", "💊 My Medicines", "⏰ Reminders", "📊 Analytics"])

# Tab 1: Scan Medicine
with tab1:
    st.header("Scan Medicine or Prescription")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Upload Image")
        scan_type = st.radio(
            "Select scan type:",
            ["Medicine Label", "Prescription"]
        )
        
        uploaded_file = st.file_uploader(
            "Choose an image...",
            type=['png', 'jpg', 'jpeg'],
            help="Upload a clear image of medicine label or prescription"
        )
        
        # Camera input option
        camera_photo = st.camera_input("Or take a photo")
        
        if uploaded_file is not None or camera_photo is not None:
            image_to_process = uploaded_file if uploaded_file else camera_photo
            
            # Display image
            image = Image.open(image_to_process)
            st.image(image, caption="Uploaded Image", use_column_width=True)
            
            # Process button
            if st.button("🔍 Process Image", type="primary"):
                with st.spinner("Processing image..."):
                    # OCR Processing
                    ocr_result = st.session_state.ocr_processor.process_image(image)
                    
                    # Extract medicine information
                    if scan_type == "Medicine Label":
                        medicine_info = st.session_state.medicine_extractor.extract_from_label(ocr_result)
                    else:
                        medicine_info = st.session_state.medicine_extractor.extract_from_prescription(ocr_result)
                    
                    # Store in session state for display in col2
                    st.session_state.latest_scan = medicine_info
                    
                    # Save to database
                    if scan_type == "Medicine Label":
                        st.session_state.medicines.append(medicine_info)
                        st.session_state.db_handler.save_medicine(medicine_info)
                    
                    # Voice announcement if enabled
                    if st.session_state.voice_enabled:
                        if scan_type == "Medicine Label":
                            st.session_state.voice_assistant.speak_scan_result(medicine_info)
                        else:
                            medicines_count = len(medicine_info.get('medicines', []))
                            announcement = f"Scanned prescription with {medicines_count} medicines."
                            st.session_state.voice_assistant.speak(announcement)
    
    with col2:
        st.subheader("Extracted Information")
        
        if hasattr(st.session_state, 'latest_scan'):
            latest_result = st.session_state.latest_scan
            
            if latest_result.get('scan_type') == 'label':
                # Display medicine label information
                st.markdown("### 📋 Medicine Details")
                
                info_container = st.container()
                with info_container:
                    st.markdown(f"**Medicine Name:** {latest_result.get('name', 'Not detected')}")
                    st.markdown(f"**Manufacturer:** {latest_result.get('manufacturer', 'Not detected')}")
                    st.markdown(f"**Batch Number:** {latest_result.get('batch_no', 'Not detected')}")
                    st.markdown(f"**Manufacturing Date:** {latest_result.get('mfg_date', 'Not detected')}")
                    st.markdown(f"**Expiry Date:** {latest_result.get('expiry_date', 'Not detected')}")
                    st.markdown(f"**Dosage:** {latest_result.get('dosage', 'Not detected')}")
                    st.markdown(f"**Form:** {latest_result.get('form', 'Not detected')}")
                    st.markdown(f"**Quantity:** {latest_result.get('quantity', 'Not detected')}")
                    
                    # Expiry status
                    if latest_result.get('expiry_date'):
                        days_until_expiry = latest_result.get('days_until_expiry', 0)
                        if days_until_expiry < 0:
                            st.markdown('<div class="expiry-danger">⚠️ This medicine has expired!</div>', 
                                      unsafe_allow_html=True)
                        elif days_until_expiry <= reminder_days_before:
                            st.markdown(f'<div class="expiry-warning">⚠️ Expires in {days_until_expiry} days!</div>', 
                                      unsafe_allow_html=True)
                        else:
                            st.success(f"✅ Valid for {days_until_expiry} days")
                    
                    # Set reminder option
                    st.markdown("### ⏰ Set Reminder")
                    reminder_type = st.selectbox(
                        "Reminder Type",
                        ["Daily", "Twice Daily", "Three Times Daily", "Weekly", "Custom"]
                    )
                    
                    if st.button("Set Reminder"):
                        reminder = st.session_state.reminder_system.create_reminder(
                            latest_result,
                            reminder_type,
                            daily_reminder_time
                        )
                        st.session_state.reminders.append(reminder)
                        st.success("✅ Reminder set successfully!")
                        
                        if st.session_state.voice_enabled:
                            st.session_state.voice_assistant.speak(f"Reminder set for {latest_result.get('name')}")
            
            elif latest_result.get('scan_type') == 'prescription':
                # Display prescription information
                st.markdown("### 📋 Prescription Details")
                
                st.markdown(f"**Doctor:** {latest_result.get('doctor_name', 'Not detected')}")
                st.markdown(f"**Patient:** {latest_result.get('patient_name', 'Not detected')}")
                st.markdown(f"**Date:** {latest_result.get('prescription_date', 'Not detected')}")
                st.markdown(f"**Clinic/Hospital:** {latest_result.get('clinic_hospital', 'Not detected')}")
                
                # Display medicines
                medicines = latest_result.get('medicines', [])
                if medicines:
                    st.markdown("### 💊 Prescribed Medicines")
                    for i, medicine in enumerate(medicines, 1):
                        st.markdown(f"**{i}. {medicine.get('name', 'Unknown')}**")
                        st.markdown(f"   - Dosage: {medicine.get('dosage', 'Not specified')}")
                        st.markdown(f"   - Instructions: {medicine.get('instructions', 'Not specified')}")
                
                # Display general instructions
                instructions = latest_result.get('instructions', [])
                if instructions:
                    st.markdown("### 📝 Instructions")
                    for instruction in instructions:
                        st.markdown(f"- {instruction}")
        else:
            st.info("No scan results yet. Upload an image and process it to see extracted information.")

# Tab 2: My Medicines
with tab2:
    st.header("My Medicine Inventory")
    
    # Search and filter
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_term = st.text_input("🔍 Search medicines", placeholder="Enter medicine name...")
    with col2:
        filter_expired = st.checkbox("Show expired only")
    with col3:
        filter_expiring = st.checkbox("Show expiring soon")
    
    # Display medicines
    filtered_medicines = st.session_state.medicines
    
    if search_term:
        filtered_medicines = [m for m in filtered_medicines 
                             if search_term.lower() in m.get('name', '').lower()]
    
    if filter_expired:
        filtered_medicines = [m for m in filtered_medicines 
                             if m.get('days_until_expiry', float('inf')) < 0]
    
    if filter_expiring:
        filtered_medicines = [m for m in filtered_medicines 
                             if 0 <= m.get('days_until_expiry', float('inf')) <= reminder_days_before]
    
    # Display in grid
    if filtered_medicines:
        cols = st.columns(3)
        for idx, medicine in enumerate(filtered_medicines):
            with cols[idx % 3]:
                # Medicine card
                card_class = "medicine-card"
                if medicine.get('days_until_expiry', float('inf')) < 0:
                    card_class = "expiry-danger"
                elif medicine.get('days_until_expiry', float('inf')) <= reminder_days_before:
                    card_class = "expiry-warning"
                
                st.markdown(f"""
                <div class="{card_class}">
                    <h4>{medicine.get('name', 'Unknown')}</h4>
                    <p><strong>Expiry:</strong> {medicine.get('expiry_date', 'Not specified')}</p>
                    <p><strong>Dosage:</strong> {medicine.get('dosage', 'Not specified')}</p>
                    <p><strong>Quantity:</strong> {medicine.get('quantity', 'Not specified')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("📢", key=f"speak_{idx}", help="Speak details"):
                        if st.session_state.voice_enabled:
                            st.session_state.voice_assistant.speak_scan_result(medicine)
                with col2:
                    if st.button("✏️", key=f"edit_{idx}", help="Edit"):
                        st.info("Edit functionality coming soon")
                with col3:
                    if st.button("🗑️", key=f"delete_{idx}", help="Delete"):
                        medicine_id = medicine.get('id')
                        if medicine_id:
                            st.session_state.db_handler.delete_medicine(medicine_id)
                        st.session_state.medicines = st.session_state.db_handler.load_medicines()
                        st.rerun()
    else:
        st.info("No medicines found. Start by scanning a medicine or prescription.")

# Tab 3: Reminders
with tab3:
    st.header("Medicine Reminders")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Active Reminders")
        
        active_reminders = [r for r in st.session_state.reminders if r['active']]
        
        if active_reminders:
            for reminder in active_reminders:
                st.markdown(f"""
                <div class="reminder-active">
                    <h4>💊 {reminder['medicine_name']}</h4>
                    <p><strong>Type:</strong> {reminder['type']}</p>
                    <p><strong>Time:</strong> {reminder['time']}</p>
                    <p><strong>Next Reminder:</strong> {reminder['next_reminder']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("✅ Mark as Taken", key=f"taken_{reminder['id']}"):
                        st.session_state.reminder_system.mark_as_taken(reminder['id'])
                        st.success("Marked as taken!")
                        if st.session_state.voice_enabled:
                            st.session_state.voice_assistant.speak(f"{reminder['medicine_name']} marked as taken")
                with col2:
                    if st.button("⏸️ Pause", key=f"pause_{reminder['id']}"):
                        st.session_state.reminder_system.pause_reminder(reminder['id'])
                        st.info("Reminder paused")
                        st.rerun()
                with col3:
                    if st.button("🗑️ Delete", key=f"del_rem_{reminder['id']}"):
                        st.session_state.reminder_system.delete_reminder(reminder['id'])
                        st.session_state.reminders = st.session_state.reminder_system.load_reminders()
                        st.rerun()
        else:
            st.info("No active reminders. Set reminders from the Scan Medicine tab.")
    
    with col2:
        st.subheader("Quick Actions")
        
        if st.button("🔊 Read All Reminders"):
            if st.session_state.voice_enabled and active_reminders:
                text = "Your active reminders are: "
                for r in active_reminders:
                    text += f"{r['medicine_name']} at {r['time']}. "
                st.session_state.voice_assistant.speak(text)
        
        if st.button("🔔 Test Notification"):
            st.session_state.reminder_system.send_test_notification()
            st.success("Test notification sent!")
        
        st.divider()
        
        st.subheader("Reminder History")
        history = st.session_state.reminder_system.get_history()
        if history:
            df = pd.DataFrame(history)
            st.dataframe(df, use_container_width=True)

# Tab 4: Analytics
with tab4:
    st.header("Medicine Analytics")
    
    if st.session_state.medicines:
        # Expiry Analysis
        st.subheader("📊 Expiry Status Overview")
        
        col1, col2, col3 = st.columns(3)
        
        expired = len([m for m in st.session_state.medicines 
                      if m.get('days_until_expiry', float('inf')) < 0])
        expiring_soon = len([m for m in st.session_state.medicines 
                           if 0 <= m.get('days_until_expiry', float('inf')) <= reminder_days_before])
        safe = len([m for m in st.session_state.medicines 
                   if m.get('days_until_expiry', float('inf')) > reminder_days_before])
        
        with col1:
            st.metric("Expired", expired, delta=None, delta_color="inverse")
        with col2:
            st.metric("Expiring Soon", expiring_soon, delta=None, delta_color="normal")
        with col3:
            st.metric("Safe", safe, delta=None, delta_color="normal")
        
        # Chart
        try:
            import plotly.express as px
            
            df = pd.DataFrame({
                'Status': ['Expired', 'Expiring Soon', 'Safe'],
                'Count': [expired, expiring_soon, safe]
            })
            
            fig = px.pie(df, values='Count', names='Status', 
                        color_discrete_map={'Expired': '#dc3545', 
                                           'Expiring Soon': '#ffc107', 
                                           'Safe': '#28a745'})
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            st.info("Install plotly for advanced charts: pip install plotly")
        
        # Medicine Timeline
        st.subheader("📅 Expiry Timeline")
        
        timeline_data = []
        for m in st.session_state.medicines:
            if m.get('expiry_date'):
                timeline_data.append({
                    'Medicine': m.get('name', 'Unknown'),
                    'Expiry Date': m.get('expiry_date'),
                    'Days Until Expiry': m.get('days_until_expiry', 0)
                })
        
        if timeline_data:
            timeline_df = pd.DataFrame(timeline_data)
            timeline_df = timeline_df.sort_values('Days Until Expiry')
            
            try:
                fig2 = px.bar(timeline_df, x='Medicine', y='Days Until Expiry',
                             color='Days Until Expiry',
                             color_continuous_scale=['red', 'yellow', 'green'],
                             hover_data=['Expiry Date'])
                st.plotly_chart(fig2, use_container_width=True)
            except:
                st.dataframe(timeline_df, use_container_width=True)
        
        # Compliance Report
        st.subheader("💊 Medication Compliance")
        
        compliance_data = st.session_state.reminder_system.get_compliance_report()
        if compliance_data:
            compliance_df = pd.DataFrame(compliance_data)
            st.dataframe(compliance_df, use_container_width=True)
            
            # Compliance score
            if len(compliance_df) > 0:
                avg_compliance = compliance_df['compliance_rate'].mean()
                st.metric("Overall Compliance", f"{avg_compliance:.1f}%")
    else:
        st.info("No data available. Start by scanning medicines to see analytics.")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>MediScan MS-VA v1.0 | Built with Streamlit & Python</p>
    <p>⚠️ This app is for informational purposes only. Always consult healthcare professionals for medical advice.</p>
</div>
""", unsafe_allow_html=True)

# Background reminder check
if st.session_state.reminders:
    due_reminders = st.session_state.reminder_system.check_due_reminders()
    if due_reminders and st.session_state.voice_enabled:
        for reminder in due_reminders:
            st.session_state.voice_assistant.speak_medicine_reminder(
                reminder['medicine_name'],
                reminder['time'],
                reminder.get('dosage')
            )