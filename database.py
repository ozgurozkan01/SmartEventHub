from werkzeug.security import generate_password_hash
from user import *
from utilities import *

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

def insert_score(user_id, points=0):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO scores (user_ID, points, earned_date)
            VALUES (?, ?, DATE('now'))
        ''', (user_id, points))

        conn.commit()
        print(f"Kullanıcı ID: {user_id} için skor kaydedildi.")
    except sqlite3.IntegrityError:
        print("Bu kullanıcı için skor zaten mevcut.")
    except Exception as e:
        print(f"Bir hata oluştu: {e}")
    finally:
        conn.close()

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
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]
    else:
        return None

def get_user_instance(username=None, email=None):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        if username:
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        elif email:
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
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
                profile_photo=user_data[11],
                status=user_data[12]
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

    print(f'New Picture : {new_profile_picture_url}')
    print(f'Username : {username}')

    cursor.execute('''
        UPDATE users 
        SET profile_photo = ? 
        WHERE username = ?
    ''', (new_profile_picture_url, username))

    conn.commit()

    if cursor.rowcount > 0:
        print(f"Successfully updated profile photo for {username}")
    else:
        print("No rows updated. Check if the username exists and is correct.")


def update_user(user_id, data):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE ID = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        print("Kullanıcı bulunamadı.")
        conn.close()
        return

    updated_data = {
        'username': data.get('username', user[1]),
        'password': data.get('password', user[2]),
        'email': data.get('email', user[3]),
        'location': data.get('location', user[4]),
        'interests': data.get('interests', user[5]),
        'first_name': data.get('first_name', user[6]),
        'last_name': data.get('last_name', user[7]),
        'birth_date': data.get('birth_date', user[8]),
        'gender': data.get('gender', user[9]),
        'phone_number': data.get('phone', user[10]),
        'profile_photo': user[11],
        'status': user[12]
    }

    query = '''
    UPDATE users
    SET username = ?, password = ?, email = ?, location = ?, interests = ?, 
        first_name = ?, last_name = ?, birth_date = ?, gender = ?, phone_number = ?, 
        profile_photo = ?, status = ?
    WHERE ID = ?
    '''

    cursor.execute(query, (
        updated_data['username'],
        updated_data['password'],
        updated_data['email'],
        updated_data['location'],
        ', '.join(updated_data['interests']),
        updated_data['first_name'],
        updated_data['last_name'],
        updated_data['birth_date'],
        updated_data['gender'],
        updated_data['phone_number'],
        updated_data['profile_photo'],
        updated_data['status'],
        user_id
    ))

    conn.commit()

    cursor.execute("SELECT * FROM users WHERE ID = ?", (user_id,))
    updated_user = cursor.fetchone()

    print(f"Güncellenmiş kullanıcı verisi: {updated_user}")

    conn.close()

def update_event_in_db(event_id, data):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    query = '''
        UPDATE events SET 
            event_name = ?, 
            description = ?, 
            startDate = ?, 
            finishDate = ?, 
            startTime = ?, 
            finishTime = ?, 
            duration = ?, 
            city = ?, 
            address = ?, 
            category = ? 
        WHERE ID = ?
    '''
    cursor.execute(query, (
        data['event-name'],
        data['event-description'],
        data['event-start-date'],
        data['event-finish-date'],
        data['event-start-time'],
        data['event-finish-time'],
        data['duration'],
        data['event-city'],
        data['event-address'],
        data['category'],
        event_id
    ))

    conn.commit()

    cursor.execute("SELECT * FROM events WHERE ID = ?", (event_id,))
    updated_event = cursor.fetchone()
    print("Updated event:", updated_event)

    conn.close()

def insert_event(event_name, description, start_date, finish_date, start_time, finish_time, duration, city, address, category, created_by):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO events (event_name, description, startDate, finishDate, startTime, finishTime, duration, city, address, category, creator_username)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (event_name, description, start_date, finish_date, start_time, finish_time, str(duration), city, address, category, created_by))

    conn.commit()
    conn.close()


def get_user_score(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT points FROM scores 
            WHERE user_ID = ?
        ''', (user_id,))

        result = cursor.fetchone()

        if result:
            return result[0]
        else:
            return 0

    except Exception as e:
        print(f"Bir hata oluştu: {e}")
        return None
    finally:
        conn.close()

def update_user_score(user_id, points_to_add):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    earned_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        cursor.execute('''SELECT points FROM scores WHERE user_ID = ?''', (user_id,))
        result = cursor.fetchone()

        if result:
            current_score = result[0]
            new_total = current_score + points_to_add
            cursor.execute('''UPDATE scores SET points = ?, earned_date = ? WHERE user_ID = ?''',
                           (new_total, earned_date, user_id))
        else:
            cursor.execute('''INSERT INTO scores (user_ID, points, earned_date) VALUES (?, ?, ?)''',
                           (user_id, points_to_add, earned_date))

        conn.commit()
    except Exception as e:
        print(f"Bir hata oluştu: {e}")
    finally:
        conn.close()


