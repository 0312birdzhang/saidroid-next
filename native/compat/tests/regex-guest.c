#include <stddef.h>
#include <sys/types.h>
struct android_regex {int magic;size_t nsub;const char *end;void *guts;};
struct android_match {ssize_t start,end;};
extern int regcomp(struct android_regex*,const char*,int);
extern int regexec(const struct android_regex*,const char*,size_t,struct android_match*,int);
extern void regfree(struct android_regex*);
/* An Android-style ELF with unresolved libc imports goes through the real
 * compatibility linker's symbol selection, not direct calls to our adapter. */
int regex_guest_check(void){
    for(int i=0;i<500;i++){
        struct android_regex regex={0};struct android_match matches[2];
        if(regcomp(&regex,"(ab)+",1))return 1;
        int error=regexec(&regex,"xxababyy",2,matches,0);
        int valid=regex.nsub==1&&!error&&matches[0].start==2&&matches[0].end==6&&matches[1].start==4&&matches[1].end==6;
        regfree(&regex);if(!valid)return 2;
    }return 0;
}
