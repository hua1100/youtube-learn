#!/bin/bash
# 停止背景執行的 Scheduler

if [ -f scheduler.pid ]; then
    PID=$(cat scheduler.pid)
    if ps -p $PID > /dev/null; then
        echo "🛑 Stopping Scheduler (PID: $PID)..."
        kill $PID
        rm scheduler.pid
        echo "✅ Scheduler stopped."
    else
        echo "⚠️ Process $PID not found. Cleaning up pid file."
        rm scheduler.pid
    fi
else
    echo "⚠️ No scheduler.pid file found. Is it running?"
fi
