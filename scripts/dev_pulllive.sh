export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=10"
$SCP root@bonito:/home/art/live.rgba /tmp/ap/live.rgba
mkdir -p /media/psf/Home/WorkSpace/saidroid-next/build
cp -f /tmp/ap/live.rgba /media/psf/Home/WorkSpace/saidroid-next/build/live.rgba
