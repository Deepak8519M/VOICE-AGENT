# 🎙️ NovaFlow AI Voice Agent

NovaFlow AI Voice Agent is a **web-based conversational AI application** developed as part of the **30 Days of AI Voice Agents challenge (Day 29: Final Documentation)**.

It integrates **real-time speech-to-text transcription, text-to-speech synthesis, generative AI responses, and web search capabilities** to provide a seamless voice and text interaction experience.

Built with **⚡ FastAPI, 🎤 AssemblyAI, 🤖 Google Gemini, 🔊 Murf AI, and 🌐 Tavily**, NovaFlow supports features like **file uploads for knowledge base integration, chat history, customizable settings, and deployment on Render**.

---

## ✨ Features

* 🎤 **Real-Time Voice Interaction**: Capture audio via browser microphone, transcribe with AssemblyAI (RealtimeTranscriber), generate AI responses with Gemini, and convert to speech via Murf AI.
* 💬 **Text-Based Interaction**: Send text queries and receive AI-generated responses.
* 📚 **Knowledge Base Integration**: Upload **PDF/TXT** files for summaries or references (e.g., *“Summarize myfile.pdf”*).
* 🔎 **Web Search**: Real-time search via **Tavily API** using queries like *search, find, look up*.
* 🗂️ **Chat History**: Save, retrieve, create, and clear conversations.
* ⚙️ **Customizable Settings**: Configure **voice ID, speed, style, microphone sensitivity, audio quality, theme, and accent color**.
* 📧 **Email Integration**: Send responses/summaries via **Zapier webhooks**.
* 🔔 **Audio Feedback**: Start/Stop sound alerts (`start.mp3`, `stop.mp3`).
* 🎨 **Responsive UI**: Dark theme, spinner for loading, fixed Stop button, favicon.
* ☁️ **Deployment**: Hosted on **Render** for scalable access.

---

## 📂 Folder Structure

```
VOICEAGENT/
│
├── main.py                 # ⚡ FastAPI backend (WebSocket transcription)
├── requirements.txt        # 📦 Python dependencies
├── .env                    # 🔑 API keys & secrets
├── static/                 # 🎨 Static assets
│   ├── index.js            # Frontend logic
│   ├── style.css           # UI styles
│   ├── settings.js         # Settings logic
│   ├── favicon.ico         # App icon
│   ├── start.mp3           # 🎵 Start sound
│   └── stop.mp3            # 🎵 Stop sound
├── templates/              # 🖼️ HTML templates
│   ├── index.html          # Main app page
│   ├── home.html           # Landing page
│   ├── docs.html           # Documentation page
│   └── settings.html       # Settings page
├── uploads/                # 📂 Uploaded files + chat history
│   ├── knowledge_base/     # PDFs/TXTs + extracted text
│   └── chats/              # 💬 JSON chat history
└── settings.json           # ⚙️ User settings
```

---

## 🛠️ Prerequisites

* 🐍 **Python 3.12** (backend)
* 🌐 **Node.js (optional)** (frontend dev)
* 🔑 **API Keys**:

  * 📝 AssemblyAI → `AAI_API_KEY`
  * 🤖 Google Gemini → `GEMINI_API_KEY`
  * 🔊 Murf AI → `MURF_API_KEY`
  * 🔎 Tavily → `TAVILY_API_KEY`
  * 📧 Zapier Webhook (optional) → `ZAPIER_WEBHOOK_URL`
* 🌍 **Browser**: Chrome / Firefox (WebSocket + WebRTC support)
* ☁️ **Render Account** (deployment)

---

## ⚙️ Setup & Installation

1. **Clone the Repository**

   ```bash
   git clone <your-repository-url>
   cd VOICEAGENT
   ```

