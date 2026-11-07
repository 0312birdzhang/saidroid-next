#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>

/* Reproduce libhybris's global DATA/function-name collision. */
int (*bionic___system_properties_init)(void);
int saildroid_bionic___system_properties_init(void){return 42;}

int main(int argc,char **argv) {
    if(argc!=3)return 2;
    void *loader=dlopen(argv[1],RTLD_NOW|RTLD_GLOBAL);
    if(!loader){fprintf(stderr,"loader: %s\n",dlerror());return 1;}
    void *(*open_library)(const char *,int)=dlsym(loader,"bionic_dlopen");
    void *(*find_symbol)(void *,const char *)=dlsym(loader,"bionic_dlsym");
    const char *(*load_error)(void)=dlsym(loader,"bionic_dlerror");
    int (*add_path)(const char *)=dlsym(loader,"bionic_add_library_path");
    if(!open_library||!find_symbol||!load_error||!add_path||add_path(argv[2])<0)return 1;
    char file[4096];
    snprintf(file,sizeof(file),"%s/libprovided.so",argv[2]);
    if(!open_library(file,RTLD_NOW)){fprintf(stderr,"provider: %s\n",load_error());return 1;}
    snprintf(file,sizeof(file),"%s/libdependent.so",argv[2]);
    void *dependent=open_library(file,RTLD_NOW);
    if(!dependent){fprintf(stderr,"SONAME dependency: %s\n",load_error());return 1;}
    int (*value)(void)=find_symbol(dependent,"dependent_value");
    if(!value||value()!=42)return 1;
    snprintf(file,sizeof(file),"%s/libpropertyclient.so",argv[2]);
    void *client=open_library(file,RTLD_NOW);
    if(!client){fprintf(stderr,"property client: %s\n",load_error());return 1;}
    value=find_symbol(client,"initialize_properties");
    int (*initialize)(void)=find_symbol(client,"__system_properties_init");
    if(!value||value()!=42||!initialize||initialize()!=42||
            bionic___system_properties_init!=NULL)return 1;
    for(int i=0;i<140;i++) {
        snprintf(file,sizeof(file),"%s/libcapacity%03d.so",argv[2],i);
        void *library=open_library(file,RTLD_NOW);
        if(!library){fprintf(stderr,"capacity at %d: %s\n",i,load_error());return 1;}
        value=find_symbol(library,"capacity_value");
        if(!value||value()!=i){fprintf(stderr,"library identity differs at %d\n",i);return 1;}
    }
    puts("API29_LINKER=PASS|soname=matched|distinct_libraries=143|symbol_identity=verified|hybris_data_collision=isolated");
    return 0;
}
