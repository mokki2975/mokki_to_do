from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)  #Flaskアプリのインスタンス
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  #///:相対パス ////:絶対パス
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #追跡機能の無効化

db = SQLAlchemy(app)  #ここまでが設定と初期化

app.secret_key = 'akichan_mokki_19710910'

DATABASE = 'database.db'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    #taskへのリレーションシップ定義(１人のユーザーが複数のタスクを持つ)
    #backref='user':ユーザーがタスク参照可
    #lazy=True:実際ののアクセス時にロード
    # 'Task.user' はTaskモデルの'user'プロパティを参照
    # cascade='all, delete-orphan' は、ユーザーが削除されたときにそのユーザーのタスクも削除されるようにします
    tasks = db.relationship('Task', backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username} >'  #可読性向上

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  #外部キー
    task = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False, nullable=False)  #Boolean(True, False)

    def __repr__(self):
        return f'<Task {self.task} (Done: {self.done})>'
#ここまでがデータベースモデルの定義

def init_db():
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
        print(f"既存のデータベースファイル '{DATABASE}' を削除しました。")

    db.create_all()
    print("データベーステーブルの作成が完了しました。")

    if User.query.count() == 0:
        print("初期ユーザーを挿入します。")
        test_user = User(username = 'testuser', password=generate_password_hash('password'))
        db.session.add(test_user)
        db.session.commit()
        print(f"ユーザー '{test_user.username}'を作成しました")
        test_task1 = Task(user_id=test_user.id, task='Flask-SQLAlchemyを学ぶ', done=False)
        test_task2 = Task(user_id=test_user.id, task='To-Doアプリを完成させる', done=True)
        db.session.add_all([test_task1, test_task2])
        db.session.commit()
        print("初期タスクを挿入しました。")

with app.app_context():
    init_db()

@app.route('/register', methods=['GET', 'POST'])
def register():
    username = "" 
    if request.method == 'POST':
        username = request.form.get('username', '') 
        password = request.form.get('password', '')

        if not username or not password:
            flash('ユーザー名とパスワードを両方入力してください。', 'error')
            return render_template('register.html', username=username) 

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('そのユーザー名は既に使われています。別のユーザー名を選んでください。', 'error')
            return render_template('register.html', username=username)
        
        try:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('登録が完了しました！ログインしてください。', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'登録中にエラーが発生しました: {e}', 'error')
            print(f"エラー: {e}")
            db.session.rollback()
            return render_template('register.html', username=username) 
        
    return render_template('register.html', username=username) 

@app.route('/login', methods=['GET', 'POST'])  #ログイン
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('ログインしました！', 'success')
            return redirect(url_for('index'))
        else:
            flash('ユーザー名またはパスワードが間違っています。', 'error')
    return render_template('login.html')

@app.route('/logout')  #ログアウト
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('ログアウトしました。', 'success')
    return redirect(url_for('index'))

@app.route('/')
def index():
    user_id = session.get('user_id')
    tasks = []
    
    # ★修正点: status_filter と sort_by をifブロックの外で初期化する
    status_filter = request.args.get('status', 'all')
    sort_by = request.args.get('sort', 'newest')

    if user_id: # ユーザーがログインしている場合のみタスクを取得
        query = Task.query.filter_by(user_id=user_id)
        
        # フィルタリング条件の追加
        if status_filter == 'done':
            query = query.filter_by(done=True)
        elif status_filter == 'active':
           query = query.filter_by(done=False)

        # 並べ替え条件の追加
        if sort_by == 'newest':
            query = query.order_by(Task.id.desc())
        elif sort_by == 'oldest':
            query = query.order_by(Task.id.asc())
        elif sort_by == 'alphabetical':
            query = query.order_by(Task.task.asc())
        
        tasks = query.all()

    return render_template('index.html', tasks=tasks, 
                           current_status=status_filter, current_sort=sort_by)

@app.route('/add', methods=['POST'])   #タスク追加
def add_task():
    user_id = session.get('user_id')
    if not user_id:
        flash('タスクを追加するにはログインしてください。', 'error')
        return redirect(url_for('login'))
    
    task_content = request.form.get('task_content')
    if not task_content:
        flash('タスクの内容を入力してください！', 'error')
        return redirect(url_for('index'))

    try:
        new_task = Task(user_id=user_id, task=task_content, done=False)
        db.session.add(new_task)
        db.session.commit()
        flash('タスクを追加しました！', 'success')
    except Exception as e:
        flash(f'タスクの追加中にエラーが発生しました:{e}', 'error')
        print(f"エラー: {e}")
        db.session.rollback()
    return redirect(url_for('index'))

@app.route('/toggle/<int:task_id>')   #タスク完了、未完了切り替え
def toggle_task(task_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('タスクの状態を更新するにはログインしてください。', 'error')
        return redirect(url_for('login'))
    
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()

    if task:
        #状態反転
        task.done = not task.done
        db.session.commit()
        flash('タスクの状態を更新しました！', 'success')
    else:
        flash('指定されたタスクが見つからないか、操作権限がありません。', 'error')
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>')   #タスク削除
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
    except Exception as e:
        flash(f'タスクの削除中にエラーが発生しました: {e}', 'error')
        print(f"エラー: {e}")
        db.session.rollback()
    return redirect(url_for('index'))

@app.route('/edit/<int:task_id>', methods = ['GET', 'POST'])
def edit_task(task_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('タスクを編集するにはログインしてください。', 'error')
        return redirect(url_for('login'))
    
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()

    if task is None:
        flash('指定されたタスクが見つからないか、操作権限がありません。', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':  #フォームからデータを取得し、データベース更新
        updated_task_content = request.form.get('task_content')
        if not updated_task_content:
            flash('タスクの内容を入力してください！', 'error')
            return render_template('edit.html', task = task)  #タスクidは渡す
        
        try:
            task.task = updated_task_content
            db.session.commit()
            flash('タスクを更新しました！', 'success')
        except Exception as e:
            flash(f'タスクの更新中にエラーが発生しました: {e}', 'error')
            print(f"エラー: {e}")
            db.session.rollback()
        return redirect(url_for('index'))
    else:
        return render_template('edit.html', task = task)  #GETリクエストなら編集フォームを表示

if __name__ == '__main__':
    print("開発サーバーを起動します")
    app.run(debug = True, host='127.0.0.1', port=5000)