2. **Create Virtual Environment**

   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows  
   source venv/bin/activate # macOS/Linux
   ```

3. **Install Dependencies**
   Add to `requirements.txt`:

   ```
   fastapi==0.112.0
   uvicorn==0.30.3
   assemblyai==0.36.0
   google-generativeai==0.8.3
   websockets==12.0
   python-dotenv==1.0.1
   aiohttp==3.9.5
   PyPDF2==3.0.1
   ```

   Install with:

   ```bash
   pip install -r requirements.txt
   ```

4. **Set Environment Variables** → `.env`

   ```
   AAI_API_KEY=your_assemblyai_api_key
   GEMINI_API_KEY=your_gemini_api_key
   MURF_API_KEY=your_murf_api_key
   TAVILY_API_KEY=your_tavily_api_key
   ZAPIER_WEBHOOK_URL=your_zapier_webhook_url
   ```

5. **Create Directories**

   ```bash
   mkdir -p uploads/knowledge_base uploads/chats
   ```

6. **Add Static Files** (`favicon.ico`, `start.mp3`, `stop.mp3`) to `/static`

---

## 🚀 Usage

### ▶️ Run Locally

```bash
uvicorn main:app --reload
```

Open 👉 [http://localhost:8000/app](http://localhost:8000/app)

### 🎤 Voice Interaction

1. Click **Mic Button** 🎙️ (#micBtn)
2. Speak for ≥ 1 sec (*e.g., “Tell me about AI”*)
3. Click **Stop Listening** 🛑 (#stopListening)
4. View transcript + AI response in chat 💬
5. Hear reply via Murf AI 🔊

### 💬 Text Interaction

* Type in **chat input** (#chatInput)
* Click **Send** (#sendBtn)

### 📚 Knowledge Base

* Upload **PDF/TXT** via `/settings`
* Query with: *“Summarize myfile.pdf”*

### 🔎 Web Search

* Queries like: *“search for AI trends”*

### ⚙️ Settings

* Configure **voice, speed, conversation type, mic sensitivity, theme, accent color**
* Enable/disable **search, knowledge base, chat saving**

### 🗂️ Chat History

* View chats at `/chats`
* Create new or clear history

### 📧 Email Integration

* Say *“send to email”* or *“email the summary”* → Zapier

---

## ☁️ Deployment on Render

1. **Push to Git**

   ```bash
   git add .
   git commit -m "Final NovaFlow AI Voice Agent for Day 29"
   git push origin main
   ```

2. **Render Setup**

   * Build Command: `pip install -r requirements.txt`
   * Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   * Add environment variables

3. **Deploy & Monitor Logs** (\~5–10 mins)

4. Access 🌍:

   ```
   https://<your-service>.onrender.com/app
   ```

   Example: `https://novaflow-agent.onrender.com/app`

---

## 🐞 Troubleshooting

* ❌ **ModuleNotFoundError: 'assemblyai.streaming'**

  * Ensure `assemblyai==0.36.0`
  * Import: `from assemblyai import RealtimeTranscriber`
  * Else: downgrade → `0.26.0`

* 🎙️ **Voice Input Issues**

  * Speak > 1 sec
  * Check API key validity
  * Allow mic access

* ⚠️ **UI Errors**

  * Use latest `index.js` (Aug 29, 2025, 20:40 IST)
  * Ensure `favicon.ico`, `start.mp3`, `stop.mp3` exist

* 🌍 **Environment Issues**

  * Activate correct venv
  * Consolidate files to project root

* ☁️ **Render Issues**

  * Check logs
  * Verify `requirements.txt` + `.env`

---

## ⚠️ Known Issues

* ⏱️ **Short Recordings** (<1s) → Error
* 📄 **PDF Extraction**: Some PDFs fail, use TXT fallback
* 🔊 **Murf AI Latency**: Small delays possible

---

## 🤝 Contributing

1. Fork 🍴 the repo
2. Create branch → `git checkout -b feature/your-feature`
3. Commit → `git commit -m "Add your feature"`
4. Push → `git push origin feature/your-feature`
5. Open a PR 🚀

---

## 📜 License

This project is licensed under the **MIT License**.

---

## 🙌 Acknowledgments

* 🎤 **AssemblyAI**: Real-time transcription
* 🤖 **Google Gemini**: Generative AI
* 🔊 **Murf AI**: TTS
* 🔎 **Tavily**: Web search
* ⚡ **FastAPI**: Backend
* ☁️ **Render**: Hosting
* 💡 **30 Days of AI Voice Agents Challenge**: Inspiration

---

## 📬 Contact

💼 Reach out on **LinkedIn** or via **GitHub Issues**.

✨ Built for **Day 29 of the 30 Days of AI Voice Agents Challenge, August 2025**


