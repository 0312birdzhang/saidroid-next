from pathlib import Path
import subprocess,shutil,json
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent
subprocess.run(['python3',str(r/'scripts/api29/build-media-player-runtime-vm.py'),'--baseline-classes',str(r/'build/evidence/qq-video-ime311-20261103-v1/runtime-build-v1/classes'),'--baseline-manifest',str(r/'build/evidence/qq-video-ime311-20261103-v1/runtime-build-v1.json'),'--include-window-ime','--include-activity-finish','--output',str(b/'runtime-build-v1')],check=True,timeout=180)
shutil.copyfile(b/'runtime-build-v1/manifest.json',b/'runtime-build-v1.json')
