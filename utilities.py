import requests
from datetime import datetime

def get_coordinates_from_city(city_name):
    api_key = 'AIzaSyCA_4LDp0ENu2nDB07pz8OVohdAfBomx5A'
    url = f'https://maps.googleapis.com/maps/api/geocode/json?address={city_name}&key={api_key}'
    response = requests.get(url)
    data = response.json()

    if data['status'] == 'OK':
        lat = data['results'][0]['geometry']['location']['lat']
        lng = data['results'][0]['geometry']['location']['lng']
        return lat, lng
    else:
        return None, None

def calculate_duration(start_date, start_time, finish_date, finish_time):
    start_datetime_str = f"{start_date} {start_time}"
    finish_datetime_str = f"{finish_date} {finish_time}"

    start_datetime = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")
    finish_datetime = datetime.strptime(finish_datetime_str, "%Y-%m-%d %H:%M")

    duration = finish_datetime - start_datetime

    days = duration.days
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    return days, hours, minutes


def is_time_conflicting(start_date, start_time, end_date, end_time, other_start_date, other_start_time, other_end_date,
                        other_end_time):
    event_start = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
    event_end = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")

    other_event_start = datetime.strptime(f"{other_start_date} {other_start_time}", "%Y-%m-%d %H:%M")
    other_event_end = datetime.strptime(f"{other_end_date} {other_end_time}", "%Y-%m-%d %H:%M")

    if event_start < other_event_end and event_end > other_event_start:
        return True
    return False


api_key = 'AIzaSyCA_4LDp0ENu2nDB07pz8OVohdAfBomx5A'

def get_coordinates_from_city(city_name):
    url = f'https://maps.googleapis.com/maps/api/geocode/json?address={city_name}&key={api_key}'
    response = requests.get(url)
    data = response.json()

    if data['status'] == 'OK':
        lat = data['results'][0]['geometry']['location']['lat']
        lng = data['results'][0]['geometry']['location']['lng']
        return lat, lng
    else:
        return None, None

def get_distance_matrix(orig_coords, dest_coords):
    url = f'https://maps.googleapis.com/maps/api/distancematrix/json?origins={orig_coords[0]},{orig_coords[1]}&destinations={dest_coords[0]},{dest_coords[1]}&key={api_key}'
    response = requests.get(url)
    data = response.json()

    if data['status'] == 'OK' and 'rows' in data and len(data['rows']) > 0:
        row = data['rows'][0]
        if 'elements' in row and len(row['elements']) > 0:
            element = row['elements'][0]
            if 'distance' in element:
                return element['distance']['value']
            else:
                print("Mesafe bilgisi mevcut değil.")
                return None
        else:
            print("Elements verisi mevcut değil.")
            return None
    else:
        print("API yanıtı geçerli değil veya herhangi bir satır bulunamadı.")
        return None
