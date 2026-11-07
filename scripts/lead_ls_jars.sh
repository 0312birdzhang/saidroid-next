export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
sshpass -e ssh -o StrictHostKeyChecking=no root@bonito "ls -la /home/art/java/dex/art/ 2>/dev/null | head -20; echo ---; ls /home/art/api29-root/ 2>/dev/null | head -20"
