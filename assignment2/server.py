from distutils.log import debug
import flask
import uuid
from flask import Flask, redirect, render_template
from flask_socketio import SocketIO, emit, send
from NahelArgama import NahelArgama

app = Flask("Danmaku")
app.config['SECRET_KEY'] = 'secret!'
soc = SocketIO(app, cors_allowed_origins='*')
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)
# app.logger.disabled = True
# log.disabled = True

danmakuHandler = NahelArgama()


@app.route("/")
def mainPage():
    return redirect("/http/rickroll")


@app.route("/http/<video>")
def httpPlayer(video):
    return render_template("danmu.html", videoName=video, mode="http")


@app.route("/ws/<video>")
def wsPlayer(video):
    return render_template("danmu.html", videoName=video, mode="ws")


@app.route("/danmaku")
def loadDanmaku():
    key = uuid.uuid4()
    while key in danmakuHandler.recv_queues:
        key = uuid.uuid4()
    danmakuHandler.register(str(key))
    return {
        "type": "load",
        "danmaku": danmakuHandler.getHistory(),
        "uuid": key
    }


@app.route("/poll/<key>")
def pollDanmaku(key):
    return {"type": "new", "newDanmaku": danmakuHandler.getUnreceived(key)}


@app.route("/send", methods=['POST'])
def sendDanmaku():
    body = flask.request.get_json()
    danmakuHandler.send(body["content"], body["time"])
    return ""


@soc.on('connect')
def wsLoadDanmaku(auth):
    emit("loadDanmaku", {"type": "load",
                         "danmaku": danmakuHandler.getHistory()
                         })

@soc.on('sendDanmaku')
def wsSendDanmaku(body):
    danmakuHandler.send(body["content"], body["time"])
    emit("newDanmaku", {"type": "new", "newDanmaku": [
         (body["content"], body["time"])]}, broadcast=True)


if __name__ == "__main__":
    soc.run(app, "127.0.0.1", 8765, debug=True)
