#include <wayland-client.h>
#include <stdio.h>
#include <string.h>
static void global(void*d,struct wl_registry*r,uint32_t n,const char*i,uint32_t v){(void)d;(void)r;(void)n;printf("%s %u\n",i,v);}
static void removed(void*d,struct wl_registry*r,uint32_t n){(void)d;(void)r;(void)n;}
static const struct wl_registry_listener listener={global,removed};
int main(void){struct wl_display*d=wl_display_connect(NULL);if(!d)return 1;struct wl_registry*r=wl_display_get_registry(d);wl_registry_add_listener(r,&listener,NULL);int result=wl_display_roundtrip(d);wl_registry_destroy(r);wl_display_disconnect(d);return result<0?2:0;}
