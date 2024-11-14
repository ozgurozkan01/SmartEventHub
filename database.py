import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from user import *

DATABASE = 'event.db'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def insert_user(username, password, email, location, interests, first_name, last_name, birth_date, gender, phone_number):
    conn = sqlite3.connect(DATABASE)
    cursor = conn

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    try:
        cursor.execute('''
            INSERT INTO Users (username, 
            password, 
            email, 
            location, 
            interests, 
            first_name, 
            last_name, 
            birth_date, gender, phone_number, profile_photo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (

        username, hashed_password, email, location, interests, first_name, last_name, birth_date, gender, phone_number, "images/default_pp.png"))

        conn.commit()
        print("Kullanıcı başarıyla kaydedildi.")
    except sqlite3.IntegrityError:
        print("Kullanıcı adı, e-posta veya telefon numarası zaten mevcut.")
    except Exception as e:
        print(f"Bir hata oluştu: {e}")

def delete_all_users():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        cursor.execute('''DELETE FROM Users''')
        conn.commit()

        print("Tüm kullanıcılar başarıyla silindi.")
    except Exception as e:
        print(f"Bir hata oluştu: {e}")
    finally:
        conn.close()

def delete_single_user(username=None, email=None):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        if username:
            cursor.execute('''DELETE FROM Users WHERE username = ?''', (username,))
        elif email:
            cursor.execute('''DELETE FROM Users WHERE email = ?''', (email,))
        else:
            print("Silinecek kullanıcı bilgilerini girin (kullanıcı adı veya e-posta).")
            return

        if cursor.rowcount > 0:
            print("Kullanıcı başarıyla silindi.")
        else:
            print("Belirtilen kullanıcı bulunamadı.")

        conn.commit()
    except Exception as e:
        print(f"Bir hata oluştu: {e}")
    finally:
        conn.close()

def get_user_password(username):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM Users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_instance(username=None, email=None):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        if username:
            cursor.execute('SELECT * FROM Users WHERE username = ?', (username,))
        elif email:
            cursor.execute('SELECT * FROM Users WHERE email = ?', (email,))
        else:
            return None

        user_data = cursor.fetchone()

        if user_data:
            user = User(
                username=user_data[1],
                password=user_data[2],
                email=user_data[3],
                location=user_data[4],
                interests=user_data[5],
                first_name=user_data[6],
                last_name=user_data[7],
                birth_date=user_data[8],
                gender=user_data[9],
                phone_number=user_data[10],
                profile_photo=user_data[11]
            )
            return user
        else:
            return None
    finally:
        conn.close()

def print_all_users():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    print("Tüm Kullanıcılar:")
    for user in users:
        print(f"ID: {user[0]}, Username: {user[1]}, Password: {user[2]}, Email: {user[3]}, Location: {user[4]}, Interests: {user[5]}, "
              f"First Name: {user[6]}, Last Name: {user[7]}, Birth Date: {user[8]}, Gender: {user[9]}, "
              f"Phone Number: {user[10]}, Profile Photo: {user[11]}")

    connection.close()

def update_profile_picture_in_db(username, new_profile_picture_url):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE users 
        SET profile_photo = ?
        WHERE username = ?
    ''', (new_profile_picture_url, username))

    conn.commit()
    conn.close()


def insert_event(event_name, description, start_date, finish_date, start_time, finish_time, duration, city, address, category, created_by, image_path):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO events (event_name, description, startDate, finishDate, startTime, finishTime, duration, city, address, category, creator_username, event_image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (event_name, description, start_date, finish_date, start_time, finish_time, str(duration), city, address, category, created_by, image_path))

    conn.commit()
    conn.close()

def get_all_approved_events():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM events WHERE isApproved = 0")
    events = cursor.fetchall()

    conn.close()
    return events


def get_all_approved_events_for_user(username):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Kullanıcının ilgi alanlarını almak
    cursor.execute("SELECT interests FROM users WHERE username = ?", (username,))
    interests = cursor.fetchone()

    if interests:
        interests = interests[0].split(', ')

        query = '''
            SELECT * FROM events
            WHERE isApproved = 0
            AND category IN ({})
        '''.format(','.join(['?'] * len(interests)))

        cursor.execute(query, interests)
        matching_events = cursor.fetchall()

        query_non_matching = '''
            SELECT * FROM events
            WHERE isApproved = 0
            AND category NOT IN ({})
        '''.format(','.join(['?'] * len(interests)))

        cursor.execute(query_non_matching, interests)
        non_matching_events = cursor.fetchall()

        events = matching_events + non_matching_events

    else:
        events = []

    conn.close()
    return events

def get_created_events_by_username(username):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM events WHERE creator_username = ?
    ''', (username,))
    events = cursor.fetchall()
    conn.close()
    return events

def get_event_by_id(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM events WHERE ID = ?
    ''', (event_id,))
    event = cursor.fetchone()  # Tek bir etkinlik döndürülür
    conn.close()
    return event

def get_user_participation_by_category(username):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT e.category, COUNT(*) as participation_count
        FROM participants p
        JOIN events e ON p.event_ID = e.ID
        JOIN users u ON p.user_ID = u.ID
        WHERE u.username = ?
        GROUP BY e.category
        ORDER BY participation_count DESC
    ''', (username,))

    category_participation = cursor.fetchall()

    conn.close()

    return category_participation


def get_suggested_events_for_user(username):
    category_participation = get_user_participation_by_category(username)

    categories_order = [category for category, _ in category_participation]

    conn = get_db_connection()
    cursor = conn.cursor()

    suggested_events = []

    for category in categories_order:
        cursor.execute('''
            SELECT * FROM events
            WHERE category = ? AND isApproved = 1
        ''', (category,))

        events_in_category = cursor.fetchall()
        suggested_events.extend(events_in_category)  # Bu kategorinin etkinliklerini ekle

    conn.close()

    return suggested_events
def print_events():
    events = get_all_approved_events()

    if events:
        for event in events:
            print(f"Etkinlik İsmi: {event['event_name']}")
            print(f"Açıklama: {event['description']}")
            print(f"Başlangıç Tarihi: {event['startDate']}")
            print(f"Bitiş Tarihi: {event['finishDate']}")
            print(f"Başlama Saati: {event['startTime']}")
            print(f"Bitiş Saati: {event['finishTime']}")
            print(f"Süre: {event['duration']}")
            print(f"City: {event['city']}")
            print(f"Address: {event['address']}")
            print(f"Kategori: {event['category']}")
            print(f"Oluşturan: {event['creator_username']}")
            print("------------")
    else:
        print("Veritabanında etkinlik bulunamadı.")


def get_event_images():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT event_image_path FROM events')  # 'events' tablosundaki 'event_image_path' sütununu alıyoruz
    event_images = cursor.fetchall()  # Sonuçları al

    conn.close()

    return [row['event_image_path'] for row in event_images]
