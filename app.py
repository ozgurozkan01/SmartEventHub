import os
import sys

from flask import Flask, render_template, request, redirect, flash, url_for, jsonify, session
from database import *
from utilities import *
from flask_mail import Mail, Message

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
            'status':user_instance.status
        }

        if user_instance.status == 'admin':
            return redirect(url_for('admin_profile'))
        else:
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
    suggested_events = [event for event in suggested_events if event['creator_username'] != username]

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

        user_id = get_user_id_by_username(creator_username)
        user_events = [dict(row) for row in get_created_events_by_username(creator_username)]
        attended_events = get_user_attended_events(user_id) if user_id else []

        all_user_events = {event['ID']: event for event in user_events + attended_events}.values()
        all_user_events = list(all_user_events)

        conflict_message = None
        for e in all_user_events:
            if is_time_conflicting(
                    start_date, start_time, finish_date, finish_time,
                    e['startDate'], e['startTime'], e['finishDate'], e['finishTime']
            ):
                conflict_message = "Bu etkinlik, başka bir etkinlik ile çakışıyor. Etkinlik oluşturulamaz."
                break

        if conflict_message:
            return render_template('createEvent.html', conflict_message=conflict_message)

        insert_event(event_name, description, start_date, finish_date, start_time, finish_time, duration, city, address, category, creator_username)

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

@app.route('/admin-profile')
def admin_profile():
    admin = {
            "first_name": session['user']['first_name'],
            "last_name": session['user']['last_name'],
            "email": session['user']['email'],
            "username": session['user']['username'],
            "password": "******",
            "location": session['user']['location'],
            "interests": session['user']['interests'],
            "birth_date": session['user']['birthday'],
            "gender": session['user']['gender'],
            "phone_number": session['user']['phone_number'],
            "profile_photo": session['user']['profile_photo'],
    }

    return render_template('adminProfile.html', admin_info=admin)

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
        attended_events = get_user_attended_events(get_user_id_by_username(username))

        user_score = get_user_score(get_user_id_by_username(username))

        return render_template('userProfile.html', user=user_data, interests=interests_list, user_events=user_events, attended_events = attended_events, score=user_score)
    else:
        flash('Lütfen önce giriş yapın!')
        return redirect(url_for('login_form'))


@app.route('/event/<int:event_id>')
def event_detail(event_id):
    event = get_event_by_id(event_id)
    if not event:
        return "Etkinlik bulunamadı", 404

    username = session.get('user', {}).get('username')
    user_id = get_user_id_by_username(username) if username else None

    is_participant = False
    is_creator = False
    if user_id:
        is_participant = is_user_participant(user_id, event_id)
        is_creator = username == get_event_creator_username(event_id)

    user_events = [dict(row) for row in get_created_events_by_username(username)]
    attended_events = get_user_attended_events(user_id) if user_id else []

    all_user_events = {event['ID']: event for event in user_events + attended_events}.values()
    all_user_events = list(all_user_events)

    conflict_message = None
    for e in all_user_events:
        if is_time_conflicting(
                event['startDate'], event['startTime'], event['finishDate'], event['finishTime'],
                e['startDate'], e['startTime'], e['finishDate'], e['finishTime']
        ):
            conflict_message = "Bu etkinlik, diğer bir etkinlik ile çakışıyor."
            break

    days, hours, minutes = calculate_duration(event['startDate'], event['startTime'], event['finishDate'],
                                              event['finishTime'])

    messages = get_messages_for_event(event_id)
    is_user_admin = is_admin(user_id)

    return render_template(
        'eventDetails.html',
        event=event,
        username=username,
        user_id= user_id,
        is_participant=is_participant,
        is_creator=is_creator,
        messages=messages,
        get_username_by_id=get_username_by_id,
        days=days, hours=hours, minutes=minutes,
        conflict_message=conflict_message,
        is_user_admin = is_user_admin
    )

