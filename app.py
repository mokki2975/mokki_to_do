from todo_app_package import create_app, init_db_command

app = create_app()

app.cli.add_command(init_db_command)