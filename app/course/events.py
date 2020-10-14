'''
from app import socketio

def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')

@socketio.on('my event', namespace='/')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('received my event: ' + str(json))
    socketio.emit('my response', json, callback=messageReceived)
'''