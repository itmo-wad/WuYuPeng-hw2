from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import os
from werkzeug.utils import secure_filename
from utils.notification import send_notification
from functools import wraps
import logging
import secrets


app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# MongoDB configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/user_auth"
mongo = PyMongo(app)
try:
    mongo.cx.server_info()  
    logging.info("MongoDB 连接成功")
except Exception as e:
    logging.info("MongoDB 连接失败: {e}")



# File upload configuration
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for('login'))
        # Check if the user still exists in the database
        user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        if not user:
            session.pop('username', None)
            session.pop('user_id', None)
            flash("Your session has expired or your account has been deleted.", "danger")
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function



@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('profile'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = mongo.db.users.find_one({'username': username})

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            session['user_id'] = str(user['_id'])
            return redirect(url_for('profile'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        name = request.form.get('name', 'unknown')
        title = request.form.get('title', '')
        bio = request.form.get('bio', '')
        allowed_skills = {"Python", "Golang", "Machine Learning", "AI security", "AI development"}
        skills = request.form.getlist('skills') or [] # 获取多选值
        skills = [skill for skill in skills if skill in allowed_skills]
        file = request.files.get('profile_image')
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
        else:
            filename = 'profile.jpg'  # 默认头像

        if mongo.db.users.find_one({'username': username}):
            flash('Username already exists')
        else:
            new_user = {
                'username': username,
                'password': password,
                'name': name,
                'title': title,
                'bio': bio,
                'skills': skills,
                'profile_image': filename  
            }
            user_id = mongo.db.users.insert_one(new_user).inserted_id
            
            # 发送通知（传入 mongo 对象）
            send_notification(mongo, f"New user {username} has joined!")

            flash('Registration successful. Please login.')
            return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']

        user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})

        if user and check_password_hash(user['password'], old_password):
            new_hashed_password = generate_password_hash(new_password)
            mongo.db.users.update_one({'_id': ObjectId(session['user_id'])}, {'$set': {'password': new_hashed_password}})
            flash('Password changed successfully.')
            return redirect(url_for('profile'))
        else:
            flash('Old password is incorrect.')

    return render_template('change_password.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('home'))

@app.route('/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        title = request.form['title']
        bio = request.form['bio']
        skills = request.form.getlist('skills')
        file = request.files['profile_image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            mongo.db.users.update_one({'_id': ObjectId(session['user_id'])}, {'$set': {'profile_image': filename}})
        else:
            user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
            filename = user.get('profile_image', 'profile.jpg')

        mongo.db.users.update_one({'_id': ObjectId(session['user_id'])}, {'$set': {'name': name, 'title': title, 'bio': bio, 'skills': skills}})
        flash('Profile updated successfully')
        return redirect(url_for('profile'))
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    return render_template('update_profile.html', user=user)



@app.route('/profile')
@login_required
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # 获取当前用户的用户名
    username = session['username']
    user = mongo.db.users.find_one({'username': username})  
    notifications = list(mongo.db.notifications.find().sort('timestamp', -1))

    # 确保头像为空时使用默认头像
    profile_image = user.get('profile_image', 'profile.jpg')  

    # 用户资料
    profile_data = {
        'name': user.get('name', 'User'),  
        'title': user.get('title', 'Robot'),
        'bio': user.get('bio', ''),  
        'skills': user.get('skills', []), 
        'profile_image': url_for('static', filename=f"images/{profile_image}"),
        'notifications': notifications
    }

    return render_template('profile.html', profile=profile_data)

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

 
    mongo.db.users.delete_one({'_id': ObjectId(user_id)})

 
    session.pop('username', None)
    session.pop('user_id', None)

    flash('Your account has been deleted.')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)