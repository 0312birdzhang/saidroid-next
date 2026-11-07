import QtQuick 2.2
import org.wpewebkit.qtwpe 1.0
Rectangle {
    color: "#ee0055"
    width: 720; height: 1280
WPEView {
    id: web
    anchors.fill: parent
    width: 720; height: 1280
    onWebViewCreated: {
        console.log("SDWEBHOST=webview_created")
        loadHtml("<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'></head><body style='margin:0;background:white'><div style='height:600px;background:#0b3d91;color:white;font-size:60px'>SailDroid WebView</div><div style='height:600px;background:#b5651d;color:white;font-size:60px' id='result'></div><canvas id='c' width='720' height='600'></canvas><script>document.title='JS='+7*6;document.getElementById('result').textContent='JavaScript: '+7*6;var c=document.getElementById('c').getContext('2d');c.fillStyle='#00aa55';c.fillRect(0,0,720,600);addEventListener('scroll',function(){document.title='scrollY='+scrollY});</script></body></html>", "https://saidroid.invalid/")
    }
    onTitleChanged: console.log("SDWEBHOST=title|value=" + title)
    onLoadingChanged: console.log("SDWEBHOST=load|status=" + loadRequest.status + "|error=" + loadRequest.errorString)
    Timer { interval: 6000; running: true; onTriggered: web.runJavaScript("window.scrollTo(0,600);document.title='scrollY='+scrollY", function(result) { console.log("SDWEBHOST=eval|result=" + result) }) }
}

}
