import streamlit as st
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from gtts import gTTS
from io import BytesIO
import base64
import random

# ===============================
# COMMAND LOGGING
# ===============================
COMMAND_LOG_FILE = 'command_log.json'

def log_command(command):
    try:
        if os.path.exists(COMMAND_LOG_FILE):
            with open(COMMAND_LOG_FILE, 'r') as file:
                command_log = json.load(file)
        else:
            command_log = []

        command_log.append({
            'command': command,
            'timestamp': str(datetime.now())
        })

        with open(COMMAND_LOG_FILE, 'w') as file:
            json.dump(command_log, file, indent=4)

    except Exception as e:
        print(f"Error logging command: {e}")

def generate_report():
    if os.path.exists(COMMAND_LOG_FILE):
        with open(COMMAND_LOG_FILE, 'r') as file:
            command_log = json.load(file)
        report = "Command Report:\n\n"
        for entry in command_log:
            report += f"Command: {entry['command']}, Timestamp: {entry['timestamp']}\n"
        return report
    else:
        return "No commands have been logged yet."

# ===============================
# TEXT-TO-SPEECH
# ===============================
def speak(text):
    tts = gTTS(text=text, lang='en')
    fp = BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    audio_bytes = fp.read()
    audio_b64 = base64.b64encode(audio_bytes).decode()
    st.markdown(f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
        </audio>
    """, unsafe_allow_html=True)

# ===============================
# VOICE ASSISTANT
# ===============================
def voice_assistant():
    st.markdown("### 🎤 SolB Voice Assistant")
    st.markdown("""
    <button onclick="startDictation()">Speak to SolB</button>
    <script>
    function startDictation() {
        if (window.hasOwnProperty('webkitSpeechRecognition')) {
            var recognition = new webkitSpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = "en-US";
            recognition.start();
            recognition.onresult = function(e) {
                var text = e.results[0][0].transcript;
                document.getElementById("voice_output").value = text;
                recognition.stop();
            };
        }
    }
    </script>
    <input type="text" id="voice_output" placeholder="Your speech will appear here">
    """, unsafe_allow_html=True)

    user_voice_input = st.text_input("Captured Speech:", "")
    if user_voice_input:
        log_command(user_voice_input)
        # Example simple responses
        if "stress" in user_voice_input.lower():
            response = "I understand you feel stressed. Let me play a relaxing song."
            speak(response)
            st.info(response)
            music_dir = "C:\\Users\\harin\\Music"
            songs = [s for s in os.listdir(music_dir) if s.endswith(".mp3")]
            if songs:
                song = random.choice(songs)
                os.startfile(os.path.join(music_dir, song))
        elif "report" in user_voice_input.lower():
            response = generate_report()
            speak("Here is your command report.")
            st.text(response)
        else:
            response = f"You said: {user_voice_input}. I am still learning to respond to this command."
            speak(response)
            st.info(response)

# ===============================
# MAIN APP
# ===============================
st.set_page_config(page_title="Solrrbox", layout="wide")
st.sidebar.title("Solrrbox Menu")
menu = st.sidebar.radio("Menu", ["Home", "SolB Voice Assistant"])

if menu == "Home":
    st.markdown("## Welcome back 👋")
    st.write("This is your home dashboard.")
    # Place any metrics, charts, etc. here
    st.info("SolB is available in the Voice Assistant menu.")

elif menu == "SolB Voice Assistant":
    voice_assistant()
