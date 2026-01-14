#!/bin/bash
# 啟動 Scheduler 到背景執行
# 輸出 log 會被寫入 scheduler.log

echo "🚀 Starting Scheduler in background..."
nohup uv run scheduler.py > scheduler.log 2>&1 &

# 儲存 Process ID 以便之後停止
echo $! > scheduler.pid
echo "✅ Scheduler started! PID: $(cat scheduler.pid)"
echo "📄 Logs: tail -f scheduler.log"
