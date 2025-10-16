import requests
import os
import time
import schedule
from dotenv import load_dotenv
from twilio.rest import Client
from gtts import gTTS
from pydub import AudioSegment
from twilio.twiml.voice_response import VoiceResponse
from git import Repo
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, TWILIO_WHATSAPP_NUMBER, GIT_PAT
from database import init_db, add_user, get_user_preferences, get_all_users

load_dotenv()

# --- Temporarily assigning values directly for debugging ---START
TWILIO_ACCOUNT_SID=os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN=os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER=os.getenv('TWILIO_PHONE_NUMBER')
TWILIO_WHATSAPP_NUMBER=os.getenv('TWILIO_WHATSAPP_NUMBER')
GIT_PAT=os.getenv('GIT_PAT')
# --- Temporarily assigning values directly for debugging ---END

# --- Hardcoded lists for Bible reader navigation (for demonstration) ---
AVAILABLE_TRANSLATIONS = [
    {"id": "cherokee", "name": "Cherokee New Testament"},
    {"id": "cuv", "name": "Chinese Union Version"},
    {"id": "bkr", "name": "Bible kralická"},
    {"id": "asv", "name": "American Standard Version (1901)"},
    {"id": "bbe", "name": "Bible in Basic English"},
    {"id": "darby", "name": "Darby Bible"},
    {"id": "dra", "name": "Douay-Rheims 1899 American Edition"},
    {"id": "kjv", "name": "King James Version"},
    {"id": "web", "name": "World English Bible"},
    {"id": "ylt", "name": "Young's Literal Translation (NT only)"},
    {"id": "oeb-cw", "name": "Open English Bible, Commonwealth Edition"},
    {"id": "webbe", "name": "World English Bible, British Edition"},
    {"id": "oeb-us", "name": "Open English Bible, US Edition"},
    {"id": "clementine", "name": "Clementine Latin Vulgate"},
    {"id": "almeida", "name": "João Ferreira de Almeida"},
    {"id": "rccv", "name": "Protestant Romanian Corrected Cornilescu Version"}
]

# A comprehensive list of books with chapter counts for common translations.
# Using KJV/standard Protestant canon chapter counts for all for simplicity,
# as bible-api.com doesn't provide full metadata endpoints for this.
AVAILABLE_BOOKS = {
    "KJV": [
        {"name": "Genesis", "chapters": 50},
        {"name": "Exodus", "chapters": 40},
        {"name": "Leviticus", "chapters": 27},
        {"name": "Numbers", "chapters": 36},
        {"name": "Deuteronomy", "chapters": 34},
        {"name": "Joshua", "chapters": 24},
        {"name": "Judges", "chapters": 21},
        {"name": "Ruth", "chapters": 4},
        {"name": "1 Samuel", "chapters": 31},
        {"name": "2 Samuel", "chapters": 24},
        {"name": "1 Kings", "chapters": 22},
        {"name": "2 Kings", "chapters": 25},
        {"name": "1 Chronicles", "chapters": 29},
        {"name": "2 Chronicles", "chapters": 36},
        {"name": "Ezra", "chapters": 10},
        {"name": "Nehemiah", "chapters": 13},
        {"name": "Esther", "chapters": 10},
        {"name": "Job", "chapters": 42},
        {"name": "Psalms", "chapters": 150},
        {"name": "Proverbs", "chapters": 31},
        {"name": "Ecclesiastes", "chapters": 12},
        {"name": "Song of Solomon", "chapters": 8},
        {"name": "Isaiah", "chapters": 66},
        {"name": "Jeremiah", "chapters": 52},
        {"name": "Lamentations", "chapters": 5},
        {"name": "Ezekiel", "chapters": 48},
        {"name": "Daniel", "chapters": 12},
        {"name": "Hosea", "chapters": 14},
        {"name": "Joel", "chapters": 3},
        {"name": "Amos", "chapters": 9},
        {"name": "Obadiah", "chapters": 1},
        {"name": "Jonah", "chapters": 4},
        {"name": "Micah", "chapters": 7},
        {"name": "Nahum", "chapters": 3},
        {"name": "Habakkuk", "chapters": 3},
        {"name": "Zephaniah", "chapters": 3},
        {"name": "Haggai", "chapters": 2},
        {"name": "Zechariah", "chapters": 14},
        {"name": "Malachi", "chapters": 4},
        {"name": "Matthew", "chapters": 28},
        {"name": "Mark", "chapters": 16},
        {"name": "Luke", "chapters": 24},
        {"name": "John", "chapters": 21},
        {"name": "Acts", "chapters": 28},
        {"name": "Romans", "chapters": 16},
        {"name": "1 Corinthians", "chapters": 16},
        {"name": "2 Corinthians", "chapters": 13},
        {"name": "Galatians", "chapters": 6},
        {"name": "Ephesians", "chapters": 6},
        {"name": "Philippians", "chapters": 4},
        {"name": "Colossians", "chapters": 4},
        {"name": "1 Thessalonians", "chapters": 5},
        {"name": "2 Thessalonians", "chapters": 3},
        {"name": "1 Timothy", "chapters": 6},
        {"name": "2 Timothy", "chapters": 4},
        {"name": "Titus", "chapters": 3},
        {"name": "Philemon", "chapters": 1},
        {"name": "Hebrews", "chapters": 13},
        {"name": "James", "chapters": 5},
        {"name": "1 Peter", "chapters": 5},
        {"name": "2 Peter", "chapters": 3},
        {"name": "1 John", "chapters": 5},
        {"name": "2 John", "chapters": 1},
        {"name": "3 John", "chapters": 1},
        {"name": "Jude", "chapters": 1},
        {"name": "Revelation", "chapters": 22}
    ]
}

