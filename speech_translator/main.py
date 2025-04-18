import os
import sys
import threading
import queue
import tkinter as tk
from tkinter import ttk, messagebox

import speech_recognition as sr
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
from gtts import gTTS
from gtts.lang import tts_langs
import tempfile
import pygame
import logging
from langdetect import detect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        # You can add FileHandler here to log to a file
    ]
)

# Define supported languages (same as your provided code)
SUPPORTED_LANGUAGES = {
    'af': {'name': 'Afrikaans', 'speech_recognition_code': 'af-ZA', 'gtts_lang_code': 'af'},
    'ar': {'name': 'Arabic', 'speech_recognition_code': 'ar-AR', 'gtts_lang_code': 'ar'},
    'bg': {'name': 'Bulgarian', 'speech_recognition_code': 'bg-BG', 'gtts_lang_code': 'bg'},
    'bn': {'name': 'Bengali', 'speech_recognition_code': 'bn-IN', 'gtts_lang_code': 'bn'},
    'ca': {'name': 'Catalan', 'speech_recognition_code': 'ca-ES', 'gtts_lang_code': 'ca'},
    'cs': {'name': 'Czech', 'speech_recognition_code': 'cs-CZ', 'gtts_lang_code': 'cs'},
    'cy': {'name': 'Welsh', 'speech_recognition_code': 'cy-GB', 'gtts_lang_code': 'cy'},
    'da': {'name': 'Danish', 'speech_recognition_code': 'da-DK', 'gtts_lang_code': 'da'},
    'de': {'name': 'German', 'speech_recognition_code': 'de-DE', 'gtts_lang_code': 'de'},
    'el': {'name': 'Greek', 'speech_recognition_code': 'el-GR', 'gtts_lang_code': 'el'},
    'en': {'name': 'English', 'speech_recognition_code': 'en-US', 'gtts_lang_code': 'en'},
    'es': {'name': 'Spanish', 'speech_recognition_code': 'es-ES', 'gtts_lang_code': 'es'},
    'et': {'name': 'Estonian', 'speech_recognition_code': 'et-EE', 'gtts_lang_code': 'et'},
    'fi': {'name': 'Finnish', 'speech_recognition_code': 'fi-FI', 'gtts_lang_code': 'fi'},
    'fr': {'name': 'French', 'speech_recognition_code': 'fr-FR', 'gtts_lang_code': 'fr'},
    'gu': {'name': 'Gujarati', 'speech_recognition_code': 'gu-IN', 'gtts_lang_code': 'gu'},
    'hi': {'name': 'Hindi', 'speech_recognition_code': 'hi-IN', 'gtts_lang_code': 'hi'},
    'hr': {'name': 'Croatian', 'speech_recognition_code': 'hr-HR', 'gtts_lang_code': 'hr'},
    'hu': {'name': 'Hungarian', 'speech_recognition_code': 'hu-HU', 'gtts_lang_code': 'hu'},
    'id': {'name': 'Indonesian', 'speech_recognition_code': 'id-ID', 'gtts_lang_code': 'id'},
    'is': {'name': 'Icelandic', 'speech_recognition_code': 'is-IS', 'gtts_lang_code': 'is'},
    'it': {'name': 'Italian', 'speech_recognition_code': 'it-IT', 'gtts_lang_code': 'it'},
    'ja': {'name': 'Japanese', 'speech_recognition_code': 'ja-JP', 'gtts_lang_code': 'ja'},
    # 'jw': {'name': 'Javanese', 'speech_recognition_code': 'jw-ID', 'gtts_lang_code': 'jw'},  # Not supported by speech_recognition
    'kn': {'name': 'Kannada', 'speech_recognition_code': 'kn-IN', 'gtts_lang_code': 'kn'},
    'ko': {'name': 'Korean', 'speech_recognition_code': 'ko-KR', 'gtts_lang_code': 'ko'},
    'lt': {'name': 'Lithuanian', 'speech_recognition_code': 'lt-LT', 'gtts_lang_code': 'lt'},
    'lv': {'name': 'Latvian', 'speech_recognition_code': 'lv-LV', 'gtts_lang_code': 'lv'},
    'mk': {'name': 'Macedonian', 'speech_recognition_code': 'mk-MK', 'gtts_lang_code': 'mk'},
    'ml': {'name': 'Malayalam', 'speech_recognition_code': 'ml-IN', 'gtts_lang_code': 'ml'},
    'mr': {'name': 'Marathi', 'speech_recognition_code': 'mr-IN', 'gtts_lang_code': 'mr'},
    'my': {'name': 'Myanmar (Burmese)', 'speech_recognition_code': 'my-MM', 'gtts_lang_code': 'my'},
    'ne': {'name': 'Nepali', 'speech_recognition_code': 'ne-NP', 'gtts_lang_code': 'ne'},
    'nl': {'name': 'Dutch', 'speech_recognition_code': 'nl-NL', 'gtts_lang_code': 'nl'},
    'no': {'name': 'Norwegian', 'speech_recognition_code': 'no-NO', 'gtts_lang_code': 'no'},
    'pa': {'name': 'Punjabi', 'speech_recognition_code': 'pa-IN', 'gtts_lang_code': 'pa'},
    'pl': {'name': 'Polish', 'speech_recognition_code': 'pl-PL', 'gtts_lang_code': 'pl'},
    'pt': {'name': 'Portuguese', 'speech_recognition_code': 'pt-PT', 'gtts_lang_code': 'pt'},
    'ro': {'name': 'Romanian', 'speech_recognition_code': 'ro-RO', 'gtts_lang_code': 'ro'},
    'ru': {'name': 'Russian', 'speech_recognition_code': 'ru-RU', 'gtts_lang_code': 'ru'},
    'si': {'name': 'Sinhala', 'speech_recognition_code': 'si-LK', 'gtts_lang_code': 'si'},
    'sk': {'name': 'Slovak', 'speech_recognition_code': 'sk-SK', 'gtts_lang_code': 'sk'},
    'sq': {'name': 'Albanian', 'speech_recognition_code': 'sq-AL', 'gtts_lang_code': 'sq'},
    'sr': {'name': 'Serbian', 'speech_recognition_code': 'sr-RS', 'gtts_lang_code': 'sr'},
    'su': {'name': 'Sundanese', 'speech_recognition_code': 'su-ID', 'gtts_lang_code': 'su'},
    'sv': {'name': 'Swedish', 'speech_recognition_code': 'sv-SE', 'gtts_lang_code': 'sv'},
    'sw': {'name': 'Swahili', 'speech_recognition_code': 'sw-KE', 'gtts_lang_code': 'sw'},
    'ta': {'name': 'Tamil', 'speech_recognition_code': 'ta-IN', 'gtts_lang_code': 'ta'},
    'te': {'name': 'Telugu', 'speech_recognition_code': 'te-IN', 'gtts_lang_code': 'te'},
    'th': {'name': 'Thai', 'speech_recognition_code': 'th-TH', 'gtts_lang_code': 'th'},
    'tl': {'name': 'Tagalog', 'speech_recognition_code': 'tl-PH', 'gtts_lang_code': 'tl'},
    'tr': {'name': 'Turkish', 'speech_recognition_code': 'tr-TR', 'gtts_lang_code': 'tr'},
    'uk': {'name': 'Ukrainian', 'speech_recognition_code': 'uk-UA', 'gtts_lang_code': 'uk'},
    'ur': {'name': 'Urdu', 'speech_recognition_code': 'ur-PK', 'gtts_lang_code': 'ur'},
    'vi': {'name': 'Vietnamese', 'speech_recognition_code': 'vi-VN', 'gtts_lang_code': 'vi'},
    'zh-cn': {'name': 'Chinese (Simplified)', 'speech_recognition_code': 'zh-CN', 'gtts_lang_code': 'zh-cn'},
    'zh-tw': {'name': 'Chinese (Traditional)', 'speech_recognition_code': 'zh-TW', 'gtts_lang_code': 'zh-tw'},
}

