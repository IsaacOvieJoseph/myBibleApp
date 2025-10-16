# config.py
import os

# Twilio (placeholders for now)
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER') # Your Twilio phone number
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER') # Your Twilio WhatsApp enabled number (e.g., 'whatsapp:+1234567890')
# Git Automation
GIT_PAT = os.getenv('GIT_PAT')