def send_notification(user_id, message):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Notifications (user_id, message, is_read, created_at) 
        VALUES (?, ?, 0, ?)
    ''', (user_id, message, datetime.now()))
    conn.commit()
    conn.close()

@app.route('/send_message/<int:event_id>', methods=['POST'])
def send_message(event_id):
    data = request.json
    content = data.get('content')
    username = session.get('user', {}).get('username')

    if not content or not username:
        return jsonify({"error": "Eksik bilgi"}), 400

    sender_id = get_user_id_by_username(username)
    if not sender_id:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 404

    creator_username = get_event_creator_username(event_id)
    if username != creator_username and not is_user_participant(sender_id, event_id):
        return jsonify({"error": "Etkinlik katılımı ya da sahiplik gereklidir"}), 403

    insert_message(sender_id, event_id, 0, content)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return jsonify({
        "success": True,
        "timestamp": timestamp,
        "user_name": username,
        "content": content,
        "sender_id": sender_id
    }), 200

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
            "sent_time": row[2],
            "sender_id": row[0],
            "message_text": row[1],
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
        event_name = request.form['event-name']
        description = request.form['event-description']
        start_date = request.form['event-start-date']
        finish_date = request.form['event-finish-date']
        start_time = request.form['event-start-time']
        finish_time = request.form['event-finish-time']
        city = request.form['location']
        address = request.form['event-address']
        category = request.form.get('category')

        start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
        finish_datetime = datetime.strptime(f"{finish_date} {finish_time}", "%Y-%m-%d %H:%M")

        duration = finish_datetime - start_datetime

        duration_in_seconds = duration.total_seconds()

        data = {
            'event-name': event_name,
            'event-description': description,
            'event-start-date': start_date,
            'event-finish-date': finish_date,
            'event-start-time': start_time,
            'event-finish-time': finish_time,
            'event-city': city,
            'event-address': address,
            'category': category,
            'duration': duration_in_seconds,
        }

        update_event_in_db(event_id, data)

        user_id = get_user_id_by_username(session.get('user').get('username'))

        if is_admin(user_id):
            return redirect(url_for('view_event', event_id=event_id))
        else:
            return redirect(url_for('event_detail', event_id=event_id))

@app.route('/join_event/<int:event_id>', methods=['POST'])
def join_event(event_id):
    if 'user' not in session:
        flash("Etkinliğe katılmak için giriş yapmalısınız.", "warning")
        return redirect(url_for('login_form'))

    user_id = get_user_id_by_username(session['user']['username'])

    join_event_for_user(user_id, event_id)

    return redirect(url_for('event_detail', event_id=event_id))

@app.route('/leave_event/<event_id>', methods=['POST'])
def leave_event(event_id):
    if 'user' not in session:
        flash("Etkinliğe katılmak için giriş yapmalısınız.", "warning")
        return redirect(url_for('login_form'))

    user_id = get_user_id_by_username(session['user']['username'])

    leave_event_for_user(user_id, event_id)
    return redirect(url_for('event_detail', event_id=event_id))

@app.route('/delete_event/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    delete_event_from_db(event_id)
    flash("Etkinlik başarıyla silindi.", "success")
    return redirect(url_for('main_page'))  # Redirect to the events list or home page

@app.route('/approve_event/<int:event_id>', methods=['POST'])
def approve_event(event_id):
    update_event_approval(event_id, 1)
    return redirect(url_for('view_event', event_id=event_id))

@app.route('/disapprove_event/<int:event_id>', methods=['POST'])
def disapprove_event(event_id):
    update_event_approval(event_id, 0)
    return redirect(url_for('view_event', event_id=event_id))

@app.route('/edit_event/<int:event_id>')
def edit_event(event_id):
    event = get_event_by_id(event_id)
    return render_template('editEvent.html', event=event)

@app.route('/notifications')
def notifications():
    username = session.get('user', {}).get('username')
    user_id = get_user_id_by_username(username)
    notifications = get_user_notifications(user_id)

    return render_template('notifications.html', notifications=notifications)

@app.route('/get-notifications', methods=['GET'])
def get_notifications():
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"status": "error", "message": "Kullanıcı oturumda değil"}), 401

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT message, created_at 
        FROM Notifications 
        WHERE user_id = ? AND is_read = 0 
        ORDER BY created_at DESC
    ''', (user_id,))
    notifications = cursor.fetchall()
    conn.close()

    return jsonify([{"message": row[0], "date": row[1]} for row in notifications])

