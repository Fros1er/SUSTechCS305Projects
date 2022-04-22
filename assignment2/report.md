# Computer Networks Assignment 2

# About code

In code, there's a lot of json fields named "video". Actually, it means "video or livestream names". I did this for some convience, but it sometimes is confusing. 

## server.py

I used flask to implement the server. 

The server does jobs below:
1. Serve and rendering html pages and video. The video need to be put in static folder.
2. forward all http requests to danmakuManager
3. receive danmaku and requests from websocket, forward them to manager and broadcast danmaku to websocket clients
4. assign ws clients to different rooms for broadcasting
5. build message and send them back to servers.

I put nearly all websocket part in server, as room was convient to use, and I didn't need a manager to handle messages for polling.  

## NahelArgama.py
For http part, I made a manager to manage requests' id and unpolled danmakus. It's also used to write danmakus to sqlite.

In manager, all unsend danmakus are grouped by video or livestream names, then , it will be appended to serveral lists for each http client playing video or livestream. Clients are identified by unique uuids. When a client is polling danmaku from manager, manager get all unsend danmakus by name and uuid, send them, and clear the list.

All clients need to register to manager when it's connected to the server. 

If a client didn't poll new danmaku for longer than 30 seconds, it will be removed from manager when new danmaku is going to be added to it.

Besides sending danmaku to lists, manager will also store newly received danmaku to sqlite immediately. It's quite annoying that sqlite is single-threaded with a lock, which slows the program.

Also, the filename of video to be played can't start with "live_". I put livestream and video in the same dict at the beginning, and I didn't mentioned that livestream and video can have the same name until I nearly finished the assignment. In order to avoid the problem, all livestreams are added with "live_" in front of their name in the frontend.

## main.js

Websocket and http protocols, video and livestream modes shares the same js file. It deduces these types from url.

Nearly everything is main.js is for send requests and bind events to engine, which are clearly described by comments.

## DanmakuEngine.js

A class for rendering danmaku to dom. Comments are clear, too.

The only thing need to be mentioned here is finding the next danmaku. For video, the engine is maintaining a sorted danmaku list and a cursor. Every 50 ms it will check whether the video's current time is larger than the danmaku which cursor is pointing to. If it is, engine will render the danmaku and move the cursor to next position.

When the video's time is modified by user, it will find the position of cursor by binary search.

# Running results:

The live mode is simulated by autoplayed video without controls. As chrome limits that autoplayed video need to be muted, the video in live mode has no sound.

The server is running well with multiple videos and livestreams accessed together.

Running steps:
1. Access http://localhost:8765/
2. The page will be redirected to http://localhost:8765/ws/video/rickroll
3. Several links is provided in the page. The first two links are for switching between videos, the remaining four are for switching between modes.
4. Url format: http://127.0.0.1:8765/protocol(ws or http)/mode(video or live)/videoname(rickroll or kongming provided by default)
5. If you want to add more video, put them directly in static folder, and access it by it's filename(without suffix). Only mp4 video is supported.
