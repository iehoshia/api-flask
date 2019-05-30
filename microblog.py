#from app import app as application

from app import create_app, db, cli

app = create_app()
cli.register(app)

from app.models import WebUser, User, Post, Message, Notification, Task

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 
    		'Message': Message,
            'Notification': Notification, 
            'tryton': tryton, 
            #'Task': Task
            }