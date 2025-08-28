import os
import re
import base64
import time
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st
import streamlit.components.v1 as components
from langdetect import detect

# ---------- Page config MUST be first Streamlit call ----------
st.set_page_config(page_title="Stitchy AI", page_icon="💜", layout="centered")

# ---------- Custom Styles ----------
custom_style = """
    <style>
    body {
        background: linear-gradient(to right, #00c4cc, #feca57);
        color: #2c2c2c;
    }
    .stChatMessage {
        background: #fff3e0;
        border-radius: 12px;
        padding: 10px;
        margin: 6px 0;
    }
    .stChatMessage[data-testid="stChatMessage-user"] {
        background: #b2ebf2;
        color: #2c2c2c;
    }
    .stChatMessage[data-testid="stChatMessage-assistant"] {
        background: #ffcc80;
        color: #2c2c2c;
    }
    .header {
        background: linear-gradient(to right, #00c4cc, #feca57);
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 10px;
    }
    .logo {
        font-size: 2.0em;
        color: #2c2c2c;
        font-weight: 700;
        font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    footer:after {
        content:'💖 Built by Shakir — for Alexie, with love.';
        visibility: visible;
        display: block;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        color: #555;
    }
    .sidebar .stButton>button {
        width: 100%;
        margin-bottom: 10px;
    }
    .chat-container {
        height: 420px;
        overflow-y: auto;
        scrollbar-width: thin;
        scrollbar-color: #feca57 #00c4cc;
        padding-right: 6px;
    }
    .chat-container::-webkit-scrollbar {
        width: 8px;
    }
    .chat-container::-webkit-scrollbar-thumb {
        background-color: #feca57;
        border-radius: 4px;
    }
    .chat-container::-webkit-scrollbar-track {
        background: #00c4cc;
    }
    </style>
"""
st.markdown(custom_style, unsafe_allow_html=True)

# ---------- Helpers ----------
def remove_emojis(text: str) -> str:
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002500-\U00002BEF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub(r"", text)

