# YouTube Learning Dashboard

這是一個全自動的 YouTube 學習儀表板，具備以下功能：
1.  **自動監控**：每 4 小時自動檢查指定 YouTube 頻道的新影片。
2.  **AI 摘要**：自動下載逐字稿並使用 AI 生成摘要（支援 OpenAI, Gemini 等）。
3.  **精美介面**：Mac 風格的儀表板，支援即時更新與搜尋。
4.  **自動部署**：支援一鍵部署到 Zeabur。

## 快速開始

### 1. 本地運行 (Production Mode)

```bash
# 只要這一行，自動編譯前端 + 啟動後端
./run_prod.sh
```
啟動後訪問：`http://localhost:8000`

### 2. 環境變數設定 (.env)

複製 `.env.example` 為 `.env` 並填入：

```ini
# OpenAI 範例
LLM_API_KEY=sk-xxxx
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o

# Google Gemini 範例
# LLM_API_KEY=AIzrB... (您的 Gemini API Key)
# LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
# LLM_MODEL=gemini-1.5-flash
```

## 部署到 Zeabur

1.  **Push** 本專案到 GitHub。
2.  在 Zeabur 建立專案並連結 GitHub Repo。
3.  設定環境變數：
    *   `LLM_API_KEY`: API 金鑰
    *   `LLM_BASE_URL`: API 網址
    *   `LLM_MODEL`: 模型名稱 (預設 gpt-4o)
    *   **HTTPS_PROXY** (選填): 如果遇到 YouTube 阻擋 (IP Block)，請填入代理伺服器網址 (例如 `http://user:pass@proxy.com:port`)。

## 常見問題

### 逐字稿被 YouTube 封鎖 (IP Block)
如果部署在 Zeabur/AWS/GCP 等雲端平台，YouTube 會封鎖其 IP。
解決方案：購買 Residence Proxy (住宅代理) 或 Smart Proxy，並在環境變數設定 `HTTPS_PROXY`。
