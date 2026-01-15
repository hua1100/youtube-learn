#!/bin/bash

# 定義 Log 檔案
LOG_FILE="server.log"

echo "🚀 Starting Server with Auto-Restart..."
echo "ℹ️  Logs will be written to $LOG_FILE"
echo "ℹ️  Press Ctrl+C to stop the loop."

# 無窮迴圈
while true; do
    echo "----------------------------------------"
    echo "⏰ Starting at $(date)"
    
    # 啟動伺服器
    # 注意：這裡不使用 nohup，因為這個腳本本身就會被 nohup 執行
    # 我們假設 run_prod.sh 已經包含了 uv run ...
    # 為了節省資源，我們直接呼叫 python，跳過前端 build (假設已 build 過)
    # 如果您希望每次重啟都重新 build 前端，請改回 ./run_prod.sh
    
    echo "🔥 Launching Python Server..."
    uv run dashboard_server.py >> "$LOG_FILE" 2>&1
    
    EXIT_CODE=$?
    echo "⚠️  Server crashed/stopped with exit code: $EXIT_CODE" >> "$LOG_FILE"
    echo "⚠️  Server crashed! Restarting in 5 seconds..."
    
    # 休息 5 秒避免瘋狂重啟佔用 CPU
    sleep 5
done
