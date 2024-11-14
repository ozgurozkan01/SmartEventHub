class Event:
    def __init__(self,
                 event_name,
                 description,
                 start_date,
                 finish_date,
                 start_time,
                 finish_time,
                 duration,
                 city,
                 address,
                 category,
                 creator,
                 image_path,
                 event_id=None):
        self.event_id = event_id
        self.event_name = event_name
        self.description = description
        self.start_date = start_date
        self.finish_date = finish_date
        self.start_time = start_time
        self.finish_time = finish_time
        self.duration = duration
        self.city = city
        self.address = address
        self.category = category
        self.creator = creator
        self.image_path = image_path