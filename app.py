from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
# Flask-WTFから必要なものをインポート
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError

# Flaskアプリケーションのインスタンスを作成
app = Flask(__name__)

 # Flask-SQLAlchemy の設定と初期化
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Flask-WTFのためにSECRET_KEYを設定（セッションと同じキーでOK）
app.secret_key = 'your_todo_app_secret_key_for_auth' # ★より長く、複雑なユニークな秘密鍵に変更してください

# ★ここからデータベースモデルの定義（UserとTask）★
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
            return f'<User {self.username}>'

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<Task {self.task} (Done: {self.done})>'
# ★ここまでデータベースモデルの定義 ★


# ★ここからフォームクラスの定義（WTFormsを使用）★

# ユーザー登録フォーム
class RegistrationForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('パスワード', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('パスワード（確認用）', validators=[DataRequired(), EqualTo('password', message='パスワードが一致しません。')])
    submit = SubmitField('登録する')

    # カスタムバリデーター：ユーザー名が既に存在するかチェック
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('そのユーザー名は既に使われています。別のユーザー名を選んでください。')

# ユーザーログインフォーム
class LoginForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    submit = SubmitField('ログインする')

# タスク追加フォーム
class TaskForm(FlaskForm):
    task_content = StringField('新しいタスクを入力', validators=[DataRequired(), Length(min=1)])
    submit = SubmitField('追加')

# タスク編集フォーム
class EditTaskForm(FlaskForm):
    task_content = StringField('タスク内容', validators=[DataRequired(), Length(min=1)])
    submit = SubmitField('更新')

# ★ここまでフォームクラスの定義 ★


# データベーステーブルを作成する関数
    def init_db():
        if os.path.exists(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')):
            os.remove(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
            print(f"既存のデータベースファイル '{app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')}' を削除しました。")
        
        db.create_all()
        print("データベーステーブルの作成が完了しました。")

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
        

    with app.app_context():
        init_db()


    # ユーザー登録のルート
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        form = RegistrationForm() # フォームのインスタンスを作成
        if form.validate_on_submit(): # フォームが送信され、バリデーションが成功した場合
            username = form.username.data
            password = form.password.data
            
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('登録が完了しました！ログインしてください。', 'success')
            return redirect(url_for('login'))
        # GETリクエストまたはバリデーション失敗時
        return render_template('register.html', form=form) 

    # ユーザーログインのルート
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm() # フォームのインスタンスを作成
        if form.validate_on_submit(): # フォームが送信され、バリデーションが成功した場合
            username = form.username.data
            password = form.password.data

            user = User.query.filter_by(username=username).first()

            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['username'] = user.username
                flash('ログインしました！', 'success')
                return redirect(url_for('index'))
            else:
                flash('ユーザー名またはパスワードが間違っています。', 'error')
                # ★修正点: ログイン失敗時に明示的にテンプレートをレンダリングして返す
                return render_template('login.html', form=form) 
        # GETリクエストまたはバリデーション失敗時
        return render_template('login.html', form=form)

    # ユーザーログアウトのルート
    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        session.pop('username', None)
        flash('ログアウトしました。', 'success')
        return redirect(url_for('index'))


    # To-Doリスト表示のルート ('/' にアクセスされたとき)
    @app.route('/')
    def index():
        user_id = session.get('user_id')
        tasks = []
        task_form = TaskForm() # タスク追加フォームのインスタンス
        
        status_filter = request.args.get('status', 'all')
        sort_by = request.args.get('sort', 'newest')

        if user_id:
            query = Task.query.filter_by(user_id=user_id)

            if status_filter == 'done':
                query = query.filter_by(done=True)
            elif status_filter == 'active':
                query = query.filter_by(done=False)

            if sort_by == 'newest':
                query = query.order_by(Task.id.desc())
            elif sort_by == 'oldest':
                query = query.order_by(Task.id.asc())
            elif sort_by == 'alphabetical':
                query = query.order_by(Task.task.asc())
            
            tasks = query.all()

        return render_template('index.html', tasks=tasks, 
                               current_status=status_filter, current_sort=sort_by,
                               task_form=task_form) # フォームをテンプレートに渡す

    # タスク追加のルート ('/add' にアクセスされたとき)
    @app.route('/add', methods=['POST'])
    def add_task():
        user_id = session.get('user_id')
        if not user_id:
            flash('タスクを追加するにはログインしてください。', 'error')
            return redirect(url_for('login'))

        task_form = TaskForm() # フォームのインスタンスを作成
        if task_form.validate_on_submit(): # フォームが送信され、バリデーションが成功した場合
            task_content = task_form.task_content.data
            try:
                new_task = Task(user_id=user_id, task=task_content, done=False)
                db.session.add(new_task)
                db.session.commit()
                flash('タスクを追加しました！', 'success')
            except Exception as e:
                flash(f'タスクの追加中にエラーが発生しました: {e}', 'error')
                print(f"エラー: {e}")
                db.session.rollback()
        else: # バリデーション失敗時
            for field, errors in task_form.errors.items():
                for error in errors:
                    flash(f'{task_form[field].label.text}: {error}', 'error')
        return redirect(url_for('index'))

    # タスク完了/未完了切り替えのルート ('/toggle/<int:task_id>' にアクセスされたとき)
    @app.route('/toggle/<int:task_id>')
    def toggle_task(task_id):
        user_id = session.get('user_id')
        if not user_id:
            flash('タスクの状態を更新するにはログインしてください。', 'error')
            return redirect(url_for('login'))

        task = Task.query.filter_by(id=task_id, user_id=user_id).first()

        if task:
            task.done = not task.done
            db.session.commit()
            flash('タスクの状態を更新しました！', 'success')
        else:
            flash('指定されたタスクが見つからないか、操作権限がありません。', 'error')
        return redirect(url_for('index'))

    # タスク削除のルート ('/delete/<int:task_id>' にアクセスされたとき)
    @app.route('/delete/<int:task_id>')
    def delete_task(task_id):
        user_id = session.get('user_id')
        if not user_id:
            flash('タスクを削除するにはログインしてください。', 'error')
            return redirect(url_for('login'))

        try:
            task = Task.query.filter_by(id=task_id, user_id=user_id).first()
            if task:
                db.session.delete(task)
                db.session.commit()
                flash('タスクを削除しました！', 'success')
            else:
                flash('指定されたタスクが見つからないか、操作権限がありません。', 'error')
        except Exception as e:
            flash(f'タスクの削除中にエラーが発生しました: {e}', 'error')
            print(f"エラー: {e}")
            db.session.rollback()
        return redirect(url_for('index'))

    # タスク編集フォーム表示と更新処理のルート ('/edit/<int:task_id>' にアクセスされたとき)
    @app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
    def edit_task(task_id):
        user_id = session.get('user_id')
        if not user_id:
            flash('タスクを編集するにはログインしてください。', 'error')
            return redirect(url_for('login'))

        task = Task.query.filter_by(id=task_id, user_id=user_id).first()

        if task is None:
            flash('指定されたタスクが見つからないか、操作権限がありません。', 'error')
            return redirect(url_for('index'))

        form = EditTaskForm() # フォームのインスタンスを作成
        if request.method == 'POST':
            if form.validate_on_submit(): # フォームが送信され、バリデーションが成功した場合
                task.task = form.task_content.data
                db.session.commit()
                flash('タスクを更新しました！', 'success')
                return redirect(url_for('index'))
            else: # バリデーション失敗時
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f'{form[field].label.text}: {error}', 'error')
                # バリデーション失敗時は、現在のタスクの内容をフォームに表示し直す
                return render_template('edit.html', form=form, task=task)
        else: # GETリクエストの場合
            form.task_content.data = task.task # 既存のタスク内容をフォームにセット
            return render_template('edit.html', form=form, task=task)


    # このファイルが直接実行された場合に開発サーバーを起動
    if __name__ == '__main__':
        print('開発サーバーを起動します')
        app.run(debug=True, host='127.0.0.1', port=5000)
    