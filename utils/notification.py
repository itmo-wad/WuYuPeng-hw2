from datetime import datetime

def send_notification(mongo, message):
    mongo.db.notifications.insert_one({
        'message': message,
        'timestamp': datetime.utcnow()
    })