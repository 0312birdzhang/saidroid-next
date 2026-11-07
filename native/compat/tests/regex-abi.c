#define _GNU_SOURCE
#include <assert.h>
#include <dlfcn.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <signal.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <unistd.h>
struct android_regex {int magic;size_t nsub;const char *end;void *guts;};
struct android_match {ssize_t start,end;};
static int(*compile)(struct android_regex*,const char*,int);
static int(*execute)(const struct android_regex*,const char*,size_t,struct android_match*,int);
static void(*release)(struct android_regex*);
static size_t(*message)(int,const struct android_regex*,char*,size_t);
static void *worker(void *unused){
    (void)unused;
    for(int i=0;i<500;i++){
        struct android_regex regex={0};struct android_match matches[3];
        assert(compile(&regex,"(hello) (world)",1|2)==0&&regex.nsub==2);
        assert(execute(&regex,"xxHELLO WORLDzz",3,matches,0)==0);
        assert(matches[0].start==2&&matches[0].end==13&&matches[1].start==2&&matches[1].end==7&&matches[2].start==8&&matches[2].end==13);
        release(&regex);
    }return NULL;
}
int main(int argc,char **argv){
    assert(argc==2||argc==3);void *library=dlopen(argv[1],RTLD_NOW|RTLD_GLOBAL);assert(library);
    compile=dlsym(library,"bionic_regcomp");execute=dlsym(library,"bionic_regexec");release=dlsym(library,"bionic_regfree");message=dlsym(library,"bionic_regerror");assert(compile&&execute&&release&&message);
    long page=sysconf(_SC_PAGESIZE);char *area=mmap(NULL,page*4,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);assert(area!=MAP_FAILED);assert(!mprotect(area+page,page,PROT_NONE)&&!mprotect(area+page*3,page,PROT_NONE));
    struct android_regex *regex=(void*)(area+page-sizeof(*regex));struct android_match *matches=(void*)(area+page*3-3*sizeof(*matches));
    // Negative control: glibc's object writes exceed Android's32-byte object.
    int negative=!getenv("REGEX_SKIP_NEGATIVE");
    if(negative){
        pid_t child=fork();assert(child>=0);
        if(child==0){int(*wrong)(struct android_regex*,const char*,int)=dlsym(RTLD_DEFAULT,"regcomp");wrong(regex,"(ab)",1);_exit(90);}
        int status;assert(waitpid(child,&status,0)==child&&WIFSIGNALED(status)&&WTERMSIG(status)==SIGSEGV);
    }
    memset(regex,0,sizeof(*regex));assert(compile(regex,"(hello) (world)",1|2)==0&&regex->nsub==2);
    matches[0]=(struct android_match){2,13};assert(execute(regex,"xxHELLO WORLDzz",3,matches,4)==0);assert(matches[0].start==2&&matches[0].end==13);release(regex);
    assert(compile(regex,"^b$",1|8)==0);assert(execute(regex,"a\nb\nc",3,matches,0)==0&&matches[0].start==2&&matches[0].end==3);release(regex);
    assert(compile(regex,"hello",4)==0);matches[0]=(struct android_match){-123,-456};assert(execute(regex,"hello",3,matches,0)==0&&matches[0].start==-123&&matches[0].end==-456);release(regex);
    const char pattern[]="(ab)ignored";regex->end=pattern+4;assert(compile(regex,pattern,1|32)==0);assert(execute(regex,"ab",3,matches,0)==0);release(regex);
    assert(compile(regex,".[*+?",16)==0);assert(execute(regex,".[*+?",3,matches,0)==0);release(regex);
    assert(compile(regex,"hello",1)==0);assert(execute(regex,"other",3,matches,0)==1);release(regex);
    assert(compile(regex,"[",1)!=0);char error[5];assert(message(7,regex,error,sizeof(error))>sizeof(error)&&error[4]==0);release(regex);
    regex->end="REG_EBRACK";char numeric[8];message(255,regex,numeric,sizeof(numeric));assert(!strcmp(numeric,"7"));
    pthread_t threads[4];for(int i=0;i<4;i++)assert(!pthread_create(&threads[i],NULL,worker,NULL));for(int i=0;i<4;i++)assert(!pthread_join(threads[i],NULL));
    if(argc==3){
        assert(dlopen("libpthread_bio.so.0",RTLD_NOW|RTLD_GLOBAL));
        assert(dlopen("libc_bio.so.0",RTLD_NOW|RTLD_GLOBAL));
        void *linker=dlopen("libdl_bio.so.0",RTLD_NOW|RTLD_GLOBAL);assert(linker);
        void*(*open_guest)(const char*,int)=dlsym(linker,"bionic_dlopen");
        void*(*symbol)(void*,const char*)=dlsym(linker,"bionic_dlsym");assert(open_guest&&symbol);
        void(*parse)(const char*,const char*)=dlsym(linker,"dl_parse_library_path");assert(parse);
        char *directory=strdup(argv[2]);assert(directory);char *slash=strrchr(directory,'/');assert(slash);*slash=0;parse(directory,":");free(directory);
        void *guest=open_guest(argv[2],RTLD_NOW);assert(guest);int(*check)(void)=symbol(guest,"regex_guest_check");assert(check&&check()==0);
        puts("API29_REGEX_GUEST=PASS|loader=bionic|symbols=regcomp-regexec-regfree");
    }
    munmap(area,page*4);printf("API29_REGEX_ABI=PASS|legacy_guard_fault=%s|android_object=32|android_offsets=64bit|flags=translated|startend=verified|threads=4|cycles=2000\n",negative?"reproduced":"skipped");return 0;
}
