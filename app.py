import os

from flask import Flask, render_template, request, redirect, flash, url_for, jsonify, session

from database import *
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
    insert_score(get_user_id_by_username(username), points=0)

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

        insert_event(event_name, description, start_date, finish_date, start_time, finish_time, duration, city, address, category, creator_username)

        user_id = get_user_id_by_username(creator_username)
        update_user_score(user_id, 15)

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

        interests = user_data.get('interests', [])

        if isinstance(interests, list):
            interests_list = interests
        else:
            interests_list = interests.split(', ') if interests else []

        username = user_data.get('username')
        user_events = get_created_events_by_username(username)
        attended_events = get_user_events(get_user_id_by_username(username))
        user_score = get_user_score(get_user_id_by_username(username))

        return render_template('userProfile.html', user=user_data, interests=interests_list, user_events=user_events, attended_events = attended_events, score=user_score)
    else:
        flash('Lütfen önce giriş yapın!')
        return redirect(url_for('login_form'))

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    event = get_event_by_id(event_id)
    username = session.get('user').get('username')
    return render_template('eventDetails.html', event=event, username=username)
@app.route('/send_message/<int:event_id>', methods=['POST'])
def send_message(event_id):
    data = request.json  # Gelen JSON verisi
    message_text = data.get('content')  # Mesaj içeriği
    sender_id = session.get('user', {}).get('id')  # Oturumdaki kullanıcının ID'si
    receiver_id = None  # Örneğin, bu birebir mesajlaşma değilse boş bırakabilirsiniz.

    if not message_text or not sender_id:
        return jsonify({"error": "Eksik bilgi"}), 400

    try:
        insert_message(sender_id, event_id, receiver_id, message_text)

        sent_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({
            "success": True,
            "message": {
                "event_id": event_id,
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "message_text": message_text,
                "sent_time": sent_time
            }
        }), 200
    except Exception as e:
        return jsonify({"error": "Mesaj kaydedilemedi", "details": str(e)}), 500

@app.route('/get_messages/<int:event_id>', methods=['GET'])
def get_messages(event_id):
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

    messages_list = [
        {
            "sender_id": row[0],
            "message_text": row[1],
            "sent_time": row[2]
        }
        for row in messages
    ]

    return jsonify(messages_list), 200

@app.route('/editProfile')
def edit_profile():
    user_data = session.get('user')

    if user_data:
        print(f"User Data: {user_data}")

        interests = user_data.get('interests', '')

        if isinstance(interests, list):
            interests = ', '.join(interests)
        elif not isinstance(interests, str):
            interests = ''

        interests_list = interests.split(', ') if interests else []

        return render_template('editProfile.html', user=user_data, interests=interests_list)

    flash('Lütfen önce giriş yapın!')
    return redirect(url_for('login_form'))


@app.route('/updateProfile', methods=['POST'])
def update_profile():
    username = request.form['username']
    user_instance = get_user_instance(username=username)

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

    updated_data = {
        'username': request.form.get('username', user_instance.username),
        'email': request.form.get('email', user_instance.email),
        'first_name': request.form.get('firstName', user_instance.first_name),
        'last_name': request.form.get('lastName', user_instance.last_name),
        'location': request.form.get('location', user_instance.location),
        'interests': request.form.getlist('interests') or (user_instance.interests.split(', ') if isinstance(user_instance.interests, str) else user_instance.interests),
        'birthday': request.form.get('birthDate', user_instance.birth_date),
        'gender': request.form.get('gender', user_instance.gender),
        'phone': request.form.get('phone', user_instance.phone_number),
    }

    user_id = get_user_id_by_username(session.get('user').get('username'))

    update_user(user_id, updated_data)

    session['user'].update(updated_data)

    return redirect('/profile')

@app.route('/update_event/<int:event_id>', methods=['GET', 'POST'])
def update_event(event_id):
    if request.method == 'POST':
        data = {
            'event-name': request.form['event-name'],
            'event-description': request.form['event-description'],
            'event-start-date': request.form['event-start-date'],
            'event-finish-date': request.form['event-finish-date'],
            'event-start-time': request.form['event-start-time'],
            'event-finish-time': request.form['event-finish-time'],
            'event-address': request.form['event-address'],
            'location': request.form['location'],
            'category': request.form['category'],
            'creator_username': request.form['creator_username'],
            'isApproved': request.form['isApproved']
        }

        update_event_in_db(event_id, data)

        return redirect(url_for('event_detail', event_id=event_id))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE ID = ?", (event_id,))
    event = cursor.fetchone()
    conn.close()

    if not event:
        return "Event not found", 404

    return render_template('eventDetails.html', event=event)
@app.route('/join_event/<int:event_id>', methods=['POST'])
def join_event(event_id):
    if 'user' not in session:
        flash("Etkinliğe katılmak için giriş yapmalısınız.", "warning")
        return redirect(url_for('login_form'))

    user_id = get_user_id_by_username(session['user']['username'])

    join_event_for_user(user_id, event_id)

    return redirect(url_for('event_detail', event_id=event_id))

@app.route('/edit_event/<int:event_id>')
def edit_event(event_id):
    event = get_event_by_id(event_id)
    return render_template('editEvent.html', event=event)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    app.run(debug=True)

