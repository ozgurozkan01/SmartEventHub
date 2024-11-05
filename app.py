from flask import Flask, render_template, request, redirect, url_for, flash
from database import insert_user
import sys
import sqlite3

sys.stdout.reconfigure(encoding='utf-8')


app = Flask(__name__)

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/forgetPassword')
def reset_password():
    return render_template('forgetPassword.html')

@app.route('/createAccount')
def create_account():
    return render_template('createAccount.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    location = request.form.get('location', '')
    interests = request.form.getlist('interests')
    first_name = request.form['firstName']
    last_name = request.form['lastName']
    birth_date = request.form['birthDate']
    gender = request.form['gender']
    phone_number = request.form['phone']
    profile_photo = request.files.get('profile_photo')

    interests_str = ', '.join(interests)

    if insert_user(username, password, email, location, interests_str, first_name, last_name, birth_date, gender, phone_number):
        flash("Kullanıcı başarıyla kaydedildi.")
    else:
        flash("Kullanıcı adı, e-posta veya telefon numarası zaten mevcut.")

    return redirect(url_for('create_account'))


def print_all_users():
    conn = sqlite3.connect('event.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    print("Tum Kullanicilar:")
    for user in users:
        print(f"ID: {user[0]}, Kullanıcı Adı: {user[1]}, E-posta: {user[3]}, Ad: {user[5]}, Soyad: {user[6]}, Cinsiyet: {user[8]}, Telefon: {user[9]}")

    conn.close()

print_all_users()


if __name__ == '__main__':
    app.run(debug=True)
