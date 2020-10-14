#from app import app as application

from app import create_app, db, cli#, socketio

app = create_app()
cli.register(app)

from app.models import WebUser, User, Post, Message, Notification, Task

#if __name__ == '__main__':
#    app.run(host='apixela.net',port=8000)

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post,
    		'Message': Message,
            'Notification': Notification,
            'Tryton': tryton,
            #'Task': Task
            }