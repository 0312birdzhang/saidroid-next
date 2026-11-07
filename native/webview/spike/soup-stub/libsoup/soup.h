/* Compile-only stub for libsoup-3.0.
 *
 * The device ships WPE WebKit headers (which include <libsoup/soup.h>) but not
 * the libsoup development headers. The WPE headers only reference two opaque
 * soup types, and this spike never calls a libsoup function, so forward
 * declarations are enough. Nothing here is linked or executed. */
#ifndef SD_SOUP_STUB_H
#define SD_SOUP_STUB_H

#include <glib.h>
#include <gio/gio.h>

typedef struct _SoupCookie SoupCookie;
typedef struct _SoupMessageHeaders SoupMessageHeaders;

#endif
