/* sdinput —— 通过 /dev/uinput 注入真实的触摸手势。
 *
 * 为什么需要：验证滚动流畅度、WebView 页面滚动、以及普通交互，都需要「真手势」，
 * 而不是一次瞬时 tap。已有的 inject_touch 只做单点点击。
 *
 * 用法：
 *   sdinput tap   X Y [按住毫秒]
 *   sdinput swipe X1 Y1 X2 Y2 [总时长毫秒] [步数]
 *   sdinput press X Y 毫秒           （长按）
 *   sdinput seq   'tap 791 1900; tap 1005 152; tap 400 1803'
 *                                    （一串手势只建一个 uinput 设备）
 *
 * 坐标是屏幕物理坐标（1080x2160）。设备侧运行，需要 root 打开 /dev/uinput。
 *
 * 为什么有 seq（2026-10-27）：sd-integration 观察到 lipstick 的 evdevtouch 插件
 * 每 4–5 秒报一次 `Could not read from input device (没有那个设备)`，dmesg 里
 * `input: sdinput as /devices/virtual/input/input30N` 的间隔正好等于我们每次
 * `sd.sh input` 的节奏——一次调用建一个 uinput 设备、发完就销毁，而 lipstick 的
 * 插件还持有旧 fd 在 poll。设备反复消失会让触摸路由反复重连，是我们能控制的
 * 唯一噪声源（lipstick 在 05:15 换过 pid 的根因无法归因，journal 已被轮转）。
 * 所以多步手势请用 seq：一次建、一次拆。
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <time.h>
#include <linux/uinput.h>
#include <sys/ioctl.h>

static int fd = -1;
/* 写入账本：注入器只能证明"我写了"，但至少要能证明"每一次 write 都成功了"。
 * 之前只打一行意图日志（SDINPUT=tap），写失败也只 perror，上层无法区分
 * "注入了" 和 "写进去了"。这里每笔手势结束时打一行 finished|writes|errors，
 * 上层据此才算 delivered。 */
static int emit_writes, emit_errors;

static void emit(int type, int code, int value)
{
	struct input_event ev;
	memset(&ev, 0, sizeof(ev));
	ev.type = type;
	ev.code = code;
	ev.value = value;
	if (write(fd, &ev, sizeof(ev)) != (ssize_t)sizeof(ev)) {
		perror("write input_event");
		emit_errors++;
	} else {
		emit_writes++;
	}
}

static void report(const char *kind)
{
	printf("SDINPUT=finished|kind=%s|writes=%d|errors=%d\n", kind, emit_writes, emit_errors);
	fflush(stdout);
	emit_writes = emit_errors = 0;
}

static void syn(void)
{
	emit(EV_SYN, SYN_REPORT, 0);
}

static void sleep_ms(long ms)
{
	struct timespec ts;
	ts.tv_sec = ms / 1000;
	ts.tv_nsec = (ms % 1000) * 1000000L;
	while (nanosleep(&ts, &ts) == -1 && errno == EINTR) {
	}
}

