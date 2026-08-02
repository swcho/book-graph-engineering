#!/usr/bin/env bash
# 프로세스를 실제로 죽였다가 이어서 돌리는 시연
set -u
cd "$(dirname "$0")"
rm -f ckpt.sqlite

echo "=== 1회차: 3번째 노드(결제)에서 죽인다 ==="
CRASH_AT=3 python3 ex1_crash_resume.py
echo "   종료 코드 $?"

echo
echo "=== 2회차: 그냥 다시 돌린다 ==="
python3 ex1_crash_resume.py
