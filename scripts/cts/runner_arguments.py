"""Translate original host-runner options to their instrumentation arguments.

LibcoreTest's actual CTS 10_r16 host class adds comma-joined core-expectations,
then clears class/method when a test-package is set. No expectation is invented
or added to the original resource list.
"""
from instrumentation_outcome import test_timeout_msec

LIBCORE_RUNNER='com.android.compatibility.testtype.LibcoreTest'

def instrumentation_arguments(runner):
    options=runner.get('options',[])
    args={o['key']:o['value']for o in options if o.get('name')=='instrumentation-arg'}
    for key in ['class','test-package','include-annotation','exclude-annotation']:
        value=next((o['value']for o in options if o.get('name')==key),None)
        if value is not None:args[{'test-package':'package','include-annotation':'annotation','exclude-annotation':'notAnnotation'}.get(key,key)]=value
    if runner.get('class')==LIBCORE_RUNNER:
        expectations=[o['value']for o in options if o.get('name')=='core-expectation']
        if expectations:
            if any(not value.startswith('/')or ','in value or '\x00'in value for value in expectations):
                raise ValueError('Invalid original Libcore expectation resource')
            args['core-expectations']=','.join(expectations)
        if any(o.get('name')=='test-package'for o in options)and any(o.get('name')=='class'for o in options):
            args.pop('class',None)
    args.setdefault('timeout_msec',str(test_timeout_msec(runner)))
    return args
