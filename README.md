# GeoFace – Smart Attendance System

GeoFace is a smart attendance management system built with **Django** that uses **Geofencing** and **Face Recognition** to verify students before marking attendance.

## Features

* Student registration and authentication
* Staff authentication
* GPS-based geofencing
* Face recognition for identity verification
* Real-time attendance using WebSockets
* Location accuracy validation
* Attendance session management
* Present/Absent tracking
* Student-wise attendance records
* Staff attendance with face and location verification
* Admin dashboard

## How It Works

```text
Student Login
      ↓
Attendance Session
      ↓
Check GPS Location
      ↓
Inside Geofence?
   ↓ Yes     ↓ No
   ↓         Reject
Face Verification
      ↓
Face Matched?
   ↓ Yes     ↓ No
   ↓         Reject
Mark Attendance
```

The student's current latitude and longitude are compared with the attendance session's configured location and radius. The system also rejects inaccurate GPS readings above the configured accuracy threshold.

## Technologies Used

* Python
* Django
* Django Channels
* WebSockets
* PostgreSQL
* Redis
* OpenCV
* `face_recognition`
* HTML
* CSS
* JavaScript

The project uses Django Channels with Redis for real-time communication.

## Geofencing

Each attendance session contains:

* Latitude
* Longitude
* Geofence radius
* Active/inactive status

```text
Campus / Attendance Location
          ●
       /     \
     /         \
   /  Geofence  \
  /               \
 ●-----------------●
```

Students can mark attendance only when their detected location is within the configured geofence.

## Face Recognition

The system captures a face from the student's camera and generates a face encoding using OpenCV and `face_recognition`. The captured encoding is compared with the registered face encoding to verify the student's identity.

## Attendance Record

Each attendance record stores:

* Student
* Attendance session
* Date/time
* Student latitude
* Student longitude
* Location verification status
* Face verification status
* Present/Absent status

## Installation

```bash
git clone <repository-url>
cd geoface

python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### Linux/macOS

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

Create an admin account:

```bash
python manage.py createsuperuser
```

Start the server:

```bash
python manage.py runserver
```

## Attendance Requirements

Students need to:

1. Allow location access.
2. Allow camera access.
3. Be inside the configured geofence.
4. Have sufficient GPS accuracy.
5. Show their face clearly to the camera.
6. Pass face verification.

The attendance interface checks location first and enables camera/attendance functionality only after successful location verification.

## Project Structure

```text
geoface/
│
├── manage.py
├── requirements.txt
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── ...
│
├── accounts/
├── attendance/
├── templates/
├── static/
└── ...
```

## License

This project is developed for educational purposes.