static int setup_device(int max_x, int max_y)
{
	fd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
	if (fd < 0) {
		perror("open /dev/uinput");
		return -1;
	}
	ioctl(fd, UI_SET_EVBIT, EV_KEY);
	ioctl(fd, UI_SET_EVBIT, EV_ABS);
	ioctl(fd, UI_SET_EVBIT, EV_SYN);
	ioctl(fd, UI_SET_KEYBIT, BTN_TOUCH);
	ioctl(fd, UI_SET_ABSBIT, ABS_MT_SLOT);
	ioctl(fd, UI_SET_ABSBIT, ABS_MT_TRACKING_ID);
	ioctl(fd, UI_SET_ABSBIT, ABS_MT_POSITION_X);
	ioctl(fd, UI_SET_ABSBIT, ABS_MT_POSITION_Y);
	ioctl(fd, UI_SET_ABSBIT, ABS_X);
	ioctl(fd, UI_SET_ABSBIT, ABS_Y);
	ioctl(fd, UI_SET_PROPBIT, INPUT_PROP_DIRECT);

	struct uinput_abs_setup ax = {0}, ay = {0}, aslot = {0}, atid = {0};
	struct uinput_abs_setup aax = {0}, aay = {0};
	ax.code = ABS_MT_POSITION_X;  ax.absinfo.minimum = 0; ax.absinfo.maximum = max_x;
	ay.code = ABS_MT_POSITION_Y;  ay.absinfo.minimum = 0; ay.absinfo.maximum = max_y;
	aax.code = ABS_X;             aax.absinfo.minimum = 0; aax.absinfo.maximum = max_x;
	aay.code = ABS_Y;             aay.absinfo.minimum = 0; aay.absinfo.maximum = max_y;
	aslot.code = ABS_MT_SLOT;     aslot.absinfo.maximum = 9;
	atid.code = ABS_MT_TRACKING_ID; atid.absinfo.maximum = 65535;
	ioctl(fd, UI_ABS_SETUP, &ax);
	ioctl(fd, UI_ABS_SETUP, &ay);
	ioctl(fd, UI_ABS_SETUP, &aax);
	ioctl(fd, UI_ABS_SETUP, &aay);
	ioctl(fd, UI_ABS_SETUP, &aslot);
	ioctl(fd, UI_ABS_SETUP, &atid);

	struct uinput_user_dev udev;
	memset(&udev, 0, sizeof(udev));
	snprintf(udev.name, sizeof(udev.name), "sdinput");
	/* 这个 legacy 结构在 UI_DEV_CREATE 时仍会被内核采用，而我们原来 memset 成 0
	 * 就等于把每个轴的 absmax 写成 0 —— 于是设备对外宣告"坐标范围 0..0"，
	 * 所有触摸坐标都被夹到 0，合成器发出来的 wl_touch.down 永远是 x=0|y=0
	 * （2026-10-27 真机实测：native 侧 SDINPUT=touch_down|match=1|x=0|y=0）。
	 * UI_ABS_SETUP 也设了，但两处都要对，legacy 结构不能留 0。 */
	udev.absmin[ABS_MT_POSITION_X] = 0; udev.absmax[ABS_MT_POSITION_X] = max_x;
	udev.absmin[ABS_MT_POSITION_Y] = 0; udev.absmax[ABS_MT_POSITION_Y] = max_y;
	udev.absmin[ABS_X] = 0;              udev.absmax[ABS_X] = max_x;
	udev.absmin[ABS_Y] = 0;              udev.absmax[ABS_Y] = max_y;
	udev.absmin[ABS_MT_SLOT] = 0;        udev.absmax[ABS_MT_SLOT] = 9;
	udev.absmin[ABS_MT_TRACKING_ID] = 0; udev.absmax[ABS_MT_TRACKING_ID] = 65535;
	udev.id.bustype = BUS_VIRTUAL;
	udev.id.vendor = 0x1234;
	udev.id.product = 0x567a;
	udev.id.version = 1;
	if (write(fd, &udev, sizeof(udev)) != (ssize_t)sizeof(udev)) {
		perror("write uinput_user_dev");
	}
	if (ioctl(fd, UI_DEV_CREATE) < 0) {
		perror("UI_DEV_CREATE");
		return -1;
	}
	/* 等合成器认到新设备。
	 *
	 * 实测（2026-10-27 真机）：Lipstick **确实**会热插拔打开我们新建的 event 节点
	 * （/proc/<lipstick>/fd 里能看到新 eventN），但从 UI_DEV_CREATE 到它真正 open
	 * 需要几百毫秒。原先只等 350 ms，tap 的按下/抬起在这个窗口里就发完了，事件被
	 * 丢在没有读者的设备上——表现就是"注入成功、屏幕毫无反应"，而且注入器自己还
	 * 打印了一行 SDINPUT=tap（它只证明注入了，不证明送达）。
	 * 所以这里把冷静期拉长到 1200 ms，宁可测试慢一点，也不要静默无效的输入。 */
	sleep_ms(1200);
	return 0;
}

static void teardown_device(void)
{
	if (fd >= 0) {
		ioctl(fd, UI_DEV_DESTROY);
		close(fd);
		fd = -1;
	}
}

/* 顺序是有语义的，不是随便排的。
 *
 * 实测（2026-10-27 真机）：原来是 TRACKING_ID 先写、坐标后写，结果合成器在
 * 槽位被激活那一刻就用当时的坐标（0,0）发出 wl_touch.down —— 我们的 runtime
 * 收到的 touch_down 就是 x=0|y=0（native 侧 SDINPUT 日志），于是点击永远打在
 * 屏幕左上角，看起来像"输入没生效"。
 * MT protocol B 的正确顺序：先摆好坐标（含 ABS_X/ABS_Y 单点兼容），再写
 * TRACKING_ID 激活槽位，最后才 BTN_TOUCH 按下，同一批 SYN_REPORT 内提交。 */
static void touch_down(int x, int y, int id)
{
	emit(EV_ABS, ABS_MT_SLOT, 0);
	emit(EV_ABS, ABS_MT_POSITION_X, x);
	emit(EV_ABS, ABS_MT_POSITION_Y, y);
	emit(EV_ABS, ABS_X, x);
	emit(EV_ABS, ABS_Y, y);
	emit(EV_ABS, ABS_MT_TRACKING_ID, id);
	emit(EV_KEY, BTN_TOUCH, 1);
	syn();
}

