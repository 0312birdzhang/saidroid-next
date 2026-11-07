/* throwwatch —— 拦截 __cxa_throw，只在指定异常类型出现时打印符号化栈。
 * 用法：LD_PRELOAD=/tmp/ap/libthrowwatch.so SD_THROW_WATCH=out_of_range ./prog
 * 比 gdb 可靠的场合：被杀进程、或 gdb 拿不到 C++ 运行时符号时。
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <execinfo.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

typedef void (*throw_fn)(void *, void *, void (*)(void *));

extern void *__cxa_begin_catch(void *);
extern void __cxa_end_catch(void);

static throw_fn real_throw;
static const char *watch;
static int in_watch;

static void dump(void *obj, const char *name)
{
	void *bt[48];
	int n;

	fprintf(stderr, "\n=== throwwatch: %s ===\n", name);
	/* std::logic_error 的 what() 串在对象 + sizeof(void*) 处（紧跟 vptr） */
	if (strstr(name, "logic_error") || strstr(name, "out_of_range") ||
	    strstr(name, "range_error") || strstr(name, "runtime_error") ||
	    strstr(name, "invalid_argument") || strstr(name, "length_error")) {
		char **msg = (char **)((char *)obj + sizeof(void *));
		fprintf(stderr, "what: %s\n", *msg ? *msg : "(null)");
	}
	n = backtrace(bt, 48);
	backtrace_symbols_fd(bt, n, fileno(stderr));
	fprintf(stderr, "=== end throwwatch ===\n");
	fflush(stderr);
}

/* 没有能用的下划线变体时，至少保证不打断 __cxa_throw 语义 */
void __cxa_throw(void *obj, void *tinfo, void (*dest)(void *))
{
	if (!real_throw) {
		real_throw = (throw_fn)dlsym(RTLD_NEXT, "__cxa_throw");
		if (!real_throw) {
			write(2, "throwwatch: cannot find real __cxa_throw\n", 41);
			abort();
		}
	}
	if (!watch) {
		watch = getenv("SD_THROW_WATCH");
		if (!watch) watch = "out_of_range";
	}
	if (!in_watch) {
		/* type_info 布局：vptr, 然后是 const char* 名字 */
		const char *name = *(const char **)((char *)tinfo + sizeof(void *));
		if (name && strstr(name, watch)) {
			in_watch = 1;
			dump(obj, name);
			in_watch = 0;
		}
	}
	real_throw(obj, tinfo, dest);
}