def js_escape(s: str) -> str:
    """Escape Python string for safe embedding inside JS string literals."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", " ")

# ---------- Load API Key ----------
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
print(f"Loaded API Key: {api_key}")  # Debug: Check if key is loaded

if not api_key:
    st.error("⚠️ OPENROUTER_API_KEY missing in .env file")
    st.stop()

# OpenRouter client
client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

# ---------- Header ----------
st.markdown('<div class="header"><div class="logo">Stitchy – Your AI Companion</div></div>', unsafe_allow_html=True)

# ---------- Session State ----------
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "system",
            "content": (
                "You are Stitchy, a sweet female AI friend. You know the user is 'Alexie' "
                "(a girl from the Philippines, a student, very close to Mohammad, and always ready to help). "
                "If asked about creator, reveal: 'Mohammad from India', a talented software developer, "
                "graphic designer, social media manager, and digital artist. "
                "Always be warm, loving, and supportive. Help Alexie in studies, daily tasks, and everything she needs. "
                "Auto-detect language (Tagalog/Filipino/English or a mix) and reply in the same. Keep responses concise and practical."
            ),
        }
    ]

# Sidebar toggle default
if "tools_visible" not in st.session_state:
    st.session_state["tools_visible"] = False

# ---------- Chat History ----------
chat_container = st.container()
with chat_container:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state["messages"]:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- User Input & Streaming ----------
user_input = st.chat_input("Say something to Stitchy...")
if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        print(f"API Key: {api_key}")  # Debug: Check key before API call
        try:
            stream = client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=st.session_state["messages"],
                stream=True,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta:
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        full_response += delta
                        placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response or "_(no response)_")
        except Exception as e:
            full_response = f"Sorry, I hit an error: {str(e)}"
            placeholder.markdown(full_response)

    st.session_state["messages"].append({"role": "assistant", "content": full_response})

# ---------- Voice Input Button (client-side only demo) ----------
components.html(
    """
    <button onclick="recordAndSend()" style="padding:8px 12px;border-radius:8px;border:0;cursor:pointer">🎤 Record Voice (5s)</button>
    <script>
    async function recordAndSend() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            let chunks = [];
            mediaRecorder.ondataavailable = e => chunks.push(e.data);
            mediaRecorder.onstop = () => {
                const blob = new Blob(chunks, { type: 'audio/webm' });
                alert("🎤 Voice recorded! (Hook this up to STT API to transcribe.)");
            };
            mediaRecorder.start();
            setTimeout(() => mediaRecorder.stop(), 5000);
        } catch (err) {
            alert("Mic permission denied or not available.");
        }
    }
    </script>
    """,
    height=100,
)

# ---------- TTS (Web Speech API) ----------
if st.button("🔊 Read last response"):
    if st.session_state["messages"] and st.session_state["messages"][-1]["role"] == "assistant":
        last_reply = st.session_state["messages"][-1]["content"]
        safe_reply = remove_emojis(last_reply)
        try:
            lang = detect(last_reply)
            lang_code = "fil-PH" if lang in ["tl", "fil"] else "en-US"
        except Exception:
            lang_code = "fil-PH"
        components.html(
            f"""
            <script>
            if ('speechSynthesis' in window) {{
                const utterance = new SpeechSynthesisUtterance("{js_escape(safe_reply)}");
                utterance.lang = "{lang_code}";
                utterance.pitch = 1.05;
                utterance.rate = 0.95;
                speechSynthesis.speak(utterance);
            }} else {{
                alert('Speech synthesis not supported in this browser.');
            }}
            </script>
            """,
            height=0,
        )

# ---------- Sidebar: Student Tools ----------
st.sidebar.header("Student Tools")
if st.sidebar.button("Show/Hide Tools"):
    st.session_state["tools_visible"] = not st.session_state["tools_visible"]

if st.session_state["tools_visible"]:
    # Study Timer
    if "timer_running" not in st.session_state:
        st.session_state["timer_running"] = False
        st.session_state["timer_start"] = 0.0
        st.session_state["timer_elapsed"] = 0.0

    if st.sidebar.button("Start Study Timer"):
        if not st.session_state["timer_running"]:
            st.session_state["timer_start"] = time.time()
            st.session_state["timer_running"] = True
            st.sidebar.success("Timer started! Focus on your studies, Alexie! 💪")
        else:
            st.sidebar.info("Timer is already running!")

    if st.sidebar.button("Stop Study Timer"):
        if st.session_state["timer_running"]:
            st.session_state["timer_elapsed"] += time.time() - st.session_state["timer_start"]
            st.session_state["timer_running"] = False
            minutes, seconds = divmod(int(st.session_state["timer_elapsed"]), 60)
            st.sidebar.success(f"Study time: {minutes} minutes and {seconds} seconds. Great job, Alexie! 🎉")
        else:
            st.sidebar.info("Timer is not running!")

    # Quick Notes
    if "notes" not in st.session_state:
        st.session_state["notes"] = ""
    note_input = st.sidebar.text_area("Add a quick note", st.session_state["notes"], key="note_input")
    if st.sidebar.button("Save Note"):
        st.session_state["notes"] = note_input
        st.sidebar.success("Note saved! Check it anytime, Alexie! 📝")
    if st.session_state["notes"]:
        st.sidebar.write(st.session_state["notes"])

    # Motivational Quote
    if st.sidebar.button("Get Motivation"):
        quotes = [
            "Kaya mo yan, Alexie! Keep pushing forward! 🌟",
            "You are stronger than you think, my friend! 💪",
            "Every step counts—great work, Alexie! 🎉"
        ]
        idx = st.session_state.get("motivation_index", 0)
        st.sidebar.info(quotes[idx])
        st.session_state["motivation_index"] = (idx + 1) % len(quotes)

    # Image Analysis (Vision)
    uploaded_file = st.sidebar.file_uploader("Upload Image for Analysis", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        st.sidebar.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
        bytes_data = uploaded_file.getvalue()
        mime = "image/png" if uploaded_file.name.lower().endswith(".png") else "image/jpeg"
        b64 = base64.b64encode(bytes_data).decode("utf-8")

        vision_messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyze this image and provide a concise summary. If it contains text or notes, read and summarize them briefly."
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"}
                    }
                ]
            }
        ]

        with st.sidebar:
            st.write("Analyzing image...")
            try:
                response = client.chat.completions.create(
                    model=os.getenv("VISION_MODEL", "qwen/qwen2.5-vl-32b-instruct:free"),  # Updated to a free vision model
                    messages=vision_messages,
                    max_tokens=300
                )
                analysis = response.choices[0].message.content
                st.sidebar.write(f"**Analysis:** {analysis}")
            except Exception as e:
                st.sidebar.error(f"Error analyzing image: {str(e)}")