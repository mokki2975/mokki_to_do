import os

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://todo_user:todo_password@db:5432/todo_db')
SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False

SECRET_KEY = os.environ.get('SECRET_KEY', 'akichan2975')