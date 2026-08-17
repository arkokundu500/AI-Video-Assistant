# 🎬 AI Video Assistant

An end-to-end AI-powered meeting and video intelligence platform. Transcribe, summarize, extract key decisions & action items, and chat with any YouTube video or uploaded video/audio file using a Retrieval-Augmented Generation (RAG) pipeline.

Built with a sleek, **Mac-inspired Bento-box UI** in Streamlit.

---

## ✨ Features

- **Multi-Source Ingestion**:
  - 🔗 **YouTube URLs**: Seamless audio extraction and processing via `yt-dlp`.
  - 📁 **Direct Video/Audio Uploads**: Supports `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, `.mp3`, `.wav`, `.flac`, `.ogg`, and `.m4a`.
- **Hybrid Speech-to-Text Engines**:
  - 🌐 **English**: High-accuracy local transcription using **OpenAI Whisper**.
  - 🇮🇳 **Hindi / Hinglish**: Real-time speech-to-text and translation to English powered by **Sarvam AI** (`saaras:v3`).
- **Meeting Intelligence Extraction** (Powered by Mistral AI & LangChain LCEL):
  - 🏷️ **Smart Title Generation**: Concise 8-word session summaries.
  - 📋 **Executive Summaries**: High-level bullet-point overviews.
  - ✅ **Action Items**: Tasks with assigned owners and deadlines.
  - 🔑 **Key Decisions**: Explicit takeaways and conclusions.
  - ❓ **Open Questions**: Unresolved topics and follow-ups.
- **Interactive RAG Q&A**:
  - Vector storage with **ChromaDB** and HuggingFace embeddings (`all-MiniLM-L6-v2`).
  - Chat directly with the transcript context using grounded RAG.
- **Mac-Inspired Bento-Grid Interface**:
  - Dark mode aesthetic with frosted-glass card design, animated status indicators, and pill badges.

---

## 🏗️ Architecture & Pipeline

```
[ YouTube URL / Video Upload ]
              │
              ▼
   [ Audio Preprocessing ]  ───►  Pydub (16kHz Mono WAV & Chunking)
              │
              ▼
    [ Transcription Engine ]
    ├── English ────────────►  OpenAI Whisper (Local)
    └── Hindi / Hinglish ───►  Sarvam AI API (Saaras v3 + Translation)
              │
              ▼
     [ Full Transcript ]
              │
    ┌─────────┴────────────────────────────────┐
    ▼                                          ▼
[ LangChain + Mistral AI ]              [ ChromaDB Vector Store ]
├── Title Generation                    ├── HuggingFace Embeddings
├── Executive Summary                   └── Recursive Text Splitter
├── Action Items Extraction                    │
├── Key Decisions                              ▼
└── Open Questions                      [ RAG Engine / Chatbot ]
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- **FFmpeg** installed and added to your system's PATH.
  - *Windows*: `winget install Gyan.FFmpeg` or download from [ffmpeg.org](https://ffmpeg.org/download.html).
  - *macOS*: `brew install ffmpeg`
  - *Linux*: `sudo apt install ffmpeg`

### 2. Clone & Setup Environment

```bash
# Clone the repository
git clone https://github.com/your-username/videoassistant.git
cd videoassistant

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure API Keys

Create a `.env` file in the root directory:

```env
# Mistral API Key (Required for Summarisation, Extraction & RAG)
MISTRAL_API_KEY=your_mistral_api_key_here

# Whisper Model Configuration (Default: small)
WHISPER_MODEL=small

# Sarvam AI (Required for Hindi / Hinglish Transcription)
SARVAM_API_KEY=your_sarvam_api_key_here
SARVAM_STT_MODEL=saaras:v3
```

---

## 💻 Usage

### Run the Web Interface (Streamlit)

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

### Run via Command Line Interface (CLI)

```bash
python main.py
```

Follow the prompts to enter a YouTube link or local path, choose the language, and interact with the CLI chat session.

---

## 📂 Project Structure

```
videoassistant/
│
├── core/
│   ├── extractor.py       # Action items, key decisions, and open questions extraction
│   ├── rag_engine.py      # LCEL RAG chain and conversational pipeline
│   ├── summarise.py       # Title generation & recursive transcript summariser
│   ├── transcriber.py     # Whisper & Sarvam AI routing and transcription
│   └── vector_store.py    # ChromaDB vector store and HuggingFace embeddings
│
├── utils/
│   └── audio_processor.py # yt-dlp downloader, WAV conversion, and chunking
│
├── app.py                 # Streamlit Bento-box UI application
├── main.py                # CLI pipeline entry point
├── requirements.txt       # Project dependencies
├── .env                   # Environment keys and configurations (git-ignored)
├── .gitignore             # Git ignore configuration
└── README.md              # Project documentation
```

---

## 🛠️ Tech Stack

- **Frontend / UI**: [Streamlit](https://streamlit.io/) with Custom CSS (Bento Design System)
- **Orchestration**: [LangChain](https://www.langchain.com/) (LCEL)
- **LLM**: [Mistral AI](https://mistral.ai/) (`mistral-small-latest`)
- **Speech-to-Text**: [OpenAI Whisper](https://github.com/openai/whisper) & [Sarvam AI](https://www.sarvam.ai/)
- **Vector Database**: [ChromaDB](https://www.trychroma.com/)
- **Embeddings**: [Hugging Face](https://huggingface.co/) (`all-MiniLM-L6-v2`)
- **Audio/Video Ingestion**: [yt-dlp](https://github.com/yt-dlp/yt-dlp), [pydub](https://github.com/jiaaro/pydub), [ffmpeg](https://ffmpeg.org/)

---

## 👤 Author

Built with ♥ by **[Arko Kundu](https://github.com/arkokundu500)**
