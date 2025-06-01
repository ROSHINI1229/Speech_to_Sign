
import streamlit as st
import os
from PIL import Image
import math
import difflib
import tempfile
import speech_recognition as sr
from deep_translator import GoogleTranslator
from pydub import AudioSegment


# Initialize translator
translator = GoogleTranslator(source='ta', target='en')

# Function to translate Telugu to English
def translate_telugu_to_english(text):
    try:
        translated_text = translator.translate(text)
        return translated_text
    except Exception as e:
        st.error(f"Translation error: {e}")
        return None


def load_resources():
    images = {}
    gifs = {}
    

    for img in os.listdir("images"):
        if img.lower().endswith(('.png', '.jpg', '.jpeg')):
            path = os.path.join("images", img)
            label = os.path.splitext(img)[0].upper()
            images[label] = path
    

    for gif in os.listdir("gifs"):
        if gif.lower().endswith('.gif'):
            path = os.path.join("gifs", gif)
            label = os.path.splitext(gif)[0].upper()
            gifs[label] = path
    
    return images, gifs


def display_asl_sequence(text, images):
    if not text:
        return
    
    text = text.upper()
    words = text.split()
    
    for word_idx, word in enumerate(words):
        st.markdown(f"""
            <div class="word-container">
                <h3 style="margin: 0; color: #7289da; text-align: center">
                    {word}
                </h3>
            </div>
        """, unsafe_allow_html=True)
        
        max_chars_per_row = min(len(word), 6)
        num_rows = math.ceil(len(word) / max_chars_per_row)
        
        for row in range(num_rows):
            start_idx = row * max_chars_per_row
            end_idx = min((row + 1) * max_chars_per_row, len(word))
            word_segment = word[start_idx:end_idx]
            
            cols = st.columns(len(word_segment))
            for idx, char in enumerate(word_segment):
                with cols[idx]:
                    if char.isalpha() and char in images:
                        img = Image.open(images[char])
                        img = img.resize((150, 150))
                        st.image(img, caption=char, use_container_width=True)
                    else:
                        st.write(char)


def show_sign_results(telugu_text, english_text, images, gifs):
    if not english_text:
        return
        
    st.success(f"Tamil Text: {telugu_text}")
    st.success(f"English Translation: {english_text}")
    
    st.markdown("""
        <div style="background-color: #e8f5e9; 
                    padding: 20px; 
                    border-radius: 10px; 
                    margin: 20px 0;">
            <h2 style="color: #2e7d32; margin: 0;">ASL Sign Sequence</h2>
        </div>
    """, unsafe_allow_html=True)
    
    display_asl_sequence(english_text, images)
    
    st.markdown("""
        <div style="background-color: #e8f5e9; 
                    padding: 20px; 
                    border-radius: 10px; 
                    margin: 20px 0;">
            <h2 style="color: #2e7d32; margin: 0;">Word/Phrase Sign</h2>
        </div>
    """, unsafe_allow_html=True)
    
    text = english_text.upper()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if text in gifs:
            st.image(gifs[text], caption=text, use_container_width=True)
        else:
            matches = difflib.get_close_matches(text, list(gifs.keys()), n=1, cutoff=0.8)
            if matches:
                st.image(gifs[matches[0]], caption=matches[0], use_container_width=True)
            else:
                st.info("No matching sign GIF found for this phrase")

# Function to process uploaded audio file
def process_audio_file(audio_file):
    try:
        # Save the uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_file.read())
            tmp_file_path = tmp_file.name
        
        # Convert to WAV format if necessary
        audio = AudioSegment.from_file(tmp_file_path)
        wav_path = tmp_file_path.replace(".tmp", ".wav")
        audio.export(wav_path, format="wav")
        
        # Recognize speech from the audio file
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
            telugu_text = recognizer.recognize_google(audio, language="ta-In")
            st.success(f"Recognized Telugu Text: {telugu_text}")
            return telugu_text
    except Exception as e:
        st.error(f"Error processing audio file: {e}")
        return None

# Main function
def main():
    st.set_page_config(
        page_title="Tamil to ASL Converter",
        page_icon="🤟",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown("""
        <div class="custom-header">
            <h1>Tamil to ASL Converter</h1>
            <p class="custom-subheader">
                Convert Telugu speech/text to English and display ISL signs
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Load ASL resources
    images, gifs = load_resources()

    # Input options
    tab1, tab2, tab3 = st.tabs(["📝 Text Input", "🎤 Voice Input", "📁 File Upload"])

    with tab1:
        st.subheader("Enter Tamil Text")
        telugu_text = st.text_area("Type or paste Telugu text here:")
        if st.button("Translate and Show ASL"):
            if telugu_text:
                english_text = translate_telugu_to_english(telugu_text)
                if english_text:
                    show_sign_results(telugu_text, english_text, images, gifs)
            else:
                st.warning("Please enter some Tamil text.")

    with tab2:
        st.subheader("Speak Tamil")
        if st.button("Start Recording"):
            with st.spinner("Listening..."):
                try:
                    recognizer = sr.Recognizer()
                    with sr.Microphone() as source:
                        audio = recognizer.listen(source, timeout=5)
                        telugu_text = recognizer.recognize_google(audio, language="ta-In")
                        st.success(f"Recognized Tamil Text: {telugu_text}")
                        english_text = translate_telugu_to_english(telugu_text)
                        if english_text:
                            show_sign_results(telugu_text, english_text, images, gifs)
                except sr.WaitTimeoutError:
                    st.error("No speech detected. Please try again.")
                except Exception as e:
                    st.error(f"Error recognizing speech: {e}")

    with tab3:
        st.subheader("Upload Telugu Audio File")
        audio_file = st.file_uploader("Upload an audio file (MP3, WAV, etc.)", type=["mp3", "wav", "ogg"])
        if audio_file:
            st.audio(audio_file)
            if st.button("Process Audio File"):
                with st.spinner("Processing audio..."):
                    telugu_text = process_audio_file(audio_file)
                    if telugu_text:
                        english_text = translate_telugu_to_english(telugu_text)
                        if english_text:
                            show_sign_results(telugu_text, english_text, images, gifs)

if __name__ == "__main__":
    main()