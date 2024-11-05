import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

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
            INSERT INTO Users (username, password, email, location, interests, first_name, last_name, birth_date, gender, phone_number, profile_photo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (

        username, hashed_password, email, location, interests, first_name, last_name, birth_date, gender, phone_number, "images/profile.png"))

        print("Kullanıcı başarıyla kaydedildi.")
    except sqlite3.IntegrityError:
        print("Kullanıcı adı, e-posta veya telefon numarası zaten mevcut.")
    except Exception as e:
        print(f"Bir hata oluştu: {e}")


def print_all_users():
    connection = sqlite3.connect(DATABASE)  # Burada "database_name.db" ifadesini kendi veritabanı adınızla değiştirin
    cursor = connection.cursor()

    # Tüm kullanıcıları seç
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    # Kullanıcıları yazdır
    print("Tüm Kullanıcılar:")
    for user in users:
        print(f"ID: {user[0]}, Username: {user[1]}, Email: {user[3]}, Location: {user[4]}, Interests: {user[5]}, "
              f"First Name: {user[6]}, Last Name: {user[7]}, Birth Date: {user[8]}, Gender: {user[9]}, "
              f"Phone Number: {user[10]}, Profile Photo: {user[11]}")

    # Bağlantıyı kapat
    connection.close()