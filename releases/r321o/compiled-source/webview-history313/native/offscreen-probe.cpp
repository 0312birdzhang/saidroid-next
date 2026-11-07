// Standalone host-side experiment. No ART/bionic or system-compositor changes.
#include <QGuiApplication>
#include <QQmlEngine>
#include <QQmlComponent>
#include <QQuickItem>
#include <QQuickWindow>
#include <QQuickRenderControl>
#include <QOpenGLContext>
#include <QOpenGLFunctions>
#include <QOffscreenSurface>
#include <QOpenGLFramebufferObject>
#include <QTimer>
#include <QImage>
#include <QDebug>

static void logMessage(QtMsgType, const QMessageLogContext &, const QString &message)
{
    fprintf(stderr, "%s\n", message.toUtf8().constData()); fflush(stderr);
}

int main(int argc, char **argv)
{
    qInstallMessageHandler(logMessage);
    QGuiApplication app(argc, argv);
    if (argc != 3) { qCritical("usage: offscreen-probe scene.qml output-directory"); return 2; }
    QQuickRenderControl control;
    QQuickWindow window(&control);
    window.setGeometry(0, 0, 720, 1280);
    window.contentItem()->setSize(QSizeF(720,1280));
    QOpenGLContext context;
    QSurfaceFormat format;
    format.setRenderableType(QSurfaceFormat::OpenGLES);
    format.setVersion(2, 0);
    context.setFormat(format);
    if (!context.create()) { qCritical("SDWEBHOST=context_failed"); return 3; }
    QOffscreenSurface surface;
    surface.setFormat(context.format());
    surface.create();
    if (!surface.isValid() || !context.makeCurrent(&surface)) return 4;
    QOpenGLFramebufferObject fbo(QSize(720,1280), QOpenGLFramebufferObject::CombinedDepthStencil);
    if (!fbo.isValid()) return 5;
    window.setRenderTarget(&fbo);
    QQmlEngine engine;
    QQmlComponent component(&engine, QUrl::fromLocalFile(QString::fromLocal8Bit(argv[1])));
    if (component.isError()) { qCritical() << component.errors(); return 6; }
    QObject *object = component.create();
    QQuickItem *item = qobject_cast<QQuickItem *>(object);
    if (!item) { qCritical() << component.errors(); delete object; return 7; }
    item->setParentItem(window.contentItem());
    item->setSize(QSizeF(720,1280));
    control.initialize(&context);
    window.setRenderTarget(&fbo);
    qWarning("SDWEBHOST=initialized|offscreen=true|visible_windows=0");
    int ticks = 0;
    const QString output = QString::fromLocal8Bit(argv[2]);
    QTimer timer;
    QObject::connect(&timer, &QTimer::timeout, [&]() {
        context.makeCurrent(&surface);
        control.polishItems();
        control.sync();
        context.makeCurrent(&surface);
        fbo.bind();
        control.render();
        context.functions()->glFlush();
        QMetaObject::invokeMethod(&window,"frameSwapped",Qt::DirectConnection);
        if (++ticks == 100 || ticks == 250 || ticks == 400) {
            qWarning() << "SDWEBHOST=geometry|visible=" << item->isVisible() << "|size=" << QSizeF(item->width(),item->height()) << "|content=" << QSizeF(window.contentItem()->width(),window.contentItem()->height()) << "|glerror=" << context.functions()->glGetError();
            const QString path = output + QString("/frame-%1.png").arg(ticks);
            const bool saved = fbo.toImage().save(path);
            qWarning() << "SDWEBHOST=frame|tick=" << ticks << "|saved=" << saved << "|path=" << path;
        }
        if (ticks >= 450) app.quit();
    });
    timer.start(20);
    QTimer::singleShot(20000, &app, SLOT(quit()));
    int result = app.exec();
    context.makeCurrent(&surface);
    delete item;
    control.invalidate();
    return result;
}