@app.route('/admin/user/')
def view_user():
    users = get_all_users()
    return render_template('view_users.html',
                           users=users,
                           get_created_events_by_username=get_created_events_by_username, # function
                           get_user_attended_events=get_user_attended_events) # function

@app.route('/admin/event/<int:event_id>')
def view_event(event_id):
    events = get_all_events()
    return render_template('view_events.html', events=events, is_user_admin=is_admin, event_id=event_id)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    delete_user_from_database(user_id)
    return redirect(url_for('view_user'))

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/authorize/<int:user_id>', methods=['POST'])
def authorize(user_id):
    user = get_user_by_id(user_id)

    if not user:
        flash('Kullanıcı bulunamadı', 'danger')
        return redirect(url_for('view_user'))

    if user['status'] == 'user':
        try:
            update_user_status(user_id, 'admin')

            flash(f'{user["name"]} başarıyla admin yapıldı!', 'success')
        except Exception as e:
            flash(f'Hata: {str(e)}', 'danger')
    else:
        flash(f'{user["name"]} zaten admin.', 'warning')

    return redirect(url_for('view_user'))


@app.route('/revoke_authorization/<int:user_id>', methods=['POST'])
def revoke_authorization(user_id):
    user = get_user_by_id(user_id)

    if not user:
        flash('Kullanıcı bulunamadı', 'danger')
        return redirect(url_for('view_user'))

    if user['status'] == 'admin':
        try:
            update_user_status(user_id, 'user')

            flash(f'{user["name"]} başarıyla admin statüsünden çıkarıldı.', 'success')
        except Exception as e:
            flash(f'Hata: {str(e)}', 'danger')
    else:
        flash(f'{user["name"]} zaten user.', 'warning')

    return redirect(url_for('view_user'))

@app.route('/send_password', methods=['POST'])
def send_password():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    print('1')

    if not username or not email:
        return jsonify({'message': 'Kullanıcı adı ve e-posta gereklidir.'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT password FROM users WHERE username = ? AND email = ?", (username, email))
    result = cursor.fetchone()
    print(f"Veritabanı sorgu sonucu: {result}")
    conn.close()

    if result:
        print('2')
        user_password = result[0]
        if not isinstance(user_password, str):
            return jsonify({'message': 'Şifre hatalı formatta.'}), 400

        mail_username = get_email_by_username(username)
        mail_password = get_user_password(username)

        print(f"Mail username: {mail_username}, Mail password: {mail_password}")

        if not isinstance(mail_username, str) or not isinstance(mail_password, str):
            return jsonify({'message': 'E-posta veya şifre hatalı.'}), 400

        mail_password = mail_password[0]
        print(f"Mail password: {mail_password}")

        app.config['MAIL_SERVER'] = 'smtp.gmail.com'
        app.config['MAIL_PORT'] = 587
        app.config['MAIL_USE_TLS'] = True
        app.config['MAIL_USERNAME'] = mail_username
        app.config['MAIL_PASSWORD'] = mail_password
        mail = Mail(app)

        print('4 - Mail gönderme başlıyor...')

        try:
            print(f"Mail gönderilecek adres: {email}")
            mail.connect()
            print('SMTP Bağlantısı başarılı')

            msg = Message("Şifre Bilgileriniz",
                          sender=app.config['MAIL_USERNAME'],
                          recipients=[email])
            msg.body = f"Merhaba {username},\n\nŞifreniz: {user_password}\n\nİyi günler!"
            if not isinstance(msg.body, str):
                return jsonify({'message': 'E-posta içeriği hatalı formatta.'}), 400

            print('5 - E-posta gönderiliyor...')
            mail.send(msg)
            print('E-posta başarıyla gönderildi.')
            return jsonify({'message': 'E-posta başarıyla gönderildi.'}), 200
        except Exception as e:
            print(f"Hata oluştu: {e}")
            return jsonify({'message': f'E-posta gönderimi sırasında bir hata oluştu: {str(e)}'}), 500
    else:
        print("Kullanıcı adı veya e-posta eşleşmedi.")
        return jsonify({'message': 'Kullanıcı adı veya e-posta eşleşmedi.'}), 404


if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    app.run(debug=True)