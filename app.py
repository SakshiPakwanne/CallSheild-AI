import streamlit as st
import pickle
import speech_recognition as sr
from gtts import gTTS
import time
import random
import base64

# ---------- PAGE ----------
st.set_page_config(page_title="AI CallShield", layout="centered")

# ---------- CSS ----------
st.markdown("""
<style>
body {background:#0f172a; color:white;}

.call-card {
    background:#1e293b;
    padding:30px;
    border-radius:25px;
    text-align:center;
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0% {box-shadow:0 0 10px #3b82f6;}
    50% {box-shadow:0 0 25px #3b82f6;}
    100% {box-shadow:0 0 10px #3b82f6;}
}

.title {font-size:28px; font-weight:bold;}
.number {color:gray;}

.risk-high {color:red; font-size:20px;}
.risk-mid {color:orange;}
.risk-low {color:lightgreen;}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>🛡️ AI CallShield</div>", unsafe_allow_html=True)

# ---------- LOAD MODEL ----------
@st.cache_resource
def load_models():
    with open("model.pkl", "rb") as f:
        ml_model = pickle.load(f)
    with open("vectorizer.pkl", "rb") as f:
        vectorizer = pickle.load(f)
    return ml_model, vectorizer

ml_model, vectorizer = load_models()

# ---------- SESSION ----------
if "active" not in st.session_state:
    st.session_state.active = False

if "ringing" not in st.session_state:
    st.session_state.ringing = True

# 🔥 NEW: REQUIRED FOR AUDIO
if "audio_enabled" not in st.session_state:
    st.session_state.audio_enabled = False

# ---------- START BUTTON (VERY IMPORTANT) ----------
if not st.session_state.audio_enabled:
    st.warning("🔊 Click below to enable audio (browser requirement)")
    if st.button("▶️ Start App"):
        st.session_state.audio_enabled = True
        st.rerun()
    st.stop()

# ---------- 🔔 RINGTONE ----------
def play_ringtone():
    if st.session_state.ringing:
        with open("ringtone.mp3", "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()

        st.markdown(f"""
        <audio autoplay loop>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """, unsafe_allow_html=True)

# ---------- 🔊 SPEAK ----------
def speak(text):
    tts = gTTS(text=text)
    tts.save("response.mp3")

    with open("response.mp3", "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()

    st.markdown(f"""
    <audio autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """, unsafe_allow_html=True)

# ---------- 🎤 SPEECH ----------
def speech_to_text():
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            audio = r.listen(source, phrase_time_limit=3)
        return r.recognize_google(audio).lower()
    except:
        return ""

# ---------- 🧠 DETECTION ----------
def analyze_call(text):
    fraud_words = ["otp", "bank", "account", "password", "verify"]
    suspicious_words = ["offer", "winner", "prize"]

    if any(w in text for w in fraud_words):
        return "🚨 FRAUD", 0.9, "Sensitive info requested"

    if any(w in text for w in suspicious_words):
        return "⚠️ SUSPICIOUS", 0.6, "Suspicious keywords"

    vec = vectorizer.transform([text])
    pred = ml_model.predict(vec)[0]

    if pred == 1:
        return "⚠️ SUSPICIOUS", 0.5, "ML flagged spam"
    return "✅ SAFE", 0.2, "No fraud signals"

# ---------- 🤖 AI ----------
def ai_reply(level):
    if level == "🚨 FRAUD":
        return "Fraud detected. Disconnect immediately."
    elif level == "⚠️ SUSPICIOUS":
        return "This call seems suspicious. Be careful."
    else:
        return "This call is safe."

# ---------- 📞 CALL UI ----------
caller = random.choice(["Unknown Caller", "Bank Support", "Spam Caller"])
phone = "+91 " + str(random.randint(7000000000, 9999999999))

st.markdown("<div class='call-card'>", unsafe_allow_html=True)
st.markdown(f"### 📞 {caller}")
st.markdown(f"<div class='number'>{phone}</div>", unsafe_allow_html=True)

# 🔔 RINGTONE
if not st.session_state.active:
    play_ringtone()

col1, col2 = st.columns(2)

if col1.button("📞 Accept"):
    st.session_state.active = True
    st.session_state.ringing = False
    st.rerun()

if col2.button("❌ Reject"):
    st.session_state.active = False
    st.session_state.ringing = False
    st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# ---------- 📡 LIVE CALL ----------
if st.session_state.active:

    st.success("📡 Call Connected")

    transcript = st.empty()
    risk_box = st.empty()
    progress = st.progress(0)

    text_all = ""
    score = 0

    for _ in range(8):

        text = speech_to_text()

        if text:
            text_all += text + " "

            level, s, reason = analyze_call(text)
            score = min(score + s*0.3, 1.0)

            transcript.markdown(f"🎤 {text_all}")

            if level == "🚨 FRAUD":
                risk_box.markdown(f"<div class='risk-high'>{level}</div>", unsafe_allow_html=True)
            elif level == "⚠️ SUSPICIOUS":
                risk_box.markdown(f"<div class='risk-mid'>{level}</div>", unsafe_allow_html=True)
            else:
                risk_box.markdown(f"<div class='risk-low'>{level}</div>", unsafe_allow_html=True)

            st.write(f"📊 Spam Probability: {int(score*100)}%")
            st.info(f"Reason: {reason}")

            progress.progress(score)

            # 🔊 SPEAK
            response = ai_reply(level)
            speak(response)

            if level == "🚨 FRAUD":
                st.error("🚨 CALL BLOCKED")
                st.session_state.active = False
                break

        time.sleep(1)

    if st.session_state.active:
        response = ai_reply(level)
        st.success(response)
        speak(response)

        if st.button("Take Over"):
            st.info("User joined call")

# ---------- RESET ----------
if not st.session_state.active:
    st.session_state.ringing = True
    st.warning("📴 No Active Call")