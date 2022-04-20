import { upperBound } from './util.js';
import { DanmakuEngine } from './DanmakuEngine.js';

const danmakuInput = $("#danmakutext")[0]
const videoPlayer = $("video")
const danmakuContainer = $(".screen_container")

const engine = new DanmakuEngine(videoPlayer[0], danmakuContainer)

videoPlayer.on("seeked", () => {
    engine.redirect(videoPlayer[0].currentTime);
});

// generate new danmakus
videoPlayer.on("play", (e) => {
    engine.start()
});

//pause danmakus
videoPlayer.on("pause", (e) => {
    engine.pause()
});

const tableBody = $(".table_div tbody");
function addDanmakuTableRow(content, time) {
    tableBody.append("<tr><td>" + content + "</td><td>" + time + "</td></tr>")
}

function addDanmakuTableRowAfter(content, time, index) {
    $("tr", tableBody).eq(index).after("<tr><td>" + content + "</td><td>" + time + "</td></tr>")
}

var socket = io("127.0.0.1:8765");
socket.on('loadDanmaku', function (data) {
    engine.danmakuList = data["danmaku"]
    for (let danmaku of data["danmaku"]) {
        addDanmakuTableRow(danmaku[0], danmaku[1]);
    }
});

socket.on("newDanmaku", function (data) {
    for (let danmaku of data["newDanmaku"]) {
        let res = upperBound(engine.danmakuList, danmaku[1]);
        engine.danmakuList.splice(res, 0, danmaku);
        addDanmakuTableRowAfter(danmaku[0], danmaku[1], res);
    }
});

$(".send").on("click", function () {
    socket.emit("sendDanmaku", {
        "content": danmakuInput.value,
        "time": videoPlayer[0].currentTime
    })
});