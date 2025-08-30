# NovaFlow AI Voice Agent

NovaFlow AI Voice Agent is a web-based conversational AI application developed as part of the **30 Days of AI Voice Agents challenge (Day 29: Final Documentation)**.  
It integrates **real-time speech-to-text transcription**, **text-to-speech synthesis**, **generative AI responses**, and **web search capabilities** to provide a seamless voice and text interaction experience.  

Built with **FastAPI, AssemblyAI, Google Gemini, Murf AI, and Tavily**, NovaFlow supports features like file uploads for knowledge base integration, chat history, customizable settings, and deployment on Render.

---

## 🚀 Features

- **Real-Time Voice Interaction**: Capture audio via browser microphone, transcribe speech using AssemblyAI (RealtimeTranscriber), and generate AI responses with Google Gemini, converted to speech via Murf AI.  
- **Text-Based Interaction**: Send text queries through a chat input and receive AI-generated responses.  
- **Knowledge Base Integration**: Upload PDF or TXT files to a knowledge base, enabling the AI to summarize or reference uploaded content (e.g., *"Summarize the content of [filename]"*).  
- **Web Search**: Perform real-time web searches using Tavily API for queries containing *"search," "find," or "look up."*  
- **Chat History**: Save and retrieve conversation history, with options to create new chats or clear history.  
- **Customizable Settings**: Configure voice ID, playback speed, conversation type (casual, formal, technical), microphone sensitivity, audio quality, and UI preferences (theme, accent color).  
- **Email Integration**: Send responses or summaries to email via Zapier webhooks.  
- **Audio Feedback**: Play sound alerts (*start.mp3*, *stop.mp3*) for voice recording start/stop.  
- **Responsive UI**: A clean, dark-themed interface with a spinner for loading states, fixed "Stop Listening" button, and favicon support.  
- **Deployment**: Hosted on **Render** for scalable, production-ready access.  

---

## 📂 Folder Structure

```

VOICEAGENT/
│
├── main.py                 # FastAPI backend with WebSocket for real-time transcription
├── requirements.txt        # Python dependencies for the project
├── .env                    # Environment variables (AAI\_API\_KEY, GEMINI\_API\_KEY, etc.)
├── static/                 # Static assets (JS, CSS, media)
│   ├── index.js            # Frontend logic for WebSocket, audio recording, and UI
│   ├── style.css           # Styles for the web interface
│   ├── settings.js         # JavaScript for settings page
│   ├── favicon.ico         # Favicon for the web app
│   ├── start.mp3           # Sound alert for starting voice recording
│   └── stop.mp3            # Sound alert for stopping voice recording
├── templates/              # HTML templates for the web interface
│   ├── index.html          # Main application page
│   ├── home.html           # Landing page
│   ├── docs.html           # Documentation page
│   └── settings.html       # Settings configuration page
├── uploads/                # Directory for uploaded files and chat history
│   ├── knowledge\_base/     # Stores uploaded PDF/TXT files and extracted text
│   └── chats/              # Stores JSON files for chat history (e.g., 1.json)
└── settings.json           # Stores user settings (voice, theme, etc.)

````

---

## 🛠️ Prerequisites

- **Python 3.12** (required for backend)  
- **Node.js** (optional, for frontend asset development)  
- **API Keys**:  
  - `AAI_API_KEY` → AssemblyAI (real-time transcription)  
  - `GEMINI_API_KEY` → Google Gemini (generative AI responses)  
  - `MURF_API_KEY` → Murf AI (text-to-speech)  
  - `TAVILY_API_KEY` → Tavily (web search)  
  - `ZAPIER_WEBHOOK_URL` → Zapier (email integration, optional)  
- **Browser**: Chrome or Firefox for WebSocket & WebRTC support  
- **Render Account**: For deployment  

---

## ⚙️ Setup and Installation

1. **Clone the Repository**
   ```bash
   git clone <your-repository-url>
   cd VOICEAGENT