static void touch_move(int x, int y)
{
	emit(EV_ABS, ABS_MT_POSITION_X, x);
	emit(EV_ABS, ABS_MT_POSITION_Y, y);
	emit(EV_ABS, ABS_X, x);
	emit(EV_ABS, ABS_Y, y);
	syn();
}

static void touch_up(void)
{
	emit(EV_KEY, BTN_TOUCH, 0);
	emit(EV_ABS, ABS_MT_SLOT, 0);
	emit(EV_ABS, ABS_MT_TRACKING_ID, -1);
	syn();
}

static int do_swipe(int x1, int y1, int x2, int y2, int duration_ms, int steps)
{
	if (steps < 2) steps = 2;
	long per = duration_ms / steps;
	if (per < 1) per = 1;
	touch_down(x1, y1, 100);
	for (int i = 1; i <= steps; i++) {
		int x = x1 + (int)((long)(x2 - x1) * i / steps);
		int y = y1 + (int)((long)(y2 - y1) * i / steps);
		touch_move(x, y);
		sleep_ms(per);
	}
	touch_up();
	return 0;
}

/* 把 "tap 791 1900" / "swipe x1 y1 x2 y2 dur steps" / "press x y ms" 解析并执行。
 * 返回 0 成功，非 0 表示该步参数错误。strtok 会就地改字符串，调用方给副本。 */
static int run_one(char *spec)
{
	char *save = NULL;
	char *tok = strtok_r(spec, " \t", &save);
	if (!tok) return 0;
	int a[6], n = 0;
	char *p;
	while ((p = strtok_r(NULL, " \t", &save)) != NULL && n < 6) a[n++] = atoi(p);

	if (!strcmp(tok, "tap")) {
		if (n < 2) { fprintf(stderr, "seq: tap 需要 X Y\n"); return 2; }
		int hold = n > 2 ? a[2] : 60;
		touch_down(a[0], a[1], 100);
		sleep_ms(hold);
		touch_up();
		printf("SDINPUT=tap|x=%d|y=%d|hold=%d|seq=1\n", a[0], a[1], hold);
		report("tap");
	} else if (!strcmp(tok, "press")) {
		if (n < 2) { fprintf(stderr, "seq: press 需要 X Y\n"); return 2; }
		int hold = n > 2 ? a[2] : 600;
		touch_down(a[0], a[1], 100);
		sleep_ms(hold);
		touch_up();
		printf("SDINPUT=press|x=%d|y=%d|hold=%d|seq=1\n", a[0], a[1], hold);
		report("press");
	} else if (!strcmp(tok, "swipe")) {
		if (n < 4) { fprintf(stderr, "seq: swipe 需要 X1 Y1 X2 Y2\n"); return 2; }
		int dur = n > 4 ? a[4] : 400;
		int steps = n > 5 ? a[5] : 24;
		do_swipe(a[0], a[1], a[2], a[3], dur, steps);
		printf("SDINPUT=swipe|x1=%d|y1=%d|x2=%d|y2=%d|dur=%d|steps=%d|seq=1\n",
		       a[0], a[1], a[2], a[3], dur, steps);
		report("swipe");
	} else if (!strcmp(tok, "sleep")) {
		sleep_ms(n > 0 ? a[0] : 1000);
		printf("SDINPUT=sleep|ms=%d|seq=1\n", n > 0 ? a[0] : 1000);
	} else {
		fprintf(stderr, "seq: 未知动作 %s\n", tok);
		return 2;
	}
	return 0;
}

