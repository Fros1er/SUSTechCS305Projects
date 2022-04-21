import flask
import logging
from flask import Flask, redirect, render_template
from flask_socketio import SocketIO, join_room, emit
from NahelArgama import NahelArgama

# init flask app
app = Flask("Danmaku")
app.config['SECRET_KEY'] = 'secret!'
soc = SocketIO(app, cors_allowed_origins='*')

# disable logs, as every poll create one line of log
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)
# app.logger.disabled = True
# log.disabled = True

# init danmaku manager
danmakuHandler = NahelArgama()


@app.route("/")
def mainPage():
    '''
    router for root, it redirects user to ws version of rickroll.
    '''
    return redirect("/ws/video/rickroll")


@app.route("/http/<type>/<video>")
def httpPlayer(type, video):
    '''
    http version of video or live resources.
    streaming is simulated by video autoplayed and without controls.
    '''
    return render_template("danmu.html", videoName=video + ".mp4", mode="http", playType=type)


@app.route("/ws/<type>/<video>")
def wsPlayer(type, video):
    '''
    websocket version of video or live resources.
    streaming is simulated by video autoplayed and without controls.
    '''
    return render_template("danmu.html", videoName=video + ".mp4", mode="ws", playType=type)


@app.route("/video/<video>")
def loadDanmaku(video):
    '''
    send uuid and danmaku in db to http client for video
    '''
    return {
        "uuid": danmakuHandler.register(video),
        "danmaku": danmakuHandler.getHistory(video)
    }


@app.route("/live/<live>")
def registerLive(live):
    '''
    send uuid to http client for livestream
    '''
    return {
        "uuid": danmakuHandler.register(live, False)
    }


@app.route("/poll/<video>/<key>")
def pollDanmaku(video, key):
    '''
    route for polling danmaku.
    '''
    return {
        "newDanmaku": danmakuHandler.getUnreceived(video, key)
    }


@app.route("/send/<name>", methods=['POST'])
def sendDanmaku(name):
    '''
    receive danmaku send by http client.
    name: video name
    data: {"type": video or live, "content": content, "time"(if video): time}
    we need to emit event for websocket there too.
    '''
    data = flask.request.get_json()
    if data["type"] == "video":
        danmakuHandler.sendVideoDanmaku(name, data["content"], data["time"])
        soc.emit("newDanmaku", {"newDanmaku": [
             (data["content"], data["time"])]}, to=name)
    else:
        danmakuHandler.sendLiveDanmaku(name, data["content"])
        soc.emit("newDanmaku", {"newDanmaku": [data["content"]]}, to=name)
    return ""


@soc.on('getHistory')
def wsLoadDanmaku(data):
    '''
    send danmaku in db to ws client for video, and register the client.
    websocket client is grouped by room. Once new danmaku is sent by client, 
    all ws client in corresponding room is boardcasted.
    '''
    danmakuHandler.registerVideo(data["video"])
    emit("loadDanmaku", {"danmaku": danmakuHandler.getHistory(data["video"])})
    join_room(data["video"])


@soc.on('register')
def wsRegisterLive(data):
    '''
    register live to handler, and join the client to room.
    '''
    danmakuHandler.registerVideo(data["live"])
    join_room(data["live"])


@soc.on('sendDanmaku')
def wsSendDanmaku(data):
    '''
    receive danmaku send by websocket client.
    data: {"type": video or live, "video": video or livestream name,
            "content": content, "time"(if video): time}
    we need to give danmaku to handler for http client too.
    '''
    if data["type"] == "video":
        danmakuHandler.sendVideoDanmaku(
            data["video"], data["content"], data["time"])
        soc.emit("newDanmaku", {"newDanmaku": [
            (data["content"], data["time"])]}, to=data["video"])
    else:
        danmakuHandler.sendLiveDanmaku(data["video"], data["content"])
        soc.emit("newDanmaku", {"newDanmaku": [data["content"]]}, to=data["video"])


if __name__ == "__main__":
    soc.run(app, "0.0.0.0", 8765)