````

2. **Create and Activate Virtual Environment**

   ```bash
   python -m venv venv
   .\venv\Scripts\activate   # Windows
   source venv/bin/activate  # macOS/Linux
   ```

3. **Install Dependencies**
   Ensure `requirements.txt` contains:

   ```txt
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

4. **Set Environment Variables**
   Create `.env` file:

   ```env
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

6. **Add Static Files**
   Place `favicon.ico`, `start.mp3`, and `stop.mp3` in `static/`.

---

## ▶️ Usage

### Run Locally

```bash
uvicorn main:app --reload
```

Open: [http://localhost:8000/app](http://localhost:8000/app)

### Voice Interaction

* Click **microphone button** (`#micBtn`) → speak (≥1 sec).
* Click **Stop Listening** (`#stopListening`).
* Transcription + AI response appear in chat.
* Hear response via **Murf AI TTS**.

### Text Interaction

* Type in chat input (`#chatInput`) → click **send button** (`#sendBtn`).

### Knowledge Base

* Upload **PDF/TXT** at `/settings`.
* Query: `"Summarize myfile.pdf"`.

### Web Search

* Use queries like `"search for AI trends"`.

### Settings

* Configure:

  * Voice ID, playback speed
  * Conversation type (casual, formal, technical)
  * Mic sensitivity, audio quality
  * Theme, accent color
  * Enable/disable search, KB, chat history

### Chat History

* View at `/chats`.
* Create new chats / clear history.

### Email Integration

* Say: `"send to email"` or `"email the summary"` → via Zapier.

---

## 🌐 Deployment on Render

1. **Push to Git**

   ```bash
   git add .
   git commit -m "Final NovaFlow AI Voice Agent for Day 29"
   git push origin main
   ```

2. **Create Render Web Service**

   * Build Command:

     ```bash
     pip install -r requirements.txt
     ```
   * Start Command:

     ```bash
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```
   * Add environment variables in Render.

3. **Deploy**

   * Wait \~5–10 mins.
   * Access at:

     ```
     https://<your-service>.onrender.com/app
     ```

---

## 🐞 Troubleshooting

* **ModuleNotFoundError: `assemblyai.streaming`**

  * Ensure `assemblyai==0.36.0`.
  * If using older version: `assemblyai==0.26.0` with

    ```python
    from assemblyai.streaming.v3 import ...
    ```

* **Voice Input Issues**

  * Speak >1 second.
  * Check `AAI_API_KEY`.
  * Ensure mic permissions granted.

* **UI Errors (spinner/JSON warnings)**

  * Use updated `index.js` (Aug 29, 2025).
  * Ensure favicon & audio files exist.

* **Environment Issues**

  * Activate venv properly.
  * Keep project consolidated.

* **Render Issues**

  * Check logs & environment vars.

---

## ⚠️ Known Issues

* Recordings <1s cause error → speak ≥2–3s.
* PDF extraction may fail (use TXT fallback).
* Murf AI TTS may have slight latency.

---

## 🤝 Contributing

1. Fork repository
2. Create branch:

   ```bash
   git checkout -b feature/your-feature
   ```
3. Commit changes:

   ```bash
   git commit -m "Add your feature"
   ```
4. Push branch & open PR

---

## 📜 License

This project is licensed under the **MIT License**.

---

## 🙌 Acknowledgments

* **30 Days of AI Voice Agents Challenge**: Inspiration
* **AssemblyAI**: Speech-to-text
* **Google Gemini**: Generative AI
* **Murf AI**: Text-to-speech
* **Tavily**: Web search
* **FastAPI**: Backend framework
* **Render**: Cloud deployment

---

## 📬 Contact

For questions or feedback:

* Reach out via **LinkedIn**
* Or submit issues on the **GitHub repository**

---

✨ Built for **Day 29** of the **30 Days of AI Voice Agents Challenge**, *August 2025*

```


