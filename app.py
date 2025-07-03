from flask import Flask, render_template, request, redirect, url_for, g, flash
import sqlite3
import os

app = Flask(__name__)  #Flaskアプリのインスタンス
app.secret_key = 'mokki2975'

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

def  init_db():   #データベーステーブル作成
    db = get_db()
    #tasks:テーブルがなければ作成
    #id   :主キー,自動で連番が振られる
    #task :タスクの内容
    #done :タスクが完了したかどうか（0=未完了、1=完了）
    db.execute("""
        CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0 
        )
    """)
    db.commit()
    print("データベーステーブルの確認/作成が完了しました。")

with app.app_context():  #アプリケーション起動時に、データベーステーブル初期化
    init_db()

@app.route( '/' )  #to-doリストの表示
def index():
    db = get_db()
    #タスクの並び替え/フィルタリング機能
    status_filter = request.args.get('status', 'all') #'all', 'done', 'active'
    sort_by = request.args.get('sort', 'newest')  #'newest', 'oldest', 'alphabetical'

    query = 'SELECT id, task, done FROM tasks'
    params = []

    if status_filter == 'done':
        query += ' WHERE done = ?'
        params.append(1)
    elif status_filter == 'active':
        query += ' WHERE done = ?'
        params.append(0)

    if sort_by == 'newest':
        query += ' ORDER BY id DESC'
    elif sort_by == 'oldest':
        query += ' ORDER BY id ASC'
    elif sort_by == 'alphabetical':
        query += ' ORDER BY task ASC'

    tasks = db.execute(query, params).fetchall()

    return render_template('index.html', tasks = tasks,
                           current_status=status_filter, current_sort=sort_by)

@app.route('/add', methods=['POST'])   #タスク追加
def add_task():
    task_content = request.form.get('task_content')
    if not task_content:
        flash('タスクの内容を入力してください！', 'error')
        return redirect(url_for('index'))

    db = get_db()
    try:
        db.execute('INSERT INTO tasks (task) VALUES (?)', (task_content,)) 
        db.commit()
        flash('タスクを追加しました！', 'success')
    except sqlite3.Error as e:
        flash(f'タスクの追加中にエラーが発生しました:{e}', 'error')
        db.rollback()
    return redirect(url_for('index'))

@app.route('/toggle/<int:task_id>')   #タスク完了、未完了切り替え
def toggle_task(task_id):
    db = get_db()
    #現在のタスクの状態取得
    task_row = db.execute('SELECT done FROM tasks WHERE id = ?', (task_id,)).fetchone()

    if task_row:
        #状態反転
        new_done_status = 1 if task_row['done'] ==0 else 0
        db.execute('UPDATE tasks SET done = ? WHERE id = ?', (new_done_status, task_id))
        db.commit()
        flash('タスクの状態を更新しました！', 'success')
    else:
        flash('指定されたタスクが見つかりません。', 'error')
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>')   #タスク削除
def delete_task(task_id):
    db = get_db()
    try:
        db.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        db.commit()
        flash('タスクを削除しました！', 'success')
    except sqlite3.Error as e:
        flash(f'タスクの削除中にエラーが発生しました: {e}', 'error')
        db.rollback()
    return redirect(url_for('index'))

@app.route('/edit/<int:task_id>', methods = ['GET', 'POST'])
def edit_task(task_id):
    db = get_db()
    task = db.execute('SELECT id, task, done FROM tasks WHERE id = ?', (task_id,)).fetchone()

    if task is None:
        flash('指定されたタスクが見つかりません。', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':  #フォームからデータを取得し、データベース更新
        updated_task_content = request.form.get('task_content')
        if not updated_task_content:
            flash('タスクの内容を入力してください！', 'error')
            return render_template('edit.html', task = task)  #タスクidは渡す
        
        try:
            db.execute('UPDATE tasks SET task = ? WHERE id = ?', (updated_task_content, task_id))
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
    print("開発サーバを起動します")
    app.run(debug = True, host='127.0.0.1', port=5000)