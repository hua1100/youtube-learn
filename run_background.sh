#!/bin/bash
# 啟動 Scheduler 到背景執行
# 輸出 log 會被寫入 scheduler.log

if [ -f scheduler.pid ]; then
    PID=$(cat scheduler.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️ Scheduler is already running (PID: $PID)."
        exit 0
    fi
fi

echo "🚀 Starting Scheduler in background..."
export PYTHONUNBUFFERED=1
nohup uv run scheduler.py > scheduler.log 2>&1 &

# 儲存 Process ID 以便之後停止
echo $! > scheduler.pid
echo "✅ Scheduler started! PID: $(cat scheduler.pid)"
echo "📄 Logs: tail -f scheduler.log"
