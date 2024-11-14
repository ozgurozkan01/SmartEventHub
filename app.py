import os

from flask import Flask, render_template, request, redirect, flash, url_for, jsonify, session
from werkzeug.utils import secure_filename

from database import *
from event import Event
from datetime import datetime

import sys

sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)
app.secret_key = 'yazlab2'

user_instance = User()

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/forgetPassword')
def forget_password():
    return render_template('forgetPassword.html')

@app.route('/createAccount')
def create_account():
    return render_template('createAccount.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user_instance = get_user_instance(username=username)

    if user_instance and check_password_hash(user_instance.password, password):
        session['user'] = {
            'username': user_instance.username,
            'email': user_instance.email,
            'first_name': user_instance.first_name,
            'last_name': user_instance.last_name,
            'location': user_instance.location,
            'interests': user_instance.interests,
            'birthday': user_instance.birth_date,
            'gender': user_instance.gender,
            'phone_number': user_instance.phone_number,
            'profile_photo': user_instance.profile_photo,
        }

        return redirect(url_for('main_page'))
    else:
        flash('Kullanıcı adı veya şifre yanlış. Lütfen tekrar deneyin.')
        return redirect(url_for('login_form'))

@app.route('/login_form')
def login_form():
    return render_template('login.html')

@app.route('/main_page')
def main_page():
    username = session.get('user').get('username')
    all_events = get_all_approved_events_for_user(username)
    suggested_events = get_suggested_events_for_user(username)
    return render_template('mainPage.html', events=all_events, suggested_events=suggested_events)

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    first_name = request.form['firstName']
    last_name = request.form['lastName']
    birth_date = request.form['birthDate']
    gender = request.form['gender']
    email = request.form['email']
    phone = request.form['phone']
    location = request.form['location']
    interests = request.form.getlist('interests')
    interests_str = ', '.join(interests)

    insert_user(username, password, email, location, interests_str, first_name, last_name, birth_date, gender, phone)

    flash("Kayıt başarılı!", "success")
    return redirect(url_for('login_form'))
@app.route('/resetPassword', methods=['POST'])
def reset_password():
    data = request.get_json()
    old_password = data['oldPassword']
    new_password = data['newPassword']

    username = session.get('user').get('username')

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

    if user is None:
        return jsonify(success=False)

    if check_password_hash(user['password'], old_password):
        new_password_hashed = generate_password_hash(new_password)
        conn.execute('UPDATE users SET password = ? WHERE username = ?', (new_password_hashed, username))
        conn.commit()
        conn.close()
        return jsonify(success=True)
    else:
        conn.close()
        return jsonify(success=False)


@app.route('/event-create', methods=['GET', 'POST'])
def event_create():
    return render_template('createEvent.html')

@app.route('/event/create', methods=['GET', 'POST'])
def create_event():
    if request.method == 'POST':
        event_name = request.form['event-name']
        start_date = request.form['event-start-date']
        finish_date = request.form['event-finish-date']
        start_time = request.form['event-start-time']
        finish_time = request.form['event-finish-time']
        description = request.form['event-description']
        city = request.form['event-city']
        address = request.form['event-address']
        category = request.form.get('category')

        start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
        finish_datetime = datetime.strptime(f"{finish_date} {finish_time}", "%Y-%m-%d %H:%M")
        duration = finish_datetime - start_datetime

        creator_username = session.get('user', {}).get('username')

        image = request.files.get('event-image')

        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join('static/images', filename)
            image.save(image_path)

            image_path = image_path.replace('\\', '/')
        else:
            image_path = None

        insert_event(event_name, description, start_date, finish_date, start_time, finish_time, duration, city, address, category, creator_username, image_path)

        return redirect(url_for('main_page'))

    return render_template('createEvent.html')


app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/updateProfilePicture', methods=['POST'])
def update_profile_picture():
    if 'profile-picture' not in request.files:
        return jsonify({'success': False, 'message': 'Dosya bulunamadı'}), 400

    file = request.files['profile-picture']

    if file.filename == '':
        return jsonify({'success': False, 'message': 'Dosya seçilmedi'}), 400

    if file and allowed_file(file.filename):
        filename = os.path.basename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        file.save(file_path)

        new_profile_picture_url = f"/{app.config['UPLOAD_FOLDER']}/{filename}"

        username = session.get('username')
        update_profile_picture_in_db(username, new_profile_picture_url)

        return jsonify({'success': True, 'newProfilePictureUrl': new_profile_picture_url})

    return jsonify({'success': False, 'message': 'Geçersiz dosya formatı'}), 400

@app.route('/profile')
def profile():
    user_data = session.get('user')

    if user_data:
        print(f"User Data: {user_data}")

        interests = user_data.get('interests', '')
        interests_list = interests.split(', ') if interests else []

        username = user_data.get('username')
        user_events = get_created_events_by_username(username)
        # attended_events = get_attended_events_by_username(username)

        return render_template('userProfile.html', user=user_data, interests=interests_list, user_events=user_events)
    else:
        flash('Lütfen önce giriş yapın!')
        return redirect(url_for('login_form'))

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    event = get_event_by_id(event_id)
    return render_template('eventDetails.html', event=event)

images = get_event_images()
print(images)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    app.run(debug=True)

