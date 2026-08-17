import streamlit as st
import time
import os
from utils.audio_processor import process_input, process_uploaded_file
from core.transcriber import transcribe_all
from core.summarise import summarise, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question
from utils.youtube_transcript import fetch_youtube_transcript
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Sync Streamlit Cloud secrets to environment variables if available
try:
    for secret_key, secret_val in st.secrets.items():
        if isinstance(secret_val, str) and secret_key not in os.environ:
            os.environ[secret_key] = secret_val
except Exception:
    pass


# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Video Assistant",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── MAC-Style Bento CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Root Variables ── */
:root {
    --bg:          #0d0d12;
    --surface:     #16161e;
    --surface-2:   #1e1e2a;
    --surface-3:   #252534;
    --border:      rgba(255,255,255,0.06);
    --border-hover:rgba(255,255,255,0.12);
    --accent:      #7c6aef;
    --accent-soft: rgba(124,106,239,0.15);
    --accent-glow: rgba(124,106,239,0.35);
    --cyan:        #38bdf8;
    --cyan-soft:   rgba(56,189,248,0.12);
    --text:        #e4e4ed;
    --text-2:      #a0a0b8;
    --text-3:      #5c5c78;
    --success:     #34d399;
    --success-soft:rgba(52,211,153,0.12);
    --warning:     #fbbf24;
    --danger:      #f87171;
    --radius:      16px;
    --radius-sm:   10px;
    --radius-xs:   6px;
}

/* ── Global Reset ── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

.stApp {
    background: var(--bg) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * {
    color: var(--text) !important;
}
[data-testid="stSidebar"] .stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: var(--surface-2);
    border-radius: var(--radius-sm);
    padding: 3px;
}
[data-testid="stSidebar"] .stTabs [data-baseweb="tab"] {
    border-radius: var(--radius-xs);
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.45rem 0.8rem;
    color: var(--text-3) !important;
    background: transparent;
}
[data-testid="stSidebar"] .stTabs [aria-selected="true"] {
    background: var(--accent-soft) !important;
    color: var(--accent) !important;
}
[data-testid="stSidebar"] .stTabs [data-baseweb="tab-highlight"] {
    display: none;
}
[data-testid="stSidebar"] .stTabs [data-baseweb="tab-border"] {
    display: none;
}

/* ── Headings ── */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Inter', sans-serif !important;
    color: var(--text) !important;
}

/* ── Hero Title ── */
.hero-title {
    font-family: 'Inter', sans-serif;
    font-size: clamp(2rem, 4vw, 3rem);
    font-weight: 800;
    line-height: 1.15;
    letter-spacing: -0.03em;
    margin: 0;
    background: linear-gradient(135deg, #ffffff 0%, #c4b5fd 60%, var(--cyan) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-sub {
    font-size: 0.85rem;
    color: var(--text-3);
    letter-spacing: 0.04em;
    margin-top: 0.35rem;
    font-weight: 400;
}

/* ── Bento Cards ── */
.bento {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s ease, box-shadow 0.3s ease, transform 0.2s ease;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
}

.bento:hover {
    border-color: var(--border-hover);
    box-shadow: 0 8px 32px rgba(0,0,0,0.25);
    transform: translateY(-2px);
}

.bento-accent::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 3px;
    background: linear-gradient(90deg, var(--accent), var(--cyan));
    border-radius: var(--radius) var(--radius) 0 0;
}

.bento-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-3);
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.bento-body {
    font-size: 0.875rem;
    line-height: 1.75;
    color: var(--text-2);
}

.bento-title-text {
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.01em;
}

/* ── Pill Badges ── */
.pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.2rem 0.65rem;
    border-radius: 100px;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.04em;
}

.pill-accent  { background: var(--accent-soft); color: var(--accent); }
.pill-cyan    { background: var(--cyan-soft);   color: var(--cyan);   }
.pill-success { background: var(--success-soft); color: var(--success); }

/* ── Pipeline Status Dots ── */
.pipe-row {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.55rem 0.85rem;
    background: var(--surface-2);
    border-radius: var(--radius-sm);
    margin: 0.3rem 0;
    border: 1px solid var(--border);
    font-size: 0.78rem;
    transition: border-color 0.2s;
}
.pipe-row:hover { border-color: var(--border-hover); }

.pipe-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
}
.dot-active  { background: var(--accent); box-shadow: 0 0 10px var(--accent-glow); animation: pulse 1.5s infinite; }
.dot-done    { background: var(--success); }
.dot-pending { background: var(--text-3); opacity: 0.4; }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%      { opacity: 0.35; }
}

/* ── Input & Buttons ── */
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
}

.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-soft) !important;
}

