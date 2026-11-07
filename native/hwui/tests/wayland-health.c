#define _POSIX_C_SOURCE 200809L
#include <wayland-client.h>
#include <errno.h>
#include <poll.h>
#include <stdio.h>
#include <time.h>

/* A live compositor PID alone does not prove its event loop is making progress.
 * This creates no surface or GPU context and requires an actual sync response. */
static int complete;
static void done(void *data, struct wl_callback *callback, uint32_t serial) {
    (void)data;(void)serial;complete=1;wl_callback_destroy(callback);
}
static const struct wl_callback_listener listener={done};
static int64_t now_ms(void) {
    struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);
    return (int64_t)t.tv_sec*1000+t.tv_nsec/1000000;
}
int main(void) {
    struct wl_display *display=wl_display_connect(NULL);
    if(!display){perror("WAYLAND_HEALTH=connect_failed");return 1;}
    struct wl_callback *callback=wl_display_sync(display);
    if(!callback){wl_display_disconnect(display);return 1;}
    wl_callback_add_listener(callback,&listener,NULL);
    int result=1;int64_t deadline=now_ms()+3000;
    while(!complete) {
        while(wl_display_prepare_read(display)!=0) {
            if(wl_display_dispatch_pending(display)<0)goto finish;
        }
        if(complete){wl_display_cancel_read(display);break;}
        if(wl_display_flush(display)<0&&errno!=EAGAIN){wl_display_cancel_read(display);goto finish;}
        int64_t left=deadline-now_ms();
        if(left<=0){wl_display_cancel_read(display);goto finish;}
        struct pollfd fd={wl_display_get_fd(display),POLLIN,0};
        int events=poll(&fd,1,(int)left);
        if(events<0&&errno==EINTR){wl_display_cancel_read(display);continue;}
        if(events<=0||!(fd.revents&POLLIN)){wl_display_cancel_read(display);goto finish;}
        if(wl_display_read_events(display)<0)goto finish;
        if(wl_display_dispatch_pending(display)<0)goto finish;
    }
    result=0;
finish:
    printf("WAYLAND_HEALTH=%s|surface_count=0\n",result?"unresponsive":"ready");
    wl_display_disconnect(display);return result;
}