def get_user_id_by_username(username):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT ID FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user:
        return user[0]
    else:
        return None

    conn.close()

def get_all_approved_events():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM events WHERE isApproved = 1")
    events = cursor.fetchall()

    conn.close()
    return events

def is_username_available(new_username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (new_username,)).fetchone()
    conn.close()
    return user is None

def get_all_approved_events_for_user(username):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT interests FROM users WHERE username = ?", (username,))
    interests = cursor.fetchone()

    if interests:
        interests = interests[0].split(', ')

        query = '''
            SELECT * FROM events
            WHERE isApproved = 1
            AND category IN ({})
        '''.format(','.join(['?'] * len(interests)))

        cursor.execute(query, interests)
        matching_events = cursor.fetchall()

        query_non_matching = '''
            SELECT * FROM events
            WHERE isApproved = 1
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
        SELECT ID, event_name, description, startDate, finishDate, startTime, finishTime, city, address, category, creator_username, isApproved 
        FROM events 
        WHERE creator_username = ? 
    ''', (username,))

    events = cursor.fetchall()
    conn.close()

    return [
        {
            "ID": event[0],
            "event_name": event[1],
            "description": event[2],
            "startDate": event[3],
            "finishDate": event[4],
            "startTime": event[5],
            "finishTime": event[6],
            "city": event[7],
            "address": event[8],
            "category": event[9],
            "creator_username": event[10],
            "is_approved": event[11],
        }
        for event in events
    ]

def get_event_by_id(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM events WHERE ID = ?
    ''', (event_id,))
    event = cursor.fetchone()
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

    cursor.execute('''
        SELECT ID FROM Users
        WHERE username = ?
    ''', (username,))
    user_id_row = cursor.fetchone()

    if not user_id_row:
        conn.close()
        raise ValueError("Kullanıcı bulunamadı")

    user_id = user_id_row[0]

    suggested_events = []

    for category in categories_order:
        cursor.execute('''
            SELECT e.*, 
                   (SELECT COUNT(*) 
                    FROM participants p2 
                    WHERE p2.event_ID = e.ID) AS participation_count
            FROM Events e
            LEFT JOIN participants p ON e.ID = p.event_ID AND p.user_ID = ?
            WHERE e.category = ? AND e.isApproved = 1 AND p.event_ID IS NULL
            ORDER BY participation_count DESC
        ''', (user_id, category))

        events_in_category = cursor.fetchall()
        suggested_events.extend(events_in_category)

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

def join_event_for_user(user_id, event_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO participants (user_ID, event_ID)
            VALUES (?, ?)
        ''', (user_id, event_id))
        conn.commit()

        if is_first_participation(user_id):
            update_user_score(user_id, 20)
        else:
            update_user_score(user_id, 10)

        return {"status": "success", "message": "Etkinliğe başarıyla katıldınız!"}
    except sqlite3.IntegrityError:
        return {"status": "info", "message": "Zaten bu etkinliğe katıldınız."}
    except Exception as e:
        return {"status": "danger", "message": f"Bir hata oluştu: {e}"}
    finally:
        conn.close()

def leave_event_for_user(user_id, event_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            DELETE FROM participants
            WHERE user_ID = ? AND event_ID = ?
        ''', (user_id, event_id))
        conn.commit()

        if cursor.rowcount > 0:
            update_user_score(user_id, -10)

        return {"status": "success", "message": "Etkinlikten başarıyla çıktınız!"}
    except Exception as e:
        return {"status": "danger", "message": f"Bir hata oluştu: {e}"}
    finally:
        conn.close()

def delete_event_from_db(event_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            DELETE FROM participants WHERE event_ID = ?
        ''', (event_id,))

        cursor.execute('''
            DELETE FROM events WHERE ID = ?
        ''', (event_id,))

        conn.commit()
    except Exception as e:
        conn.rollback()  # Rollback in case of error
        print(f"Error deleting event {event_id}: {e}")
    finally:
        conn.close()

