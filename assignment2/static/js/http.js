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

let uuid = undefined;
fetch("/danmaku").then(res => res.json()).then(data => {
    engine.danmakuList = data["danmaku"]
    for (let danmaku of data["danmaku"]) {
        addDanmakuTableRow(danmaku[0], danmaku[1]);
    }
    uuid = data["uuid"];
})

let poll = setInterval(function () {
    if (uuid != undefined) {
        fetch("/poll/" + uuid).then(res => res.json()).then(data => {
            for (let danmaku of data["newDanmaku"]) {
                let res = upperBound(engine.danmakuList, danmaku[1]);
                console.log(res);
                engine.danmakuList.splice(res, 0, danmaku);
                addDanmakuTableRowAfter(danmaku[0], danmaku[1], res);
            }
        }).catch(e => clearInterval(poll))
    }
}, 50);

$(".send").on("click", function () {
    fetch("/send", {
        method: 'POST',
        cache: "no-cache",
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            "content": danmakuInput.value,
            "time": videoPlayer[0].currentTime
        })
    })
});