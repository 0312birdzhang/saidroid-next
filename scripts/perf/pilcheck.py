try:
    import PIL, sys
    print('VM_PIL', PIL.__version__, sys.version.split()[0])
except Exception as e:
    print('VM_PIL_MISSING', e)
