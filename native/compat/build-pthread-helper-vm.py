#!/usr/bin/env python3
"""Build a process-private fix without modifying the nested translator checkout."""
from pathlib import Path
import argparse,hashlib,json,subprocess
p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
repo=Path(__file__).resolve().parents[2];source=repo/'third_party/bionic_translation/pthread_wrapper/libpthread.c'
original=source.read_text();needle='#define INIT_IF_NOT_MAPPED(x, init) do { if (!IS_MAPPED(x)) init(x); } while(0)'
assert original.count(needle)==1,'Review the upstream lazy-init implementation before applying the fix'
replacement='''/* All lazy readers synchronize with initialization, including the interval
 * after the native pointer is assigned but before its initializer is copied.
 * A mapped pointer alone is not evidence that the object is ready. Never hold
 * this guard while actually locking/waiting on an application primitive. */
static pthread_mutex_t static_init_guard = PTHREAD_MUTEX_INITIALIZER;
#define INIT_IF_NOT_MAPPED(x, init) do { \\
    pthread_mutex_lock(&static_init_guard); \\
    if (!IS_MAPPED(x)) init(x); \\
    pthread_mutex_unlock(&static_init_guard); \\
} while(0)'''
patched=original.replace(needle,replacement);generated=a.output/'libpthread.c';generated.write_text(patched)
library=a.output/'libpthread_bio.so.0'
subprocess.run(['gcc','-shared','-fPIC','-O2','-D_GNU_SOURCE','-fno-exceptions','-Wl,-soname,libpthread_bio.so.0','-Wl,--no-as-needed','-o',str(library),str(generated),'-ldl','-lpthread'],check=True)
record=dict(source=str(source.relative_to(repo)),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),patched_source_sha256=hashlib.sha256(patched.encode()).hexdigest(),library_sha256=hashlib.sha256(library.read_bytes()).hexdigest())
(a.output/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');print('PTHREAD_STATIC_INIT=compiled|sha256='+record['library_sha256'])
