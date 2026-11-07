from pathlib import Path
import subprocess,tempfile
header=Path(__file__).with_name('host-worker-identity.hpp').resolve()
with tempfile.TemporaryDirectory(prefix='sd-host-worker-identity-')as directory:
 b=Path(directory);source=b/'test.cpp';source.write_text('#include "'+str(header)+'"\n'+r'''
#include <thread>
#include <atomic>
#include <cassert>
#include <sys/prctl.h>
int main(){prctl(PR_SET_NAME,"app-main-kept");std::atomic<int> stage{0};std::thread host([&](){prctl(PR_SET_NAME,"native-worker");stage=1;while(stage!=2)std::this_thread::yield();char name[16];prctl(PR_GET_NAME,name);assert(!strncmp(name,"sdhost-",7));});while(stage!=1)std::this_thread::yield();assert(sd_label_host_workers()==1);char main_name[16];prctl(PR_GET_NAME,main_name);assert(!strcmp(main_name,"app-main-kept"));stage=2;host.join();std::thread app([](){prctl(PR_SET_NAME,"app-worker-kept");char name[16];prctl(PR_GET_NAME,name);assert(!strcmp(name,"app-worker-kept"));});app.join();puts("HOST_WORKER_IDENTITY=PASS|native-worker-labelled|main-kept|later-app-worker-kept");}
''');subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror','-pthread',str(source),'-o',str(b/'test')],check=True,timeout=30);subprocess.run([str(b/'test')],check=True,timeout=10)