int main(int argc, char **argv)
{
	if (argc < 2) {
		fprintf(stderr, "用法:\n  %s tap X Y [按住ms]\n  %s swipe X1 Y1 X2 Y2 [时长ms] [步数]\n  %s press X Y ms\n  %s seq 'tap 791 1900; tap 1005 152'\n  %s serve            （stdin 逐行读动作，一个设备跑完整段）\n  %s hold MS          （只建设备、等 MS 毫秒、销毁；用于热插拔二分）\n",
		        argv[0], argv[0], argv[0], argv[0], argv[0], argv[0]);
		return 2;
	}
	const char *mode = argv[1];
	int sx = 1080, sy = 2160;
	if (setup_device(sx, sy) < 0) return 3;

	/* serve：一个 uinput 设备跑完整个脚本。
	 *
	 * 为什么要有它（2026-10-27 真机事故）：lipstick 在 05:15:54 和 06:54:38
	 * 各 SIGSEGV 一次，第二次崩溃前 1 秒正是
	 *   lipstick[56530]: evdevtouch: Could not read from input device
	 * 而 dmesg 里 `input: sdinput as /devices/virtual/input/input30N` 的间隔
	 * 正好等于我们每次 `sd.sh input` 的节奏 —— 一次调用建一个设备、发完就拆，
	 * 让 lipstick 的 evdevtouch 插件反复经历热插拔。把"每次手势一个设备"
	 * 降到"每段会话一个设备"，是我们在不改系统、不改合成器的前提下能做的最
	 * 直接削减。 */
	if (!strcmp(mode, "serve")) {
		char *line = NULL;
		size_t cap = 0;
		ssize_t len;
		int rc = 0;
		printf("SDINPUT=serve_ready|pid=%d\n", (int)getpid());
		fflush(stdout);
		while ((len = getline(&line, &cap, stdin)) > 0) {
			while (len > 0 && (line[len - 1] == '\n' || line[len - 1] == '\r' ||
			                   line[len - 1] == ' ' || line[len - 1] == '\t'))
				line[--len] = 0;
			char *p = line;
			while (*p == ' ' || *p == '\t') p++;
			if (!*p || *p == '#') continue;
			if (!strcmp(p, "quit") || !strcmp(p, "exit")) break;
			printf("SDINPUT=serve_step|spec=%s\n", p);
			fflush(stdout);
			char *copy = strdup(p);
			if (!copy) { rc = 3; break; }
			int r = run_one(copy);
			free(copy);
			fflush(stdout);
			if (r) { rc = r; break; }
		}
		free(line);
		printf("SDINPUT=serve_done|rc=%d\n", rc);
		fflush(stdout);
		sleep_ms(120);
		teardown_device();
		return rc;
	}

	/* hold：只建设备、等一会儿、再销毁，不发任何事件。
	 * 用来把「热插拔本身」和「触摸事件」分成两个变量（见 lipstick SEGV 二分）。 */
	if (!strcmp(mode, "hold")) {
		int ms = argc > 2 ? atoi(argv[2]) : 3000;
		printf("SDINPUT=hold|ms=%d|pid=%d\n", ms, (int)getpid());
		fflush(stdout);
		sleep_ms(ms);
		teardown_device();
		printf("SDINPUT=hold_done|ms=%d\n", ms);
		fflush(stdout);
		return 0;
	}

	int rc = 0;
	if (!strcmp(mode, "seq")) {
		if (argc < 3) { teardown_device(); return 2; }
		char *buf = strdup(argv[2]);
		if (!buf) { teardown_device(); return 3; }
		char *save = NULL;
		for (char *g = strtok_r(buf, ";", &save); g; g = strtok_r(NULL, ";", &save)) {
			while (*g == ' ' || *g == '\t') g++;
			if (!*g) continue;
			printf("SDINPUT=seq_step|spec=%s\n", g);
			fflush(stdout);
			int r = run_one(g);
			if (r) { rc = r; break; }
			fflush(stdout);
		}
		free(buf);
		printf("SDINPUT=seq_done|rc=%d\n", rc);
		fflush(stdout);
		sleep_ms(120);
		teardown_device();
		return rc;
	}
	if (argc < 4) {
		teardown_device();
		fprintf(stderr, "用法: %s tap X Y [按住ms] | swipe X1 Y1 X2 Y2 [时长ms] [步数] | press X Y ms | seq '...'\n", argv[0]);
		return 2;
	}
	if (!strcmp(mode, "tap")) {
		int x = atoi(argv[2]), y = atoi(argv[3]);
		int hold = argc > 4 ? atoi(argv[4]) : 60;
		touch_down(x, y, 100);
		sleep_ms(hold);
		touch_up();
		printf("SDINPUT=tap|x=%d|y=%d|hold=%d\n", x, y, hold);
		report("tap");
	} else if (!strcmp(mode, "press")) {
		int x = atoi(argv[2]), y = atoi(argv[3]);
		int hold = argc > 4 ? atoi(argv[4]) : 600;
		touch_down(x, y, 100);
		sleep_ms(hold);
		touch_up();
		printf("SDINPUT=press|x=%d|y=%d|hold=%d\n", x, y, hold);
		report("press");
	} else if (!strcmp(mode, "swipe")) {
		if (argc < 6) { fprintf(stderr, "swipe 需要 4 个坐标\n"); teardown_device(); return 2; }
		int x1 = atoi(argv[2]), y1 = atoi(argv[3]);
		int x2 = atoi(argv[4]), y2 = atoi(argv[5]);
		int dur = argc > 6 ? atoi(argv[6]) : 400;
		int steps = argc > 7 ? atoi(argv[7]) : 24;
		rc = do_swipe(x1, y1, x2, y2, dur, steps);
		printf("SDINPUT=swipe|x1=%d|y1=%d|x2=%d|y2=%d|dur=%d|steps=%d\n",
		       x1, y1, x2, y2, dur, steps);
		report("swipe");
	} else {
		fprintf(stderr, "未知模式 %s\n", mode);
		rc = 2;
	}
	fflush(stdout);
	sleep_ms(120);
	teardown_device();
	return rc;
}
