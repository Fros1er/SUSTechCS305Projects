import { lowerBound } from "./util.js"

/**
 * Danmaku render engine.
 */
export class DanmakuEngine {

    /**
     * sorted list for all danmakus in video mode.
     * for live, it's a buffer for unsend danmakus, and is emptied after send.
     */
    danmakuList = []

    /**
     * a pointer or cursor for last sended danmaku in video mode.  
     * used for reduce searching time.
     */
    cursor = 0

    /** 
     * list for timers created by function addInterval.
     */
    timers = []

    /**
     * list for dom elements created by function createDanmaku.
     */
    currentDanmakuDomList = []

    /**
     * timer for checking video's current time.
     */
    queryInterval = null

    paused = false

    // video and container dom elements
    videoDom = undefined
    containerDom = undefined

    /**
     * bind video and danmaku container to engine.
     */
    constructor(videoDom, containerDom) {
        this.videoDom = videoDom
        this.containerDom = containerDom
    }

    /**
     * remove all danmaku dom elements and timers.
     */
    clear() {
        for (let e of this.currentDanmakuDomList) {
            e.remove()
        }
        for (let e of this.timers) {
            clearInterval(e)
        }
        this.currentDanmakuDomList = []
        this.timers = []
    }

    /**
     * callback function, need to bind to videoPlayer's seek event.  
     * when user redirects video, clear all existed danmaku and redirect cursor.
     */
    redirect(time) {
        this.clear()
        this.cursor = lowerBound(this.danmakuList, time)
    }

    /**
     * function for start live mode. need to bind to videoPlayer's play event.  
     * clear existed stated in engine, start a timer to render all danmaku 
     * in list, then clear the list.
     */
    dry() {
        this.paused = false;
        if (!this.queryInterval)
            clearInterval(this.queryInterval)
        this.queryInterval = null
        this.clear()

        this.queryInterval = setInterval(() => {
            for (let v of this.danmakuList) {
                let danmaku = this.createDanmaku(v[0])
                this.currentDanmakuDomList.push(danmaku)
                this.addInterval(danmaku)
            }
            this.danmakuList = []
        }, 50)
    }

    /**
     * function for start video mode. need to bind to videoPlayer's play event.   
     * clear existed queryInterval, then start a timer to check whether video's time is larger than a danmaku's time.
     */
    start() {
        if (!this.queryInterval)
            clearInterval(this.queryInterval)
        this.paused = false
        this.queryInterval = setInterval(() => {
            // if danmaku list is not drained and a danmaku's time less or equal than current time
            while (this.cursor < this.danmakuList.length && this.danmakuList[this.cursor][1] <= this.videoDom.currentTime) {
                // create danmaku dom, play it, then move the cursor.
                let danmaku = this.createDanmaku(this.danmakuList[this.cursor][0])
                this.currentDanmakuDomList.push(danmaku)
                this.addInterval(danmaku)
                this.cursor++
            }
        }, 50)
    }

    /**
     * function for pause danmaku. need to bind to videoPlayer's pause event.   
     * stop queryInterval, set paused = true to stop all danmaku's movement. 
     */
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
            if (this.paused) return // if paused, stop updateing position
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
