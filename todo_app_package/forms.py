from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from .models import User

class RegistrationForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('パスワード', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('パスワード（確認用）', validators=[DataRequired(), EqualTo('password', message='パスワードが一致しません。')])
    submit = SubmitField('登録する')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('そのユーザー名は既に使われています。別のユーザー名を選んでください。')
        
class LoginForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    remember_me = BooleanField('ログイン情報を記憶する')
    submit = SubmitField('ログインする')

class TaskForm(FlaskForm):
    task_content = StringField('新しいタスクを入力', validators=[DataRequired(), Length(min=1)])
    submit = SubmitField('追加')

class EditTaskForm(FlaskForm):
    task_content = StringField('タスク内容', validators=[DataRequired(), Length(min=1)])
    submit = SubmitField('更新')