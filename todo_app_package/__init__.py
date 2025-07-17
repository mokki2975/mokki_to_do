from flask import Flask
from .extensions import db, login_manager
from .models import User, Task
from .auth import auth_bp
from .tasks import tasks_bp
import os

def create_app():
    app = Flask(__name__)

    app.config.from_pyfile('settings.py')
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'ログインしてください。'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(tasks_bp)

    return app

import click
from flask.cli import with_appcontext

@click.command('init-db')
@with_appcontext
def init_db_command():
    db.drop_all()
    db.create_all()

    from werkzeug.security import generate_password_hash
    test_user_username = 'testuser'
    test_user_password = 'password'

    if not User.query.filter_by(username=test_user_username).first():
        hashed_password = generate_password_hash(test_user_password)
        new_user = User(username=test_user_username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        click.echo(f'ユーザー "{test_user_username}" を追加しました。')
    else:
        click.echo(f'ユーザー "{test_user_username}" は既に存在します。')
    
    click.echo(f'データベースを初期化しました。')