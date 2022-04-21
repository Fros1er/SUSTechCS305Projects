import { upperBound } from './util.js'
import { DanmakuEngine } from './DanmakuEngine.js'

const danmakuInput = $("#danmakutext")[0]
const videoPlayer = $("video")
const danmakuContainer = $(".screen_container")

// get infomations from url
const paths = window.location.pathname.split('/')
const videoName = paths.pop()
const playType = paths.pop()
const protocolType = paths.pop()

const engine = new DanmakuEngine(videoPlayer[0], danmakuContainer)

// live mode: remove controls from videoPlayer, and play it directly.
if (playType == "live") {
    videoPlayer.removeAttr('controls')
}

videoPlayer.on("seeked", () => {
    if (playType == "video") {
        engine.redirect(videoPlayer[0].currentTime)
    }
})

videoPlayer.on("play", () => {
    if (playType == "video") {
        engine.start()
    } else {
        engine.dry() // as controls is hidden, play event will only be triggered once 
    }
})

videoPlayer.on("pause", () => {
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
    /*
    data = {
        "newDanmaku": [[content, time(if video)], ...] in video mode,
        "newDanmaku": [content, ...] in Live mode
    }
    */
    if (playType == "video") {
        for (let danmaku of data["newDanmaku"]) {
            // insert new danmaku to list in order
            let res = upperBound(engine.danmakuList, danmaku[1])
            engine.danmakuList.splice(res, 0, danmaku)
            addDanmakuTableRowAfter(danmaku[0], danmaku[1], res)
        }
    } else { // livestream mode
        for (let s of data["newDanmaku"]) {
            engine.danmakuList.push([s])
        }
        for (let danmaku of data["newDanmaku"]) {
            addDanmakuTableRow(danmaku, 0) // live mode's time in table is all set to 0
        }
    }
}

if (protocolType == "http") {
    let uuid = undefined
    // get sorted history danmaku and uuid
    let url = "/" + playType + "/"
    if (playType == "live") {
        url += "live_"
    }
    fetch(url + videoName).then(res => res.json()).then(data => {
        if (playType == "video") {
            engine.danmakuList = data["danmaku"] // override existed danmaku list
            for (let danmaku of data["danmaku"]) { // add to table
                addDanmakuTableRow(danmaku[0], danmaku[1])
            }
        }
        uuid = data["uuid"]
    })

    // start polling.
    let poll = setInterval(function () {
        if (uuid != undefined) {
            let url = "/poll/"
            if (playType == "live") {
                url += "live_"
            }
            fetch(url + videoName + "/" + uuid).then(res => res.json()).then(data => {
                parseNewDanmakus(data)
            }).catch(() => clearInterval(poll))
        }
    }, 50)

    $(".send").on("click", function () {
        let body = {
            "type": playType,
            "content": danmakuInput.value
        }
        if (playType == "video") {
            body["time"] = videoPlayer[0].currentTime
        }
        let url = "/send/"
        if (playType == "live") {
            url += "live_"
        }
        fetch(url + videoName, {
            method: 'POST',
            cache: "no-cache",
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body)
        })
    })
} else { // websocket
    var socket = io()
    if (playType == "video") {
        socket.emit("getHistory", { "video": videoName })
    } else { // livestream
        socket.emit("register", { "live": "live_" + videoName })
    }

    // load history event. If in live mode, the event will never be emitted.
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
            "content": danmakuInput.value,
        }
        if (playType == "video") {
            body["time"] = videoPlayer[0].currentTime
            body["video"] = videoName
        } else {
            body["video"] = "live_" + videoName
        }
        socket.emit("sendDanmaku", body)
    })
}