class Translator:
    def __init__(self, src_lang: str, tgt_lang: str, cache_dir: str = None):
        """
        Initializes the translator with the specified source and target languages.

        :param src_lang: Source language code (e.g., 'en', 'es', 'fr')
        :param tgt_lang: Target language code
        :param cache_dir: Directory to cache the model and tokenizer
        """
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang

        logging.info(f"Loading tokenizer for M2M-100 model...")
        self.tokenizer = M2M100Tokenizer.from_pretrained("facebook/m2m100_418M", cache_dir=cache_dir)
        logging.info(f"Loading M2M-100 model...")
        self.model = M2M100ForConditionalGeneration.from_pretrained("facebook/m2m100_418M", cache_dir=cache_dir)

        # Set the source language
        self.tokenizer.src_lang = self.src_lang
        logging.info(f"Translator initialized for {self.src_lang} to {self.tgt_lang}")

    def translate(self, text: str, max_length: int = 512) -> str:
        """
        Translates the input text from source language to target language.

        :param text: Text to translate
        :param max_length: Maximum length of the translated text
        :return: Translated text
        """
        logging.debug(f"Translating text: {text}")
        # Tokenize the input text
        encoded = self.tokenizer(text, return_tensors="pt")

        # Generate translation
        generated_tokens = self.model.generate(
            **encoded,
            forced_bos_token_id=self.tokenizer.get_lang_id(self.tgt_lang),
            max_length=max_length
        )

        # Decode the generated tokens
        translated = self.tokenizer.decode(generated_tokens[0], skip_special_tokens=True)
        logging.debug(f"Translated text: {translated}")
        return translated

