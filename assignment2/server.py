import flask
from flask import Flask, redirect, render_template
from flask_socketio import SocketIO, emit, join_room
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
    return redirect("/http/video/rickroll")


@app.route("/http/<type>/<video>")
def httpPlayer(type, video):
    return render_template("danmu.html", videoName=video + ".mp4", mode="http")


@app.route("/ws/<type>/<video>")
def wsPlayer(type, video):
    return render_template("danmu.html", videoName=video + ".mp4", mode="ws")


@app.route("/video/<video>")
def loadDanmaku(video):
    return {
        "uuid": danmakuHandler.register(video),
        "danmaku": danmakuHandler.getHistory(video)
    }


@app.route("/live/<live>")
def registerLive(live):
    return {
        "uuid": danmakuHandler.register(live, False)
    }


@app.route("/poll/<video>/<key>")
def pollDanmaku(video, key):
    return {"type": "new", "newDanmaku": danmakuHandler.getUnreceived(video, key)}


@app.route("/send/<name>", methods=['POST'])
def sendDanmaku(name):
    data = flask.request.get_json()
    if data["type"] == "video":
        danmakuHandler.sendVideo(name, data["content"], data["time"])
    else:
        danmakuHandler.sendLive(name, data["content"])
    return ""


@soc.on('getHistory')
def wsLoadDanmaku(data):
    join_room(data["video"])
    emit("loadDanmaku", {"danmaku": danmakuHandler.getHistory(data["video"])})

@soc.on('register')
def wsRegister(data):
    join_room(data["video"])

@soc.on('sendDanmaku')
def wsSendDanmaku(data):
    if data["type"] == "video":
        danmakuHandler.sendVideo(data["video"], data["content"], data["time"])
        emit("newDanmaku", {"newDanmaku": [
            (data["content"], data["time"])]}, to=data["video"])
    else:
        danmakuHandler.sendLive(data["video"], data["content"])
        emit("newDanmaku", {"newDanmaku": data["content"]}, to=data["video"])


if __name__ == "__main__":
    soc.run(app, "127.0.0.1", 8765, debug=True)
