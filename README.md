# Homework 2
## Description
   This project is a web application built with Python and Flask, providing users with authentication functionality and a personalized profile page. The application allows users to create accounts, authenticate, update profile information, change passwords, and manage profile pictures. The backend uses MongoDB for storing user credentials, and password hashing is implemented for security.
  
 ## Getting Started
### Dependencies
- VScode, pycharm
- Python 3.9
- MongoDB Compass 1.45.2
### Executing program
```python
python app.py
```
Dataset
 open mongo service
```
brew services start mongodb-community@8.0
```
 close mongo service
```
brew services stop mongodb-community@8.0
```

Input address
```
http://127:0.0.1:5000
```

## Introduction
- Authentication Form: The application renders an authentication form at http://localhost:5000/ where users can log in.
- Account Creation: Users can create new accounts. Upon successful account creation, users are redirected to their profile page, which displays their personal data.
- Password Hashing: Passwords are securely hashed using appropriate hashing algorithms before being stored in the database.
- Login Redirect: If a user is successfully authenticated, they are redirected to their profile page at [http://localhost:5000/profile](http://localhost:5000/profile).
- Profile Page: The profile page is accessible only to authenticated users and is dynamically generated based on their account data stored in MongoDB.
- Profile Information: Users can view and update their profile information, such as their name, bio, and other personal details.
- Profile Picture: New users are assigned a default profile picture (images/profile.jpg).
Users can update their profile picture through the application.
- Password Management
Password Change: Users can change their password via a dedicated page after logging in.
- Logout: A logout feature is implemented, allowing users to end their session securely.
- Notifications
User Notifications: Active users will receive a notification when a new account is created, providing them with timely updates within the system.

