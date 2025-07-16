from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .extensions import db
from .models import Task
from .forms import TaskForm, EditTaskForm

tasks_bp = Blueprint('tasks', __name__, url_prefix='/')

@tasks_bp.route('/')
def index():
    user_id = session.get('user_id')
    tasks = []
    task_form = TaskForm()

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
                           task_form=task_form)

@tasks_bp.route('/add', methods=['POST'])
def add_task():
    user_id = session.get('user_id')
    if not user_id:
        flash('タスクを追加するにはログインしてください。', 'error')
        return redirect(url_for('auth.login'))
    
    task_form = TaskForm()
    if task_form.validate_on_submit():
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

    else:
        for field, errors in task_form.errors.items():
            for error in errors:
                flash(f' {task_form[field].label.text} : {error}', 'error')
    return redirect(url_for('tasks.index'))

@tasks_bp.route('/toggle/<int:task_id>')
def toggle_task(task_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('タスクの状態を更新するにはログインしてください。', 'error')
        return redirect(url_for('auth.login'))
    
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()

    if task:
        task.done = not task.done
        db.session.commit()
        flash('タスクの状態を更新しました！', 'success')
    else:
        flash('指定されたタスクが見つからないか、操作権限がありません。', 'error')
    return redirect(url_for('tasks.index'))

@tasks_bp.route('/delete/<int:task_id>')
def delete_task(task_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('タスクを削除するにはログインしてください。', 'error')
        return redirect(url_for('auth.login'))
    
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
    return redirect(url_for('tasks.index'))

@tasks_bp.route('/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('タスクを編集するにはログインしてください。', 'error')
        return redirect(url_for('auth.login'))
    
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()

    if task is None:
        flash('指定されたタスクが見つからないか、操作権限がありません。', 'error')
        return redirect(url_for('tasks.index'))
    
    form = EditTaskForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            task.task = form.task_content.data
            db.session.commit()
            flash('タスクを更新しました！', 'success')
            return redirect(url_for('tasks.index'))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{form[field].label.text}: {error}', 'error')
            return render_template('edit.html', form=form, task=task)
    else:
        form.task_content.data = task.task
        return render_template('edit.html', form=form, task=task)