from flask import Flask, session
import os
from .extensions import db, login_manager
from werkzeug.security import generate_password_hash
import click
from .models import User

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, '..', 'database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = 'akichan2975'

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    from .auth import auth_bp
    from .tasks import tasks_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)

    @app.cli.command("init-db")
    def init_db_command():
        with app.app_context():
            database_path = db.engine.url.database
            if os.path.exists(database_path):
                try:
                    os.remove(database_path)
                    print(f"既存のデータベースファイル '{database_path}' を削除しました。")
                except PermissionError:
                    click.echo(f"エラー: データベースファイル '{database_path}' が別のプロセスによって使用中のため削除できませんでした。")
                    click.echo("Flaskサーバーやデータベースブラウザなど、データベースファイルを使用している可能性のあるすべてのアプリケーションを閉じてから、再度 'flask init-db' を実行してください。")
                    return

            db.create_all()
            print("データベーステーブルの作成が完了しました。")

            from .models import User, Task
            if User.query.count() == 0:
                print("初期ユーザーを挿入します。")
                test_user = User(username='testuser', password=generate_password_hash('password'))
                db.session.add(test_user)
                db.session.commit()
                print(f"ユーザー '{test_user.username}' を作成しました。")

                test_task1 = Task(user_id=test_user.id, task='Flask-SQLAlchemyを学ぶ', done=False)
                test_task2 = Task(user_id=test_user.id, task='To-Doアプリを完成させる', done=True)
                db.session.add_all([test_task1, test_task2])
                db.session.commit()
                print("初期タスクを挿入しました。")
        click.echo("データベースの初期化が完了しました。")

    return app

if __name__ == '__main__':
    app = create_app()
    print('開発サーバーを起動します')
    app.run(debug=True, host='127.0.0.1', port=5000)