def is_first_participation(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT COUNT(*) FROM participants WHERE user_ID = ?
        ''', (user_id,))
        result = cursor.fetchone()
        return result[0] == 0
    except Exception as e:
        print(f"Bir hata oluştu: {e}")
        return False
    finally:
        conn.close()


def get_user_attended_events(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT e.ID, e.event_name, e.description, e.startDate, e.finishDate, 
                   e.startTime, e.finishTime, e.city, e.address, e.category, e.creator_username
            FROM events e
            INNER JOIN participants p ON e.ID = p.event_ID
            WHERE p.user_ID = ?
        ''', (user_id,))

        events = cursor.fetchall()

        return [
            {
                "ID": event[0],
                "event_name": event[1],
                "description": event[2],
                "startDate": event[3],
                "finishDate": event[4],
                "startTime": event[5],
                "finishTime": event[6],
                "city": event[7],
                "address": event[8],
                "category": event[9],
                "creator_username": event[10],
            }
            for event in events
        ]
    except Exception as e:
        print(f"Bir hata oluştu: {e}")
        return []
    finally:
        conn.close()

def insert_message(sender_id, event_id, receiver_id, message_text):
    sent_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO messages (sender_ID, event_ID, receiver_ID, message_text, sent_time)
        VALUES (?, ?, ?, ?, ?)
    ''', (sender_id, event_id, receiver_id, message_text, sent_time))

    conn.commit()
    conn.close()

def is_user_participant(user_id, event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 1 
        FROM participants 
        WHERE user_id = ? AND event_id = ?
    ''', (user_id, event_id))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_event_creator_username(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT creator_username
        FROM events
        WHERE id = ?
    ''', (event_id,))
    result = cursor.fetchone()
    conn.close()
    return result['creator_username'] if result else None


def get_messages_for_event(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT sender_ID, message_text, sent_time
        FROM messages
        WHERE event_ID = ?
        ORDER BY sent_time ASC
    ''', (event_id,))

    messages = cursor.fetchall()
    conn.close()

    return messages


def get_username_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT username FROM users WHERE ID = ?', (user_id,))
    user = cursor.fetchone()

    conn.close()

    if user:
        return user['username']
    return None


def get_participants(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p.user_ID
        FROM Participants p
        WHERE p.event_ID = ?
    ''', (event_id,))

    participant_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute('''
        SELECT u.username, u.email, u.location, u.interests, u.first_name, u.last_name, u.birth_date, u.gender, 
               u.phone_number, u.profile_photo, u.status
        FROM Users u
        WHERE u.ID IN ({})
    '''.format(','.join(['?'] * len(participant_ids))), participant_ids)

    users = [User(username=row[0], email=row[1], location=row[2], interests=row[3], first_name=row[4],
                  last_name=row[5], birth_date=row[6], gender=row[7], phone_number=row[8],
                  profile_photo=row[9], status=row[10]) for row in cursor.fetchall()]

    conn.close()
    return users




def set_user_as_admin(username):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE users SET status = 'admin' WHERE username = ?",
            (username,)
        )
        conn.commit()

        if cursor.rowcount > 0:
            print(f"{username} adlı kullanıcı artık admin.")
        else:
            print(f"{username} adlı kullanıcı bulunamadı.")
    except Exception as e:
        print(f"Bir hata oluştu: {e}")
    finally:
        conn.close()


def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")

    users = cursor.fetchall()

    conn.close()

    return users


def delete_user_from_database(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

        conn.commit()

        print(f"Kullanıcı (ID: {user_id}) başarıyla silindi.")
    except sqlite3.Error as e:
        print(f"Veritabanı hatası: {e}")
    finally:
        conn.close()


def is_admin(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT status FROM users WHERE ID = ?', (user_id,))
    result = cursor.fetchone()

    if result and result[0] == 'admin':
        return True
    return False


def get_all_events():
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM events"

    cursor.execute(query)

    events = cursor.fetchall()

    conn.close()

    return events


def update_event_approval(event_id, new_approval_status):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE events
            SET isApproved = ?
            WHERE ID = ?
        ''', (new_approval_status, event_id))

        conn.commit()

        print("Etkinlik onayı başarıyla güncellendi.")

    except sqlite3.Error as e:
        print(f"Veritabanı hatası: {e}")

    finally:
        conn.close()


import sqlite3


def get_email_by_username(username):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT email FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]
    else:
        return None


def update_user_status(user_id, user_statu):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE users
            SET status = ?
            WHERE ID = ?
        ''', (user_statu, user_id))

        conn.commit()

        if cursor.rowcount == 0:
            raise Exception("Kullanıcı bulunamadı veya zaten hedef statüye sahip.")

    except Exception as e:
        print(f"Hata: {str(e)}")
        conn.rollback()

    finally:
        conn.close()


def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE ID = ?", (user_id,))
    user = cursor.fetchone()

    conn.close()

    if user:
        user_dict = {
            'ID': user[0],
            'username': user[1],
            'password': user[2],
            'email': user[3],
            'location': user[4],
            'interests': user[5],
            'first_name': user[6],
            'last_name': user[7],
            'birth_date': user[8],
            'gender': user[9],
            'phone_number': user[10],
            'profile_photo': user[11],
            'status': user[12]
        }
        return user_dict
    else:
        return None