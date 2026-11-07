import QtQuick 2.2
import org.wpewebkit.qtwpe 1.0
Item {
    id: root
    function report(o) { bridge.event(JSON.stringify(o)) }
    function command(o) {
        if (o.op === "load") {
            if (o.html !== undefined) web.loadHtml(o.html, o.base || "about:blank")
            else web.url = o.url
        } else if (o.op === "post") {
            // Android postUrl's body is application/x-www-form-urlencoded.
            // A real WebKit form submission preserves POST, cookies and redirects.
            var data = JSON.stringify({url:o.url,body:o.body}).replace(/<\//g,"<\\/")
            var html = "<!doctype html><meta charset='utf-8'><script>(function(){var d=" + data + ";var f=document.createElement('form');f.method='POST';f.action=d.url;new URLSearchParams(atob(d.body)).forEach(function(v,k){var i=document.createElement('input');i.type='hidden';i.name=k;i.value=v;f.appendChild(i)});document.documentElement.appendChild(f);f.submit()})();<" + "/script>"
            web.loadHtml(html,o.url)
        } else if (o.op === "eval") {
            web.runJavaScript(o.script, function(value) {
                report({event:"eval",id:o.id,result:JSON.stringify(value) === undefined ? "null" : JSON.stringify(value)})
            })
        } else if (o.op === "back") web.goBack()
        else if (o.op === "forward") web.goForward()
        else if (o.op === "reload") web.reload()
        else if (o.op === "stop") web.stop()
        else report({event:"unsupported",op:o.op})
    }
    WPEView {
        id: web
        objectName: "web"
        anchors.fill: parent
        onWebViewCreated: root.report({event:"engine_created"})
        onTitleChanged: root.report({event:"title",title:title})
        onUrlChanged: root.report({event:"url",url:url.toString()})
        onLoadProgressChanged: root.report({event:"progress",value:loadProgress})
        onLoadingChanged: root.report({event:"load",status:loadRequest.status,error:loadRequest.errorString,url:loadRequest.url.toString()})
        onScrollPositionChanged: root.report({event:"scroll",y:scrollY,height:scrollHeight,viewport:innerHeight})
        onBackForwardChanged: root.report({event:"history",back:canGoBack,forward:canGoForward})
    }
}