.stButton > button {
    background: linear-gradient(135deg, var(--accent), #5b4cc4) !important;
    color: white !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.02em !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.25s ease !important;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 24px var(--accent-glow) !important;
}

.stButton > button[kind="secondary"] {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-2) !important;
}

/* ── File Uploader ── */
[data-testid="stFileUploader"] {
    background: var(--surface-2) !important;
    border: 1px dashed var(--border-hover) !important;
    border-radius: var(--radius-sm) !important;
    padding: 0.5rem !important;
}
[data-testid="stFileUploader"] * {
    color: var(--text-2) !important;
    font-size: 0.8rem !important;
}

/* ── Chat ── */
.chat-container {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem;
    max-height: 400px;
    overflow-y: auto;
    margin-bottom: 1rem;
}

.chat-msg {
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
}

.chat-label {
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

.chat-bubble {
    display: inline-block;
    padding: 0.6rem 1rem;
    border-radius: var(--radius-sm);
    font-size: 0.84rem;
    line-height: 1.65;
    max-width: 88%;
}

.user-label  { color: var(--accent); }
.bot-label   { color: var(--cyan); }

.user-bubble { background: var(--accent-soft); border: 1px solid rgba(124,106,239,0.18); align-self: flex-end; }
.bot-bubble  { background: var(--cyan-soft);   border: 1px solid rgba(56,189,248,0.15);  align-self: flex-start; }

/* ── Transcript ── */
.transcript-box {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 1.2rem;
    font-size: 0.8rem;
    line-height: 1.85;
    max-height: 280px;
    overflow-y: auto;
    color: var(--text-3);
    white-space: pre-wrap;
    word-break: break-word;
}

/* ── Divider ── */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 1.5rem 0 !important;
}

/* ── Progress ── */
.stProgress > div > div > div { background: var(--accent) !important; }
.stSpinner > div { border-top-color: var(--accent) !important; }
[data-testid="stMarkdownContainer"] p { color: var(--text) !important; }
label { color: var(--text-3) !important; font-size: 0.78rem !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--surface-3); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

/* ── Credits Footer ── */
.credits {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
    color: var(--text-3);
    font-size: 0.72rem;
    letter-spacing: 0.06em;
}
.credits a {
    color: var(--accent);
    text-decoration: none;
    font-weight: 600;
}
.credits a:hover { text-decoration: underline; }

