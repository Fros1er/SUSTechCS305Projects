import { upperBound } from './util.js'
import { DanmakuEngine } from './DanmakuEngine.js'

const danmakuInput = $("#danmakutext")[0]
const videoPlayer = $("video")
const danmakuContainer = $(".screen_container")
const paths = window.location.pathname.split('/')
const videoName = paths.pop()
const playType = paths.pop()
const protocolType = paths.pop()

const engine = new DanmakuEngine(videoPlayer[0], danmakuContainer)

videoPlayer.on("seeked", () => {
    if (playType == "video") {
        engine.redirect(videoPlayer[0].currentTime)
    }
})

// generate new danmakus
videoPlayer.on("play", (e) => {
    if (playType == "video") {
        engine.start()
    } else {
        engine.dry()
    }
})

//pause danmakus
videoPlayer.on("pause", (e) => {
    if (playType == "video") {
        engine.pause()
    }
})

const tableBody = $(".table_div tbody")
function addDanmakuTableRow(content, time) {
    tableBody.append("<tr><td>" + content + "</td><td>" + time + "</td></tr>")
}

function addDanmakuTableRowAfter(content, time, index) {
    $("tr", tableBody).eq(index).after("<tr><td>" + content + "</td><td>" + time + "</td></tr>")
}

function parseNewDanmakus(data) {
    if (playType == "video") {
        for (let danmaku of data["newDanmaku"]) {
            let res = upperBound(engine.danmakuList, danmaku[1])
            engine.danmakuList.splice(res, 0, danmaku)
            addDanmakuTableRowAfter(danmaku[0], danmaku[1], res)
        }
    } else {
        engine.danmakuList.push([data["newDanmaku"]])
        addDanmakuTableRow(data["newDanmaku"], 0)
    }
}

if (protocolType == "http") {
    let uuid = undefined
    fetch("/" + playType + "/" + videoName).then(res => res.json()).then(data => {
        if (playType == "video") {
            engine.danmakuList = data["danmaku"]
            for (let danmaku of data["danmaku"]) {
                addDanmakuTableRow(danmaku[0], danmaku[1])
            }
        }
        uuid = data["uuid"]
    })

    let poll = setInterval(function () {
        if (uuid != undefined) {
            fetch("/poll/" + videoName + "/" + uuid).then(res => res.json()).then(data => {
                parseNewDanmakus(data)
            }).catch(() => clearInterval(poll))
        }
    }, 50)

    $(".send").on("click", function () {
        let body = {
            "type": "video",
            "content": danmakuInput.value
        }
        if (playType == "video") {
            body["time"] = videoPlayer[0].currentTime
        }
        fetch("/send/" + videoName, {
            method: 'POST',
            cache: "no-cache",
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body)
        })
    })
} else {
    var socket = io("127.0.0.1:8765")
    if (playType == "video") {
        socket.emit("getHistory", { "video": videoName })
    } else {
        socket.emit("register", { "video": videoName })
    }

    socket.on('loadDanmaku', function (data) {
        engine.danmakuList = data["danmaku"]
        for (let danmaku of data["danmaku"]) {
            addDanmakuTableRow(danmaku[0], danmaku[1])
        }
    })

    socket.on("newDanmaku", function (data) {
        parseNewDanmakus(data)
    })

    $(".send").on("click", function () {
        let body = {
            "type": playType,
            "video": videoName,
            "content": danmakuInput.value,
        }
        if (playType == "video") {
            body["time"] = videoPlayer[0].currentTime
        }
        socket.emit("sendDanmaku", body)
    })
}
