/* 通过 /dev/uinput 注入一次触摸点击，用来验证 Wayland 输入通路。 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <time.h>
#include <linux/uinput.h>
#include <sys/ioctl.h>

static void emit(int fd, int type, int code, int val) {
    struct input_event ev;
    memset(&ev, 0, sizeof(ev));
    ev.type = type; ev.code = code; ev.value = val;
    if (write(fd, &ev, sizeof(ev)) != sizeof(ev)) { perror("input write"); exit(5); }
}

int main(int argc, char **argv) {
    int swipe = argc > 1 && !strcmp(argv[1], "--swipe");
    if (swipe && argc != 6 && argc != 7) return 1;
    int offset = swipe ? 1 : 0;
    int x = argc > 1+offset ? atoi(argv[1+offset]) : 270;
    int y = argc > 2+offset ? atoi(argv[2+offset]) : 540;
    int end_x = swipe ? atoi(argv[4]) : x;
    int end_y = swipe ? atoi(argv[5]) : y;
    int duration = swipe && argc == 7 ? atoi(argv[6]) : 300;
    if (x<0 || x>1079 || y<0 || y>2159 || end_x<0 || end_x>1079 || end_y<0 || end_y>2159 || duration<40 || duration>2000) return 1;
    int fd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
    if (fd < 0) { perror("open /dev/uinput"); return 2; }

    ioctl(fd, UI_SET_EVBIT, EV_KEY);
    ioctl(fd, UI_SET_EVBIT, EV_ABS);
    ioctl(fd, UI_SET_EVBIT, EV_SYN);
    ioctl(fd, UI_SET_KEYBIT, BTN_TOUCH);
    ioctl(fd, UI_SET_ABSBIT, ABS_MT_SLOT);
    ioctl(fd, UI_SET_ABSBIT, ABS_MT_TRACKING_ID);
    ioctl(fd, UI_SET_ABSBIT, ABS_MT_POSITION_X);
    ioctl(fd, UI_SET_ABSBIT, ABS_MT_POSITION_Y);
    ioctl(fd, UI_SET_PROPBIT, INPUT_PROP_DIRECT);

    struct uinput_abs_setup ax = {0}, ay = {0}, aslot = {0}, atid = {0};
    ax.code = ABS_MT_POSITION_X; ax.absinfo.minimum = 0; ax.absinfo.maximum = 1079;
    ay.code = ABS_MT_POSITION_Y; ay.absinfo.minimum = 0; ay.absinfo.maximum = 2159;
    aslot.code = ABS_MT_SLOT; aslot.absinfo.maximum = 9;
    atid.code = ABS_MT_TRACKING_ID; atid.absinfo.maximum = 65535;
    ioctl(fd, UI_ABS_SETUP, &ax); ioctl(fd, UI_ABS_SETUP, &ay);
    ioctl(fd, UI_ABS_SETUP, &aslot); ioctl(fd, UI_ABS_SETUP, &atid);

    struct uinput_setup us;
    memset(&us, 0, sizeof(us));
    strncpy(us.name, "saidroid-vtouch", UINPUT_MAX_NAME_SIZE - 1);
    us.id.bustype = BUS_VIRTUAL;
    us.id.vendor = 0x1209; us.id.product = 0x0001; us.id.version = 1;
    if (ioctl(fd, UI_DEV_SETUP, &us) < 0) { perror("UI_DEV_SETUP"); return 3; }
    if (ioctl(fd, UI_DEV_CREATE) < 0) { perror("UI_DEV_CREATE"); return 4; }
    usleep(400000);

    emit(fd, EV_ABS, ABS_MT_SLOT, 0);
    emit(fd, EV_ABS, ABS_MT_TRACKING_ID, 1);
    emit(fd, EV_ABS, ABS_MT_POSITION_X, x);
    emit(fd, EV_ABS, ABS_MT_POSITION_Y, y);
    emit(fd, EV_KEY, BTN_TOUCH, 1);
    emit(fd, EV_SYN, SYN_REPORT, 0);
    if (swipe) {
        for (int step=1; step<=20; step++) {
            usleep(duration*1000/20);
            emit(fd, EV_ABS, ABS_MT_POSITION_X, x+(end_x-x)*step/20);
            emit(fd, EV_ABS, ABS_MT_POSITION_Y, y+(end_y-y)*step/20);
            emit(fd, EV_SYN, SYN_REPORT, 0);
        }
    } else usleep(120000);
    emit(fd, EV_KEY, BTN_TOUCH, 0);
    emit(fd, EV_ABS, ABS_MT_TRACKING_ID, -1);
    emit(fd, EV_SYN, SYN_REPORT, 0);
    usleep(200000);
    ioctl(fd, UI_DEV_DESTROY);
    close(fd);
    printf("INJECT_DONE x=%d y=%d end_x=%d end_y=%d swipe=%d\n", x, y, end_x, end_y, swipe);
    return 0;
}
