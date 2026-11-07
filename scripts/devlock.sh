#!/bin/bash
# SailDroid 设备占用锁：同一台手机上同一时刻只允许一个 ART 实例在跑。
#
# 用法：
#   scripts/devlock.sh acquire [超时秒] [标签]   # 拿不到就非 0 退出；标签写进 owner 便于归因
#   scripts/devlock.sh release [标签]           # 只释放自己这把（按 owner 标签校验）
#   scripts/devlock.sh release --force          # 强行清掉（确认对方已死才用）
#   scripts/devlock.sh status                   # 谁持锁、持了多久
#
# 归属：owner 文件内容为 "<标签>|<hostname>|<pid>|<epoch>"。标签建议传自己名字
#       （sd-runtime / sd-webview / sd-integration / lead），否则归因不出来。
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"

# 2026-10-27 事故：在 Mac 宿主上跑本脚本时没有 sshpass，每次 ssh 都失败，
# 于是 status 一律打印 LOCK_FREE、release 一律打印 LOCK_RELEASED，锁其实没动过。
# 任何人都可能据此误判"锁空着"然后抢设备。缺工具/连不上时必须是 UNKNOWN，不许假装 FREE。
if ! command -v sshpass >/dev/null 2>&1; then
  echo "LOCK_UNKNOWN reason=no_sshpass (本脚本必须在 Parallels VM 里跑；Mac 宿主没有 sshpass)"
  exit 3
fi
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
LOCK=/home/art/test/.device-lock

# 连不上设备也必须是 UNKNOWN：chmod/网络/设备睡眠都会让 ssh 失败。
if ! $SSH true >/dev/null 2>&1; then
  echo "LOCK_UNKNOWN reason=ssh_unreachable (root@bonito 不可达)"
  exit 3
fi
cmd=${1:-status}
wait=${2:-0}
label=${3:-${DEVLOCK_LABEL:-unnamed}}
stamp="$(hostname)|$$|$(date +%s)"
token="${label}|$(hostname)|$$|$(date +%s)"

case "$cmd" in
acquire)
  end=$(( $(date +%s) + wait ))
  while :; do
    # 关键：以 mkdir 的退出码判定归属。mkdir 成功才写 owner 并回 GOT；
    # 目录已存在说明别人持锁（老版本这里会误报 LOCK_ACQUIRED，等于没锁）。
    out=$($SSH "if mkdir '$LOCK' 2>/dev/null; then printf '%s' '$token' > '$LOCK/owner'; echo GOT; else echo BUSY; fi" 2>/dev/null)
    if [ "$out" = "GOT" ]; then
      echo "LOCK_ACQUIRED owner=$token"
      exit 0
    fi
    if [ "$wait" -le 0 ] || [ "$(date +%s)" -ge "$end" ]; then
      echo "LOCK_BUSY holder=$($SSH "cat '$LOCK/owner' 2>/dev/null" 2>/dev/null)"
      exit 1
    fi
    sleep 3
  done
  ;;
release)
  if [ "${2:-}" = "--force" ] || [ "${wait:-0}" = "--force" ]; then
    $SSH "rm -rf '$LOCK'" >/dev/null 2>&1
    echo "LOCK_FORCE_RELEASED"
    exit 0
  fi
  rel_label=${2:-$label}
  cur=$($SSH "cat '$LOCK/owner' 2>/dev/null" 2>/dev/null)
  cur_label=${cur%%|*}
  if [ -z "$cur" ]; then
    echo "LOCK_ALREADY_FREE"
    exit 0
  fi
  if [ "$cur_label" = "$rel_label" ]; then
    $SSH "rm -rf '$LOCK'" >/dev/null 2>&1
    echo "LOCK_RELEASED owner=$cur"
    exit 0
  fi
  echo "LOCK_NOT_MINE holder=$cur label=$rel_label (确认对方已死再用 release --force)"
  exit 1
  ;;
status)
  if $SSH "test -d '$LOCK'" >/dev/null 2>&1; then
    cur=$($SSH "cat '$LOCK/owner' 2>/dev/null" 2>/dev/null)
    held=${cur##*|}
    case "$held" in
      ''|*[!0-9]*) held="" ;;
    esac
    if [ -n "$held" ]; then
      age=$(( $(date +%s) - held ))
      echo "LOCK_HELD by: $cur age=${age}s"
    else
      echo "LOCK_HELD by: (无 owner 文件，可能是异常残留)"
    fi
  else
    echo "LOCK_FREE"
  fi
  ;;
*)
  echo "用法: $0 acquire [超时秒] [标签] | release [标签|--force] | status"
  exit 2
  ;;
esac
