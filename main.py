from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from database import init_db, add_user, update_user_preferences, get_user_preferences
import os
from dotenv import load_dotenv
from app import get_random_verse, get_chapter_content, get_all_translations, get_books_for_translation, AVAILABLE_TRANSLATIONS # Import new functions and AVAILABLE_TRANSLATIONS

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'supersecret') # Use an environment variable or a default

# Removed as it's deprecated in newer Flask versions
# def setup():
#     init_db()

@app.route('/')
def bible_reader():
    translations = get_all_translations()
    books = get_books_for_translation("KJV") # Default to KJV for initial book list
    return render_template('bible_reader.html', translations=translations, books=books)

@app.route('/<string:translation_name>/<string:book_name>/<int:chapter_number>')
def view_chapter(translation_name, book_name, chapter_number):
    chapter_data = get_chapter_content(translation_name, book_name, chapter_number)
    
    # Ensure chapter number from chapter_data is an integer for comparison
    if chapter_data and 'chapter' in chapter_data and isinstance(chapter_data['chapter'], str):
        try:
            chapter_data['chapter'] = int(chapter_data['chapter'])
        except ValueError:
            chapter_data['chapter'] = 1 # Default to 1 if conversion fails

    # Fetch all books for navigation sidebar/dropdown (assuming same for all translations for simplicity)
    books_for_nav = get_books_for_translation(translation_name)
    
    # Find current book to determine total chapters for next/prev logic
    current_book_info = next((book for book in books_for_nav if book['name'].lower() == book_name.lower()), None)
    total_chapters = int(current_book_info['chapters']) if current_book_info and 'chapters' in current_book_info else 100 # Default if not found, ensure int

    return render_template('bible_reader.html',
                           chapter_data=chapter_data,
                           translation=translation_name,
                           book=book_name,
                           chapter=chapter_number,
                           books_for_nav=books_for_nav,
                           total_chapters=total_chapters,
                           translations=get_all_translations()) # Pass all translations here as well

@app.route('/get_books/<string:translation_id>')
def get_books(translation_id):
    books = get_books_for_translation(translation_id)
    return jsonify(books)


@app.route('/preferences', methods=['GET', 'POST'])
def preferences():
    verse_of_the_day = get_random_verse() # Keep for preferences page, or remove if not desired here
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        preferred_method = request.form['preferred_method']
        delivery_time = request.form['delivery_time']
        # bible_translation now comes as a list from the multi-select
        selected_translations = request.form.getlist('bible_translation')
        bible_translations_str = ",".join(selected_translations) # Convert list to comma-separated string
        verse_preference = request.form['verse_preference']

        user_exists = get_user_preferences(phone_number)
        if user_exists:
            update_user_preferences(
                phone_number,
                preferred_method=preferred_method,
                delivery_time=delivery_time,
                bible_ids_str=bible_translations_str, # Pass as string
                verse_of_day_preference=verse_preference
            )
            flash('Your preferences have been updated successfully!', 'success')
        else:
            add_user(
                phone_number,
                preferred_method,
                delivery_time,
                bible_translations_str, # Pass as string
                verse_preference
            )
            flash('Your preferences have been saved successfully!', 'success')
        return redirect(url_for('preferences')) # Redirect back to preferences to show flash message
    
    return render_template('index.html', verse_of_the_day=verse_of_the_day, available_translations=AVAILABLE_TRANSLATIONS)

if __name__ == '__main__':
    init_db() # Initialize the database here instead
    app.run(debug=True)
