import sqlite3

DATABASE_NAME = "bible_app.db"

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT UNIQUE NOT NULL,
            preferred_method TEXT NOT NULL,
            delivery_time TEXT NOT NULL,
            bible_id TEXT NOT NULL, -- Storing translation like 'KJV', 'WEB'
            verse_of_day_preference TEXT NOT NULL -- Storing verse reference like 'john 3:16'
        )
    ''')
    conn.commit()
    conn.close()

def add_user(phone_number, preferred_method, delivery_time, bible_ids_str, verse_of_day_preference):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (phone_number, preferred_method, delivery_time, bible_id, verse_of_day_preference) VALUES (?, ?, ?, ?, ?)",
                  (phone_number, preferred_method, delivery_time, bible_ids_str, verse_of_day_preference))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        print(f"User with phone number {phone_number} already exists.")
        return False
    finally:
        conn.close()

def get_user_preferences(phone_number):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE phone_number = ?", (phone_number,))
    user = c.fetchone()
    conn.close()
    if user:
        # Split the comma-separated string back into a list of translation IDs
        bible_ids_list = user[4].split(',') if user[4] else []
        return {
            "id": user[0],
            "phone_number": user[1],
            "preferred_method": user[2],
            "delivery_time": user[3],
            "bible_id": bible_ids_list, # Now returns a list
            "verse_of_day_preference": user[5]
        }
    return None

def update_user_preferences(phone_number, preferred_method=None, delivery_time=None, bible_ids_str=None, verse_of_day_preference=None):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    updates = []
    params = []
    if preferred_method: 
        updates.append("preferred_method = ?")
        params.append(preferred_method)
    if delivery_time:
        updates.append("delivery_time = ?")
        params.append(delivery_time)
    if bible_ids_str is not None: # Use is not None to allow empty string
        updates.append("bible_id = ?")
        params.append(bible_ids_str)
    if verse_of_day_preference:
        updates.append("verse_of_day_preference = ?")
        params.append(verse_of_day_preference)
    
    if not updates:
        conn.close()
        return False

    params.append(phone_number)
    set_clause = ", ".join(updates)
    c.execute(f"UPDATE users SET {set_clause} WHERE phone_number = ?", tuple(params))
    conn.commit()
    conn.close()
    return True

def delete_user(phone_number):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE phone_number = ?", (phone_number,))
    conn.commit()
    conn.close()
    return True

def get_all_users():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users_data = c.fetchall()
    conn.close()
    users = []
    for user in users_data:
        bible_ids_list = user[4].split(',') if user[4] else []
        users.append({
            "id": user[0],
            "phone_number": user[1],
            "preferred_method": user[2],
            "delivery_time": user[3],
            "bible_id": bible_ids_list, # Now returns a list
            "verse_of_day_preference": user[5]
        })
    return users

if __name__ == "__main__":
    init_db()
    print("Database initialized and user table created.")

    # Example Usage
    # The database schema has changed for bible_id to be a comma-separated string
    add_user("+1234567890", "sms", "08:00", "KJV,WEB", "john 3:16") # Example with multiple translations
    update_user_preferences("+1234567890", preferred_method="call", delivery_time="09:30", bible_ids_str="KJV,ASV") # Example update
    
    user1 = get_user_preferences("+1234567890")
    print(f"Updated User 1 preferences: {user1}")

    # Clean up previous example user
    delete_user("+1987654321")
    user2 = get_user_preferences("+1987654321")
    print(f"User 2 preferences after deletion: {user2}")