# Populate other translations with the same book list for simplicity
for trans in AVAILABLE_TRANSLATIONS:
    if trans["id"] != "KJV":
        AVAILABLE_BOOKS[trans["id"].upper()] = AVAILABLE_BOOKS["KJV"]

def get_all_translations():
    return AVAILABLE_TRANSLATIONS

def get_books_for_translation(translation_id):
    return AVAILABLE_BOOKS.get(translation_id.upper(), [])

import random

def get_random_verse(translations=["kjv"], verse_reference="john 3:16"):
    if isinstance(translations, str):
        translations = [translations] # Ensure it's a list
    
    # Randomly pick one of the user's preferred translations
    chosen_translation = random.choice(translations)

    api_url = f"https://bible-api.com/{verse_reference}?translation={chosen_translation.lower()}"
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        
        if data and 'verses' in data and data['verses']:
            verse_text = " ".join([v['text'] for v in data['verses']])
            verse_reference_full = data['verses'][0]['book_name'] + " " + str(data['verses'][0]['chapter']) + ":" + str(data['verses'][0]['verse'])
            translation_used = data['translation_name'] if 'translation_name' in data else chosen_translation.upper()
            
            return {
                'text': verse_text.strip(),
                'reference': verse_reference_full,
                'translation': translation_used
            }
        else:
            return {'text': "Could not fetch verse content.", 'reference': "", 'translation': ""}
    except requests.exceptions.RequestException as e:
        return {'text': f"Could not fetch verse: {e}", 'reference': "", 'translation': ""}

def get_chapter_content(translation, book_name, chapter_number):
    # bible-api.com endpoint for a whole chapter
    api_url = f"https://bible-api.com/{book_name} {chapter_number}?translation={translation.lower()}"
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()

        if data and 'verses' in data and data['verses']:
            # Extract and join all verse texts for the chapter
            chapter_text = " ".join([v['text'] for v in data['verses']])
            return {
                'text': chapter_text.strip(),
                'book_name': data['verses'][0]['book_name'],
                'chapter': data['verses'][0]['chapter'],
                'translation': data['translation_name'] if 'translation_name' in data else translation.upper(),
                'verses': data['verses'] # Return individual verses for finer control in template
            }
        else:
            return {'text': "Could not fetch chapter content.", 'book_name': "", 'chapter': "", 'translation': "", 'verses': []}
    except requests.exceptions.RequestException as e:
        return {'text': f"Could not fetch chapter: {e}", 'book_name': "", 'chapter': "", 'translation': "", 'verses': []}

def generate_voice_note(text, filename="voice_note.ogg"):
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save("temp.mp3")
        
        # Convert mp3 to ogg (opus codec) for WhatsApp compatibility
        audio = AudioSegment.from_mp3("temp.mp3")
        audio.export(filename, format="ogg", codec="opus")
        
        os.remove("temp.mp3") # Clean up temp mp3 file
        return filename
    except Exception as e:
        print(f"Error generating voice note: {e}")
        return None

def generate_twiml_for_call(verse_text):
    response = VoiceResponse()
    response.say("Hello from your daily Bible verse app!")
    response.pause(length=1)
    response.say("Here is your verse for today:")
    response.pause(length=1)
    response.say(verse_text)
    response.say("Have a blessed day!")
    return str(response)

