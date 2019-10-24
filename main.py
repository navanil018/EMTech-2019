from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO
import GtransWrapper as GTW
import os
import base64
import realtime_demo
import time
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
socketio = SocketIO(app)
clientsSSImap = {}
ClientLanguageMap = {}
reverseclientsSSImap = {}
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
english_bot = ChatBot("Chatterbot", storage_adapter="chatterbot.storage.SQLStorageAdapter")
trainer = ChatterBotCorpusTrainer(english_bot)
trainer.train("chatterbot.corpus.english.conversations")

if app.debug is True:   
    import logging
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler('python.log', maxBytes=1024 * 1024 * 100, backupCount=20)
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)


@app.route('/')
def sessions():
    return render_template('logonpage.html')

@app.route('/errorpage')
def errorpae():
    return render_template('errorpage.html')

@app.route('/ChatApp/<UUID>')
def testHarveyUI(UUID):
    s= "OpenChat: Hi "+UUID+"!! What are you thinking about? try this app. Talk in your native language."
    s=GTW.tanslatedata(s, ClientLanguageMap[UUID])
    y = ""
    for k,v in ClientLanguageMap.items():
      y += k + "-" + v + "|"
    return render_template('ChatApp.html', name=UUID, valva=y[:-1], opener=s)


def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')

@socketio.on('removeme_flask')
def remove_ClientMapping(json, methods=['GET', 'POST']):
    username_toremove = ""
    username_toremove = reverseclientsSSImap[request.sid]
    del clientsSSImap[username_toremove]
    del ClientLanguageMap[username_toremove]
    print(username_toremove + " is diconnected.")
    socketio.emit('removeme', json, callback=messageReceived)
    
@socketio.on('ChatProcessing')
def handle_my_chat_event(json, methods=['GET', 'POST']):
    print('received my event: ' + str(json))
    clientsSSImap[str(json['user_name'])] = request.sid
    reverseclientsSSImap[request.sid] = str(json['user_name'])
    if ("@autobot" in json['message']):
        json['message'] = GTW.tanslatedata(json['message'], ClientLanguageMap[json['user_name']])
        print("response from Gtrans -> " + str(json['message']))
        socketio.emit('my response', json,room=request.sid, callback=messageReceived)
        time.sleep(1)
        json['message'] = GTW.tanslatedata(str(english_bot.get_response(json['message'][6:])), ClientLanguageMap[json['user_name']])
        json['user_name'] = 'Autobot'
        socketio.emit('my response', json,room=request.sid, callback=messageReceived)
    else:
        for key, value in clientsSSImap.items():
            json['message'] = GTW.tanslatedata(json['message'], ClientLanguageMap[key])
            print("response from Gtrans -> " + str(json['message']))
            socketio.emit('my response', json,room=value, callback=messageReceived)

@socketio.on('client_language_mapping')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    #print('received my event: ' + str(json))
    age = 0
    target = os.path.join(APP_ROOT, 'static/images')
    destination = "/".join([target, str(json['user_name']) + ".png"])
    s = bytes((json['user_img'])[23:], 'utf-8')
    with open(destination, "wb") as fh:
        fh.write(base64.decodebytes(s))
    fcv = realtime_demo.FaceCV(depth=16, width=8)
    fcvout = fcv.detect_face(destination)
    time.sleep(5)
    if fcvout: 
        age = int(fcvout.split(',')[0])
        gender = fcvout.split(',')[1]
    
    if age > 20:
        clientsSSImap[str(json['user_name'])] = request.sid
        reverseclientsSSImap[request.sid] = str(json['user_name'])
        ClientLanguageMap[str(json['user_name'])] = str(json['language'])
    else:
        json['user_name'] = '123'
    socketio.emit('validity', json, callback=messageReceived)
    print(str(json['user_name']) + " mapped to " + str(json['language']))
    socketio.emit('addme', json, callback=messageReceived)

@socketio.on('Client_Session_Mapper')
def ClientSessionMappper(json, methods=['GET', 'POST']):
    clientsSSImap[str(json['user_name'])] = request.sid
    reverseclientsSSImap[request.sid] = str(json['user_name'])
    ClientLanguageMap[str(json['user_name'])] = str(json['language'])
    #socketio.emit('addme', json, callback=messageReceived)
    
@app.errorhandler(500)
def internal_error(exception):
    app.logger.error(exception)

    
if __name__ == '__main__':
    socketio.run(app,host='0.0.0.0', debug=True)