def speak_text_gtts(text: str, lang: str):
    """
    Converts text to speech using gTTS and plays the audio using pygame.

    :param text: Text to convert to speech
    :param lang: Language code for TTS
    """
    supported_langs = tts_langs()
    if lang not in supported_langs:
        logging.error(f"Language '{lang}' is not supported by gTTS.")
        return
    try:
        logging.info(f"Converting text to speech in '{lang}'...")
        tts = gTTS(text=text, lang=lang)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_path = fp.name
            tts.save(temp_path)
        logging.info("Playing the translated speech...")
        pygame.mixer.init()
        pygame.mixer.music.load(temp_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        os.remove(temp_path)
        logging.info("Playback completed.")
    except Exception as e:
        logging.error(f"Error in TTS: {e}")

# Global variables for threading and queue
stop_translation_flag = False
translation_thread = None
gui_queue = queue.Queue()

# Specify a consistent cache directory
cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "transformers")
os.makedirs(cache_dir, exist_ok=True)

def translation_process(src_lang_code, tgt_lang_code):
    global stop_translation_flag

    try:
        # Initialize the translator
        translator = Translator(src_lang_code, tgt_lang_code, cache_dir=cache_dir)
        logging.info(f"Translator initialized: {SUPPORTED_LANGUAGES[src_lang_code]['name']} -> {SUPPORTED_LANGUAGES[tgt_lang_code]['name']}")
    except Exception as e:
        logging.error(f"Error initializing translator: {e}")
        gui_queue.put(('error', f"Error initializing translator: {e}"))
        return

    # Define language codes for SpeechRecognition
    lang_codes = {lang: info['speech_recognition_code'] for lang, info in SUPPORTED_LANGUAGES.items()}

    if src_lang_code not in lang_codes:
        logging.error(f"Source language '{src_lang_code}' is not supported for speech recognition.")
        gui_queue.put(('error', f"Source language '{src_lang_code}' is not supported for speech recognition."))
        return

    source_language_code = lang_codes[src_lang_code]
    tgt_gtts_lang = SUPPORTED_LANGUAGES[tgt_lang_code]['gtts_lang_code']

    # Initialize the recognizer
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        logging.info("Adjusting for ambient noise... Please wait.")
        recognizer.adjust_for_ambient_noise(source, duration=2)
        logging.info("Ready for speech. Speak now!")

        while not stop_translation_flag:
            try:
                logging.info("\nListening...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                logging.info("Processing...")

                # Recognize speech using Google Web Speech API
                text = recognizer.recognize_google(audio, language=source_language_code)
                logging.info(f"Recognized ({SUPPORTED_LANGUAGES[src_lang_code]['name']}): {text}")

                # Put the recognized text into the queue
                gui_queue.put(('recognized', text))

                # Translate the text
                translated_text = translator.translate(text)
                logging.info(f"Translated ({SUPPORTED_LANGUAGES[tgt_lang_code]['name']}): {translated_text}")

                # Put the translated text into the queue
                gui_queue.put(('translated', translated_text))

                # Optional: Verify translation language
                try:
                    detected_lang = detect(translated_text)
                    logging.debug(f"Detected language of translation: {detected_lang}")
                except Exception as lang_detect_error:
                    logging.warning(f"Could not detect language of translated text: {lang_detect_error}")

                # Speak out the translated text using gTTS in a separate thread
                tts_thread = threading.Thread(target=speak_text_gtts, args=(translated_text, tgt_gtts_lang))
                tts_thread.start()

            except sr.WaitTimeoutError:
                logging.warning("Listening timed out while waiting for phrase to start.")
            except sr.UnknownValueError:
                logging.warning("Could not understand the audio.")
            except sr.RequestError as e:
                logging.error(f"Could not request results from the speech recognition service; {e}")
                gui_queue.put(('error', f"Could not request results from the speech recognition service; {e}"))
            except Exception as e:
                logging.error(f"An error occurred: {e}")
                gui_queue.put(('error', f"An error occurred: {e}"))

def start_translation():
    global translation_thread, stop_translation_flag
    if translation_thread and translation_thread.is_alive():
        messagebox.showwarning("Warning", "Translation is already running.")
        return

    src_lang_name = src_lang_combobox.get()
    tgt_lang_name = tgt_lang_combobox.get()

    if not src_lang_name or not tgt_lang_name:
        messagebox.showerror("Error", "Please select both source and target languages.")
        return

    src_lang_code = name_to_code[src_lang_name]
    tgt_lang_code = name_to_code[tgt_lang_name]

    # Initialize translator and start translation thread
    stop_translation_flag = False
    translation_thread = threading.Thread(target=translation_process, args=(src_lang_code, tgt_lang_code))
    translation_thread.start()

def stop_translation():
    global stop_translation_flag
    stop_translation_flag = True
    logging.info("Translation stopped.")

def process_queue():
    while not gui_queue.empty():
        try:
            msg_type, msg = gui_queue.get_nowait()
            if msg_type == 'recognized':
                # Update the recognized text widget
                recognized_text_text.delete(1.0, tk.END)
                recognized_text_text.insert(tk.END, msg)
            elif msg_type == 'translated':
                # Update the translated text widget
                translated_text_text.delete(1.0, tk.END)
                translated_text_text.insert(tk.END, msg)
            elif msg_type == 'error':
                messagebox.showerror("Error", msg)
        except queue.Empty:
            pass
    root.after(100, process_queue)  # Check the queue again after 100ms

def on_closing():
    stop_translation()
    root.destroy()

# GUI Setup
root = tk.Tk()
root.title("Real-Time Multi-Language Speech Translator")
root.geometry("600x600")
root.protocol("WM_DELETE_WINDOW", on_closing)

# Language selection
language_list = [(code, info['name']) for code, info in SUPPORTED_LANGUAGES.items()]
language_list.sort(key=lambda x: x[1])  # Sort by language name
language_codes = [code for code, name in language_list]
language_names = [name for code, name in language_list]
name_to_code = {info['name']: code for code, info in SUPPORTED_LANGUAGES.items()}

src_lang_label = tk.Label(root, text="Source Language:")
src_lang_label.pack()
src_lang_combobox = ttk.Combobox(root, values=language_names)
src_lang_combobox.pack()

tgt_lang_label = tk.Label(root, text="Target Language:")
tgt_lang_label.pack()
tgt_lang_combobox = ttk.Combobox(root, values=language_names)
tgt_lang_combobox.pack()

# Start and Stop buttons
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

start_button = tk.Button(button_frame, text="Start Translation", command=start_translation)
start_button.pack(side=tk.LEFT, padx=5)

stop_button = tk.Button(button_frame, text="Stop Translation", command=stop_translation)
stop_button.pack(side=tk.LEFT, padx=5)

# Recognized text display
recognized_text_label = tk.Label(root, text="Recognized Speech:")
recognized_text_label.pack()
recognized_text_text = tk.Text(root, height=5, width=70)
recognized_text_text.pack()

# Translated text display
translated_text_label = tk.Label(root, text="Translated Text:")
translated_text_label.pack()
translated_text_text = tk.Text(root, height=5, width=70)
translated_text_text.pack()

# Start processing the queue
root.after(100, process_queue)

# Start the GUI event loop
root.mainloop()