/* ── Sidebar Logo ── */
.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.5rem 0 1rem 0;
}
.sidebar-icon {
    width: 38px; height: 38px;
    border-radius: var(--radius-sm);
    background: linear-gradient(135deg, var(--accent), var(--cyan));
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    flex-shrink: 0;
}
.sidebar-name {
    font-weight: 800;
    font-size: 1rem;
    letter-spacing: -0.02em;
    color: var(--text);
    line-height: 1.1;
}
.sidebar-tag {
    font-size: 0.6rem;
    font-weight: 500;
    color: var(--text-3);
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ──────────────────────────────────────────────────────────
for key, default in {
    "result": None,
    "chat_history": [],
    "processing": False,
    "pipeline_done": False,
    "pipeline_steps": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── Helpers ────────────────────────────────────────────────────────────────────
def step_status(steps: dict, key: str) -> str:
    s = steps.get(key, "pending")
    if s == "active":  return "dot-active"
    if s == "done":    return "dot-done"
    return "dot-pending"

def render_step_bar(label: str, key: str, icon: str):
    css = step_status(st.session_state.pipeline_steps, key)
    st.markdown(f"""
    <div class="pipe-row">
        <div class="pipe-dot {css}"></div>
        <span>{icon} {label}</span>
    </div>""", unsafe_allow_html=True)

# ─── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-icon">🎬</div>
        <div>
            <div class="sidebar-name">AI Video Assistant</div>
            <div class="sidebar-tag">Chat with Video</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # ── Input Mode ──
    st.markdown('<span class="pill pill-accent">Source</span>', unsafe_allow_html=True)

    tab_url, tab_upload = st.tabs(["🔗 YouTube URL", "📁 Upload File"])

    source_url = ""
    uploaded_file = None

    with tab_url:
        source_url = st.text_input(
            "YouTube URL",
            placeholder="https://youtube.com/watch?v=...",
            label_visibility="collapsed",
        )

    with tab_upload:
        uploaded_file = st.file_uploader(
            "Upload video or audio",
            type=["mp4", "mkv", "avi", "mov", "webm", "mp3", "wav", "flac", "ogg", "m4a"],
            label_visibility="collapsed",
        )

    st.markdown("")  # spacer
    language = st.selectbox("Language", ["english", "hinglish"], index=0)

    run_btn = st.button("⚡  Analyse", use_container_width=True)

    # ── Pipeline Status ──
    if st.session_state.pipeline_done:
        st.markdown("---")
        st.markdown('<span class="pill pill-success">Pipeline Complete</span>', unsafe_allow_html=True)
        for step, icon, label in [
            ("audio",      "🔊", "Audio Processing"),
            ("transcript", "📝", "Transcription"),
            ("title",      "🏷️", "Title Generation"),
            ("summary",    "📋", "Summarisation"),
            ("extract",    "🔍", "Extraction"),
            ("rag",        "🧠", "RAG Engine"),
        ]:
            render_step_bar(label, step, icon)

# ─── Main Area ──────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">AI Video Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Transcribe · Summarise · Chat with any video by uploading or by pasting Youtube URL</div>', unsafe_allow_html=True)
st.markdown("---")

# ── Run Pipeline ────────────────────────────────────────────────────────────────
if run_btn:
    has_url = source_url.strip() if source_url else ""
    has_file = uploaded_file is not None

    if not has_url and not has_file:
        st.error("Please enter a YouTube URL or upload a video / audio file.")
    else:
        st.session_state.pipeline_done = False
        st.session_state.result = None
        st.session_state.chat_history = []
        st.session_state.pipeline_steps = {}

        progress_placeholder = st.empty()

        def update_step(key, state):
            st.session_state.pipeline_steps[key] = state

        try:
            with progress_placeholder.container():
                st.info("⚙️ Pipeline running — see sidebar for live status…")

            # ── Step 1 & 2: Audio + Transcription ──
            is_youtube_url = has_url and ("youtube.com" in has_url or "youtu.be" in has_url)

            if has_file:
                # Uploaded file: download → convert → chunk → transcribe
                update_step("audio", "active")
                chunks = process_uploaded_file(uploaded_file)
                update_step("audio", "done")

                update_step("transcript", "active")
                transcript = transcribe_all(chunks, language)
                update_step("transcript", "done")

            elif is_youtube_url:
                # YouTube URL: try captions API first (works on cloud IPs),
                # fall back to yt-dlp audio download + Whisper.
                update_step("audio", "active")
                transcript = None
                try:
                    preferred = ["en", "hi"] if language.lower() == "hinglish" else ["en"]
                    transcript = fetch_youtube_transcript(has_url, preferred_langs=preferred)
                    update_step("audio", "done")
                    update_step("transcript", "done")
                except Exception as yt_caption_err:
                    print(f"YouTube captions unavailable ({yt_caption_err}), falling back to audio download…")

                if transcript is None or not transcript.strip():
                    # Fallback: download audio via yt-dlp → transcribe
                    try:
                        chunks = process_input(has_url)
                        update_step("audio", "done")

                        update_step("transcript", "active")
                        transcript = transcribe_all(chunks, language)
                        update_step("transcript", "done")
                    except Exception as dl_err:
                        raise RuntimeError(
                            f"Could not process this YouTube video.\n\n"
                            f"• Captions were not available for this video.\n"
                            f"• Audio download failed: {dl_err}\n\n"
                            f"Please download the video manually and upload the file instead."
                        )
            else:
                # Non-YouTube URL or local path
                update_step("audio", "active")
                chunks = process_input(has_url)
                update_step("audio", "done")

                update_step("transcript", "active")
                transcript = transcribe_all(chunks, language)
                update_step("transcript", "done")

            # ── Step 3: Title ──
            update_step("title", "active")
            title = generate_title(transcript)
            update_step("title", "done")

            # ── Step 4: Summary ──
            update_step("summary", "active")
            summary = summarise(transcript)
            update_step("summary", "done")

            # ── Step 5: Extraction ──
            update_step("extract", "active")
            action_items = extract_action_items(transcript)
            decisions    = extract_key_decisions(transcript)
            questions    = extract_questions(transcript)
            update_step("extract", "done")

            # ── Step 6: RAG ──
            update_step("rag", "active")
            rag_chain = build_rag_chain(transcript)
            update_step("rag", "done")

            st.session_state.result = {
                "title": title,
                "transcript": transcript,
                "summary": summary,
                "action_items": action_items,
                "key_decisions": decisions,
                "open_questions": questions,
                "rag_chain": rag_chain,
            }
            st.session_state.pipeline_done = True
            progress_placeholder.success("✅ Analysis complete!")
            time.sleep(0.5)
            progress_placeholder.empty()
            st.rerun()

        except Exception as e:
            for k in ["audio", "transcript", "title", "summary", "extract", "rag"]:
                if st.session_state.pipeline_steps.get(k) == "active":
                    st.session_state.pipeline_steps[k] = "pending"
            progress_placeholder.error(f"❌ Error: {e}")

# ── Results — Bento Grid ────────────────────────────────────────────────────────
if st.session_state.result:
    r = st.session_state.result

    # ── Title Card (full width) ──
    st.markdown(f"""
    <div class="bento bento-accent" style="margin-bottom:1.25rem">
        <div class="bento-label">📌 Session Title</div>
        <div class="bento-title-text">{r['title']}</div>
    </div>""", unsafe_allow_html=True)

    # ── Row 2: Summary + Transcript ──
    col1, col2 = st.columns([3, 2], gap="medium")

    with col1:
        st.markdown(f"""
        <div class="bento" style="min-height:200px">
            <div class="bento-label">📋 Summary</div>
            <div class="bento-body">{r['summary']}</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        with st.expander("📝 Full Transcript", expanded=False):
            st.markdown(f'<div class="transcript-box">{r["transcript"]}</div>', unsafe_allow_html=True)

    st.markdown("")  # spacing

    # ── Row 3: Three extraction cards ──
    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        st.markdown(f"""
        <div class="bento">
            <div class="bento-label">✅ Action Items</div>
            <div class="bento-body">{r['action_items']}</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="bento">
            <div class="bento-label">🔑 Key Decisions</div>
            <div class="bento-body">{r['key_decisions']}</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="bento">
            <div class="bento-label">❓ Open Questions</div>
            <div class="bento-body">{r['open_questions']}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── RAG Chat (full width) ──
    st.markdown('<div style="font-size:1.15rem;font-weight:700;letter-spacing:-0.01em;margin-bottom:1rem">💬 Chat with your Video</div>', unsafe_allow_html=True)

    # Chat history
    if st.session_state.chat_history:
        chat_html = '<div class="chat-container">'
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                chat_html += f"""
                <div class="chat-msg" style="align-items:flex-end">
                    <span class="chat-label user-label">You</span>
                    <div class="chat-bubble user-bubble">{msg['content']}</div>
                </div>"""
            else:
                chat_html += f"""
                <div class="chat-msg" style="align-items:flex-start">
                    <span class="chat-label bot-label">🤖 Assistant</span>
                    <div class="chat-bubble bot-bubble">{msg['content']}</div>
                </div>"""
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="bento" style="text-align:center;padding:2.5rem 1.5rem">
            <div style="font-size:2rem;margin-bottom:0.5rem">💬</div>
            <div style="color:var(--text-3);font-size:0.85rem">Ask anything about your video transcript</div>
        </div>""", unsafe_allow_html=True)

    # Chat input
    chat_col1, chat_col2 = st.columns([5, 1], gap="small")
    with chat_col1:
        user_input = st.text_input("Your question", placeholder="What were the main decisions made?", label_visibility="collapsed")
    with chat_col2:
        send_btn = st.button("Send →", use_container_width=True)

    if send_btn and user_input.strip():
        with st.spinner("Thinking…"):
            answer = ask_question(r["rag_chain"], user_input.strip())
        st.session_state.chat_history.append({"role": "user",      "content": user_input.strip()})
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()

else:
    # ── Empty State ──
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:5rem 2rem;text-align:center">
        <div style="
            width:80px;height:80px;
            border-radius:20px;
            background:linear-gradient(135deg, var(--accent-soft), var(--cyan-soft));
            display:flex;align-items:center;justify-content:center;
            font-size:2.2rem;margin-bottom:1.5rem;
            border:1px solid var(--border);
        ">🎬</div>
        <div style="font-size:1.4rem;font-weight:700;color:var(--text);margin-bottom:0.4rem;letter-spacing:-0.02em">
            Ready to Analyse
        </div>
        <div style="color:var(--text-3);font-size:0.85rem;max-width:380px;line-height:1.7">
            I used <strong style="color:var(--text-2)">Sarvam AI</strong> for Hindi videos and <strong style="color:var(--text-2)">Whisper</strong> for English videos.
        </div>
        <div style="color:var(--text-3);font-size:0.85rem;max-width:380px;line-height:1.7">
            Paste a YouTube URL or upload a video / audio file in the sidebar, choose your language, and hit <strong style="color:var(--text-2)">Analyse</strong>.
        </div>
        <div style="margin-top:2rem;display:flex;gap:0.75rem;flex-wrap:wrap;justify-content:center">
            <span class="pill pill-accent">Transcription</span>
            <span class="pill pill-cyan">Summarisation</span>
            <span class="pill pill-success">RAG Chat</span>
        </div>
    </div>""", unsafe_allow_html=True)

# ─── Credits Footer ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div class="credits">
    Built with ♥ by <a href="https://www.linkedin.com/in/arkokundu5000/">Arko Kundu</a>
</div>
""", unsafe_allow_html=True)