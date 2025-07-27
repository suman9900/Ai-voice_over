import streamlit as st
import whisper
from gtts import gTTS
from pydub import AudioSegment
import subprocess
import os
import uuid

# Function to extract audio from video using ffmpeg
def extract_audio(video_path, output_audio_path):
    try:
        command = [
            "ffmpeg", "-i", video_path, "-vn",
            "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
            output_audio_path
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode != 0:
            error_message = result.stderr.decode()
            st.error(f"❌ FFmpeg failed: {error_message}")
            return None

        return output_audio_path

    except FileNotFoundError:
        st.error("❌ FFmpeg not found. Make sure it is installed and added to your system PATH.")
        return None
    except Exception as e:
        st.error(f"❌ Error extracting audio: {e}")
        return None


# Transcribe audio using Whisper
def transcribe_audio(audio_path, language="en"):
    try:
        model = whisper.load_model("small")
        result = model.transcribe(audio_path, language=language)
        return result.get("text", "").strip()
    except Exception as e:
        st.error(f"❌ Transcription failed: {e}")
        return None

# Generate AI voice with gTTS
def generate_ai_voice(text, lang="en"):
    try:
        tts = gTTS(text=text, lang=lang)
        output_path = f"ai_voice_{uuid.uuid4()}.mp3"
        tts.save(output_path)
        return output_path
    except Exception as e:
        st.error(f"❌ Error generating AI voice: {e}")
        return None

# Adjust audio to match video length
def adjust_audio_length(original_audio_path, generated_audio_path):
    try:
        original = AudioSegment.from_file(original_audio_path)
        generated = AudioSegment.from_file(generated_audio_path)

        if len(original) > len(generated):
            silence = AudioSegment.silent(duration=(len(original) - len(generated)))
            adjusted = generated + silence
        else:
            adjusted = generated[:len(original)]

        adjusted_path = f"adjusted_{uuid.uuid4()}.wav"
        adjusted.export(adjusted_path, format="wav")
        return adjusted_path
    except Exception as e:
        st.error(f"❌ Error adjusting audio: {e}")
        return None

# Replace audio in video using ffmpeg
def replace_audio(video_path, new_audio_path, output_video_path):
    try:
        command = [
            "ffmpeg", "-i", video_path, "-i", new_audio_path, "-c:v", "copy",
            "-map", "0:v:0", "-map", "1:a:0", "-shortest", "-y", output_video_path
        ]
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return output_video_path
    except Exception as e:
        st.error(f"❌ Error replacing audio: {e}")
        return None

# Streamlit UI
st.set_page_config(page_title="AI Voice Over", layout="centered")
st.title("🎙️ AI Voice Over for Videos")

st.markdown("""
1. Extract audio from your video  
2. Transcribe it using Whisper  
3. Generate AI voice with gTTS  
4. Replace video audio using ffmpeg  
""")

uploaded_file = st.file_uploader("📤 Upload a video", type=["mp4", "avi", "mov"])
language_options = {"English": "en", "Spanish": "es", "French": "fr", "Hindi": "hi"}
language = st.selectbox("Select language", list(language_options.keys()))

if uploaded_file:
    video_path = f"video_{uuid.uuid4()}.mp4"
    with open(video_path, "wb") as f:
        f.write(uploaded_file.read())
    st.video(video_path)

    if st.button("🔧 Process Video"):
        with st.spinner("Processing..."):
            audio_path = f"audio_{uuid.uuid4()}.wav"
            extracted_audio = extract_audio(video_path, audio_path)
            if not extracted_audio:
                st.stop()

            transcript = transcribe_audio(extracted_audio, language_options[language])
            if not transcript:
                st.stop()
            st.success("📝 Transcription complete")
            st.write(transcript)

            ai_voice = generate_ai_voice(transcript, language_options[language])
            if not ai_voice:
                st.stop()

            adjusted_audio = adjust_audio_length(extracted_audio, ai_voice)
            if not adjusted_audio:
                st.stop()

            output_video_path = f"output_{uuid.uuid4()}.mp4"
            final_video = replace_audio(video_path, adjusted_audio, output_video_path)
            if not final_video:
                st.stop()

            st.success("✅ Video processed successfully!")
            st.video(output_video_path)
            with open(final_video, "rb") as f:
                st.download_button("⬇️ Download Final Video", f, file_name="ai_voice_video.mp4")

        # Cleanup
        for file in [video_path, audio_path, ai_voice, adjusted_audio, output_video_path]:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except:
                pass

