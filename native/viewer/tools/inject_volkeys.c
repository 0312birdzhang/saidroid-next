/* 注入一次「音量上+音量下」组合键。
 * Sailfish 的截图就是这个手势（Lipstick 里处理），所以可以用它抓到真实屏幕。
 * 用法： inject_volkeys [按住毫秒数，默认 120]
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <time.h>
#include <linux/uinput.h>
#include <sys/ioctl.h>

static void emit(int fd, int type, int code, int val)
{
	struct input_event ev;
	memset(&ev, 0, sizeof(ev));
	ev.type = type;
	ev.code = code;
	ev.value = val;
	if (write(fd, &ev, sizeof(ev)) < 0) {
		perror("write");
	}
}

int main(int argc, char **argv)
{
	int hold = argc > 1 ? atoi(argv[1]) : 120;
	int fd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
	if (fd < 0) {
		perror("open /dev/uinput");
		return 2;
	}
	ioctl(fd, UI_SET_EVBIT, EV_KEY);
	ioctl(fd, UI_SET_EVBIT, EV_SYN);
	ioctl(fd, UI_SET_KEYBIT, KEY_VOLUMEUP);
	ioctl(fd, UI_SET_KEYBIT, KEY_VOLUMEDOWN);

	struct uinput_user_dev udev;
	memset(&udev, 0, sizeof(udev));
	snprintf(udev.name, sizeof(udev.name), "sd-volkeys");
	udev.id.bustype = BUS_VIRTUAL;
	udev.id.vendor = 0x1234;
	udev.id.product = 0x5679;
	udev.id.version = 1;
	if (write(fd, &udev, sizeof(udev)) < 0) {
		perror("write uinput_user_dev");
	}
	if (ioctl(fd, UI_DEV_CREATE) < 0) {
		perror("UI_DEV_CREATE");
		return 3;
	}
	usleep(300 * 1000);            /* 等合成器认到新设备 */

	emit(fd, EV_KEY, KEY_VOLUMEUP, 1);
	emit(fd, EV_SYN, SYN_REPORT, 0);
	emit(fd, EV_KEY, KEY_VOLUMEDOWN, 1);
	emit(fd, EV_SYN, SYN_REPORT, 0);
	usleep((useconds_t)hold * 1000);

	emit(fd, EV_KEY, KEY_VOLUMEUP, 0);
	emit(fd, EV_KEY, KEY_VOLUMEDOWN, 0);
	emit(fd, EV_SYN, SYN_REPORT, 0);
	usleep(100 * 1000);

	ioctl(fd, UI_DEV_DESTROY);
	close(fd);
	printf("VOLKEYS_SENT\n");
	return 0;
}