def commit_and_push_files(file_paths, commit_message="Automated media update"):
    try:
        repo = Repo(os.getcwd())
        repo.git.add(file_paths)
        repo.index.commit(commit_message)
        
        # Use PAT for authentication
        remote_url = repo.remote().url
        if "github.com" in remote_url:
            # Assuming GitHub, format URL with PAT
            # Example: https://YOUR_PAT@github.com/YOUR_USERNAME/YOUR_REPO.git
            auth_remote_url = remote_url.replace(
                "https://", f"https://{GIT_PAT}@"
            )
            with repo.remotes.origin.config_writer as cw:
                cw.set("url", auth_remote_url)

        origin = repo.remote(name='origin')
        origin.push()
        print(f"Successfully committed and pushed: {commit_message}")
        return True
    except Exception as e:
        print(f"Error committing and pushing files: {e}")
        return False

def make_call(to_number, twiml_url):
    try:
        call = twilio_client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            url=twiml_url  # URL to your TwiML instructions
        )
        print(f"Call SID: {call.sid}")
        return True
    except Exception as e:
        print(f"Error making call: {e}")
        return False

def send_message(to_number, message_body, preferred_method, media_url=None):
    try:
        if preferred_method == "sms":
            message = twilio_client.messages.create(
                to=to_number,
                from_=TWILIO_PHONE_NUMBER,
                body=message_body
            )
        elif preferred_method == "whatsapp_text":
            message = twilio_client.messages.create(
                to=f"whatsapp:{to_number}",
                from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
                body=message_body
            )
        elif preferred_method == "whatsapp_voice_note":
            if media_url:
                message = twilio_client.messages.create(
                    to=f"whatsapp:{to_number}",
                    from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
                    media_url=[media_url] # Twilio expects a list of URLs
                )
            else:
                print("Media URL is required for WhatsApp voice note.")
                return False
        else:
            print(f"Unsupported preferred method: {preferred_method}")
            return False
        print(f"Message SID: {message.sid}")
        return True
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

def send_daily_verse(user):
    print("Running daily verse delivery...")
    verse = get_random_verse(user["bible_id"], user["verse_of_day_preference"] if user["verse_of_day_preference"] != "random" else "john 3:16") # Placeholder verse_id for now
    
    full_message = f"Daily Verse: {verse['text']}"

    if user["preferred_method"] in ["sms", "whatsapp_text"]:
        send_message(user["phone_number"], full_message, user["preferred_method"])
    elif user["preferred_method"] == "whatsapp_voice_note":
        voice_note_file = generate_voice_note(full_message)
        if voice_note_file:
            # Host this file publicly and provide a URL.
            # For automation, we'll push it to a repo for GitHub Pages hosting.
            commit_and_push_files([voice_note_file], f"Add voice note for {user['phone_number']}")
            # Assuming GitHub Pages, the URL would be something like:
            # public_url = f"https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/{voice_note_file}"
            # send_message(user["phone_number"], "", user["preferred_method"], media_url=public_url)
            print(f"Voice note generated and pushed: {voice_note_file}. You need to configure its public URL.")
        else:
            print("Failed to generate voice note.")
    elif user["preferred_method"] == "call":
        twiml_content = generate_twiml_for_call(full_message)
        twiml_file_name = f"twiml_verse_{user['phone_number']}.xml"
        with open(twiml_file_name, "w") as f:
            f.write(twiml_content)

        # Host this TwiML publicly and provide its URL.
        # For automation, we'll push it to a repo for GitHub Pages hosting.
        commit_and_push_files([twiml_file_name], f"Add TwiML for call to {user['phone_number']}")
        # Assuming GitHub Pages, the URL would be something like:
        # public_url = f"https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/{twiml_file_name}"
        # make_call(user["phone_number"], twiml_url=public_url)
        print(f"TwiML generated and pushed: {twiml_file_name}. You need to configure its public URL.\n{twiml_content}")
    else:
        print(f"User {user['phone_number']} has preferred method {user['preferred_method']}, which is not supported.")

if __name__ == "__main__":
    init_db()  # Initialize the database
    print("Welcome to the Bible App!")

    # Removed hardcoded user creation/retrieval from scheduler startup
    # All user management should primarily happen via the web app (main.py)
    
    print("Loading user preferences from database...")
    all_users = get_all_users()
    if all_users:
        for user in all_users:
            print(f"Loaded user: {user['phone_number']} | Method: {user['preferred_method']} | Time: {user['delivery_time']}")
    else:
        print("No users found in the database. Please add preferences via the web app.")

    # Schedule daily verse delivery for each user
    # This part remains the same, as it correctly uses get_all_users()
    users_for_scheduling = get_all_users() 
    if users_for_scheduling:
        for user in users_for_scheduling:
            schedule.every().day.at(user['delivery_time']).do(send_daily_verse, user=user) 

    print("Scheduler started. Waiting for jobs...")
    while True:
        schedule.run_pending()
        time.sleep(1)
