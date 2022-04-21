import { lowerBound } from "./util.js"

export class DanmakuEngine {

    danmakuList = []
    danmakuSpeed = 3
    cursor = 0
    timers = []
    currentDanmakuDomList = []
    queryInterval = null
    paused = false
    videoDom = undefined
    containerDom = undefined
    
    constructor(videoDom, containerDom) {
        this.videoDom = videoDom
        this.containerDom = containerDom
    }

    clear() {
        for (let e of this.currentDanmakuDomList) {
            e.remove()
        }
        for (let e of this.timers) {
            clearInterval(e)
        }
    }

    redirect(time) {
        this.clear()
        this.currentDanmakuDomList = []
        this.cursor = lowerBound(this.danmakuList, time)
    }

    dry() {
        this.paused = false;
        if (!this.queryInterval)
            clearInterval(this.queryInterval)
        this.queryInterval = null
        this.clear()
        this.queryInterval = setInterval
        this.queryInterval = setInterval(() => {
            for (let v of this.danmakuList) {
                let danmaku = this.createDanmaku(v[0])
                this.currentDanmakuDomList.push(danmaku)
                this.addInterval(danmaku)
            }
            this.danmakuList = []
        }, 10)
    }

    start() {
        if (!this.queryInterval)
            clearInterval(this.queryInterval)
        this.paused = false
        this.queryInterval = setInterval(() => {
            while (this.cursor < this.danmakuList.length && this.danmakuList[this.cursor][1] <= this.videoDom.currentTime) {
                let danmaku = this.createDanmaku(this.danmakuList[this.cursor][0])
                this.currentDanmakuDomList.push(danmaku)
                this.addInterval(danmaku)
                this.cursor++
            }
        }, 5)
    }

    pause() {
        this.paused = true
        if (!this.queryInterval)
            clearInterval(this.queryInterval)
        this.queryInterval = null
    }

    // create a Dom object corresponding to a danmaku
    createDanmaku(text) {
        const jqueryDom = $("<div class='bullet'>" + text + "</div>")
        const fontColor = "rgb(255,255,255)"
        const fontSize = "20px"
        let height = this.containerDom.height();
        let top = Math.floor(height * 0.05 + Math.random() * 0.9 * height) + "px"
        const left = this.containerDom.width() + "px"
        jqueryDom.css({
            "position": 'absolute',
            "color": fontColor,
            "font-size": fontSize,
            "left": left,
            "top": top,
        })
        this.containerDom.append(jqueryDom)
        return jqueryDom
    }
    // add timer task to let the danmaku fly from right to left
    addInterval(jqueryDom) {
        let left = jqueryDom.offset().left - this.containerDom.offset().left
        const timer = setInterval(() => {
            if (this.paused) return
            left--
            jqueryDom.css("left", left + "px")
            if (jqueryDom.offset().left + jqueryDom.width() < this.containerDom.offset().left) {
                for (let i = 0; i < this.currentDanmakuDomList.length; i++) {
                    if (this.currentDanmakuDomList[i] == jqueryDom) {
                        this.currentDanmakuDomList.splice(i, 1)
                    }
                }
                jqueryDom.remove()
                for (let i = 0; i < this.timers.length; i++) {
                    if (this.timers[i] == timer) {
                        this.timers.splice(i, 1)
                    }
                }
                clearInterval(timer)
            }
        }, 5) // set delay as 5ms,which means the danmaku changes its position every 5ms
        this.timers.push(timer)
    }
}
