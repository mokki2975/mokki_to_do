from flask import Flask, render_template, request, redirect, url_for, g, flash, session
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)  #Flaskアプリのインスタンス
app.secret_key = 'akichan19710910'

DATABASE = 'database.db'

def get_db():
    if 'db' not in g:  #gオブジェクトによるdbの作成
        g.db = sqlite3.connect(
            DATABASE,
            detect_types = sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row  #結果を辞書のようにカラム名でアクセス可
    return g.db

@app.teardown_appcontext  #データベースのお片付け
def close_db(e=None):     #リクエスト終了の確認
    db = g.pop('db', None)
    if db is not None:    #空でなければ閉じる
        db.close()

# データベーステーブルを作成する関数
def init_db():
    db = get_db()
    
    # ★修正点1: users テーブルを先に作成する
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    # ★修正点2: tasks テーブルをその後に作成する
    db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    db.commit()
    print("データベーステーブルの確認/作成が完了しました。")

with app.app_context():  #アプリケーション起動時に、データベーステーブル初期化
    init_db()

@app.route('/register', methods=['GET', 'POST'])
def register():
    # ★修正点1: username を初期化する
    username = "" 
    if request.method == 'POST':
        # ★修正点2: request.form.get() にデフォルト値を設定する
        username = request.form.get('username', '') 
        password = request.form.get('password', '')

        if not username or not password:
            flash('ユーザー名とパスワードを両方入力してください。', 'error')
            # ★修正点3: エラー時に username をテンプレートに渡す
            return render_template('register.html', username=username) 

        db = get_db()
        try:
            hashed_password = generate_password_hash(password)
            db.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                       (username, hashed_password))
            db.commit()
            flash('登録が完了しました！ログインしてください。', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('そのユーザー名は既に使われています。別のユーザー名を選んでください。', 'error')
            # ★修正点4: エラー時に username をテンプレートに渡す
            return render_template('register.html', username=username) 
        except sqlite3.Error as e:
            flash(f'登録中にエラーが発生しました: {e}', 'error')
            print(f"データベースエラー: {e}")
            db.rollback()
            # ★修正点5: エラー時に username をテンプレートに渡す
            return render_template('register.html', username=username) 
    # ★修正点6: GETリクエスト時にも username をテンプレートに渡す (最初は空文字列)
    return render_template('register.html', username=username) 

@app.route('/login', methods=['GET', 'POST'])  #ログイン
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
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
        db = get_db()
        
        query = 'SELECT id, task, done FROM tasks WHERE user_id = ?'
        params = [user_id]
        
        # フィルタリング条件の追加
        if status_filter == 'done':
            query += ' AND done = ?'
            params.append(1)
        elif status_filter == 'active':
            query += ' AND done = ?'
            params.append(0)

        # 並べ替え条件の追加
        if sort_by == 'newest':
            query += ' ORDER BY id DESC'
        elif sort_by == 'oldest':
            query += ' ORDER BY id ASC'
        elif sort_by == 'alphabetical':
            query += ' ORDER BY task ASC'
        
        tasks = db.execute(query, params).fetchall()

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

    db = get_db()
    try:
        db.execute('INSERT INTO tasks (user_id, task) VALUES (?, ?)', (user_id, task_content)) 
        db.commit()
        flash('タスクを追加しました！', 'success')
    except sqlite3.Error as e:
        flash(f'タスクの追加中にエラーが発生しました:{e}', 'error')
        db.rollback()
    return redirect(url_for('index'))

@app.route('/toggle/<int:task_id>')   #タスク完了、未完了切り替え
def toggle_task(task_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('タスクの状態を更新するにはログインしてください。', 'error')
        return redirect(url_for('login'))
    
    db = get_db()
    #現在のタスクの状態取得
    task_row = db.execute('SELECT done FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id)).fetchone()

    if task_row:
        #状態反転
        new_done_status = 1 if task_row['done'] ==0 else 0
        db.execute('UPDATE tasks SET done = ? WHERE id = ? AND user_id = ?', (new_done_status, task_id, user_id))
        db.commit()
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
    
    db = get_db()
    try:
        db.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id))
        db.commit()
        flash('タスクを削除しました！', 'success')
    except sqlite3.Error as e:
        flash(f'タスクの削除中にエラーが発生しました: {e}', 'error')
        db.rollback()
    return redirect(url_for('index'))

@app.route('/edit/<int:task_id>', methods = ['GET', 'POST'])
def edit_task(task_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('タスクを編集するにはログインしてください。', 'error')
        return redirect(url_for('login'))
    
    db = get_db()
    task = db.execute('SELECT id, task, done FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id)).fetchone()

    if task is None:
        flash('指定されたタスクが見つからないか、操作権限がありません。', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':  #フォームからデータを取得し、データベース更新
        updated_task_content = request.form.get('task_content')
        if not updated_task_content:
            flash('タスクの内容を入力してください！', 'error')
            return render_template('edit.html', task = task)  #タスクidは渡す
        
        try:
            db.execute('UPDATE tasks SET task = ? WHERE id = ? AND user_id = ?', (updated_task_content, task_id, user_id))
            db.commit()
            flash('タスクを更新しました！', 'success')
        except sqlite3.Error as e:
            flash(f'タスクの更新中にエラーが発生しました: {e}', 'error')
            print(f'データベースエラー: {e}')
            db.rollback()
        return redirect(url_for('index'))
    else:
        return render_template('edit.html', task = task)  #GETリクエストなら編集フォームを表示

if __name__ == '__main__':
    print("開発サーバーを起動します")
    app.run(debug = True, host='127.0.0.1', port=5000)