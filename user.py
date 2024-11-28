class User:
    def __init__(self, username=None, password=None, email=None, location=None, interests=None, first_name=None,
                 last_name=None, birth_date=None, gender=None, phone_number=None, profile_photo=None, status="user"):
        self.username = username
        self.password = password
        self.email = email
        self.location = location
        self.interests = interests
        self.first_name = first_name
        self.last_name = last_name
        self.birth_date = birth_date
        self.gender = gender
        self.phone_number = phone_number
        self.profile_photo = profile_photo
        self.status = status

