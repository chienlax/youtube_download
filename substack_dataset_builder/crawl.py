import os
import subprocess
import re
import time
import pandas as pd
from gtts import gTTS
from deep_translator import GoogleTranslator

# --- 1. Downloader ---
def run_downloader(urls_file="urls.txt", output_dir="raw_corpus"):
    """
    Reads URLs from a file and runs the sbstck-dl command for each.
    """
    if not os.path.exists(urls_file):
        print(f"Error: '{urls_file}' not found. Please create it and add Substack URLs.")
        return False

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(urls_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"Found {len(urls)} URL(s) to process.")

    for url in urls:
        print(f"\n{'='*20}\nDownloading from: {url}\n{'='*20}")
        command = [
            "sbstck-dl",
            "download",
            "-u", url,
            "-f", "txt",
            "-o", output_dir,
        ]
        try:
            subprocess.run(command, check=True, shell=True)
            print(f"--- Successfully downloaded from {url} ---")
        except subprocess.CalledProcessError as e:
            print(f"--- Error downloading from {url}: {e} ---")
        except FileNotFoundError:
            print("\nCRITICAL ERROR: 'sbstck-dl' command not found.")
            print("Please ensure the 'sbstck-dl' tool is installed and accessible in your system's PATH.")
            return False
    return True

# --- 2. Preprocessor ---
def load_teencode_dict(file_path):
    teencode_dict = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) == 2:
                    teencode_dict[parts[0]] = parts[1]
    except FileNotFoundError:
        print(f"Warning: Teencode file not found at {file_path}.")
    except Exception as e:
        print(f"Error reading teencode file: {e}")
    return teencode_dict

def clean_text(text, teencode_dict):
    text = str(text).lower()
    url_pattern = r'https?://\S+|www\.\S+'
    text = re.sub(url_pattern, '', text)
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF" u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF" u"\U00002702-\U000027B0" u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937" u'\U00010000-\U0010ffff' u"\u200d" u"\u2640-\u2642"
        u"\u2600-\u2B55" u"\u23cf" u"\u23e9" u"\u231a" u"\u3030" u"\ufe0f"
        "]+", flags=re.UNICODE)
    text = re.sub(emoji_pattern, ' ', text)

    for key, value in teencode_dict.items():
        if key.isalnum():
            pattern = r'\b' + re.escape(key) + r'\b'
        else:
            pattern = re.escape(key)
        text = re.sub(pattern, value, text, flags=re.IGNORECASE)
        
    text = " ".join(text.split())
    return text

def run_preprocessing(input_dir, teencode_path="teencode.txt"):
    print(f"\n{'='*20}\nStarting preprocessing...\n{'='*20}")
    replace_list = {':v':'hihi', '<3':'yêu', '♥️':'yêu','❤':'yêu','a':'anh','ac':'anh chị','ace':'anh chị em','ad':'quản lý'}
    teencode_from_file = load_teencode_dict(teencode_path)
    final_replace_list = {**replace_list, **teencode_from_file}
    
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' not found.")
        return

    count = 0
    for filename in os.listdir(input_dir):
        if filename.endswith(".txt"):
            file_path = os.path.join(input_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                cleaned_content = clean_text(content, final_replace_list)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)
                count += 1
            except Exception as e:
                print(f"Error processing {filename}: {e}")
    print(f"--- Preprocessing complete. Processed {count} files in '{input_dir}' ---")

# --- 3. TTS Generator ---
class TTSGenerator:
    def __init__(self, output_dir="gen_audio", lang='vi'):
        self.output_dir = output_dir
        self.lang = lang
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_audio(self, text, filename_no_ext):
        if not text or not text.strip(): return None
        output_filename = f"{filename_no_ext}.mp3"
        output_path = os.path.join(self.output_dir, output_filename)
        if os.path.exists(output_path): return output_path
        try:
            tts = gTTS(text=text, lang=self.lang)
            tts.save(output_path)
            return output_path
        except Exception as e:
            print(f"TTS Generation Error for {filename_no_ext}: {e}")
            return None

# --- 4. Translator ---
class ContentTranslator:
    def __init__(self, method='online'):
        if method == 'online':
            self.translator = GoogleTranslator(source='auto', target='vi')
        else:
            self.translator = None

    def translate_text(self, text):
        if not self.translator or not text or len(text.strip()) == 0: return ""
        try:
            chunks = [text[i:i+4500] for i in range(0, len(text), 4500)]
            translated_chunks = []
            for chunk in chunks:
                translated = self.translator.translate(chunk)
                translated_chunks.append(translated)
                time.sleep(0.5)
            return " ".join(translated_chunks)
        except Exception as e:
            print(f"Translation error: {e}")
            return f"TRANSLATION_ERROR: {e}"

    def process_directory(self, input_dir, output_dir, audio_output_dir):
        if not os.path.exists(input_dir):
            print(f"Error: Input directory '{input_dir}' not found.")
            return
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        tts_gen = TTSGenerator(output_dir=audio_output_dir, lang='vi')
        print(f"Scanning '{input_dir}' for .txt files...")
        for filename in os.listdir(input_dir):
            if filename.endswith(".txt"):
                input_path = os.path.join(input_dir, filename)
                filename_no_ext = os.path.splitext(filename)[0]
                output_filename = filename_no_ext + ".csv"
                output_path = os.path.join(output_dir, output_filename)

                if os.path.exists(output_path):
                    print(f"Skipping '{filename}' (already exists).")
                    continue

                print(f"Processing '{filename}'...")
                with open(input_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                print(f"  -> Generating audio...")
                audio_path = tts_gen.generate_audio(content, filename_no_ext)
                audio_id = os.path.basename(audio_path) if audio_path else ""
                
                print(f"  -> Translating...")
                translated_content = self.translate_text(content)
                
                df = pd.DataFrame({
                    'transcript_processed': [content],
                    'transcript_vi': [translated_content],
                    'audio_id': [audio_id],
                    'audio_path': [audio_path]
                })
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
                print(f"  -> Saved to '{output_path}'")

# --- 5. Main Pipeline Execution ---
def run_full_pipeline(crawl=True):
    # Define relative paths
    # Assumes the script is run from `substack_dataset_builder` directory
    raw_corpus_dir = "../raw_corpus"
    transcript_dir = "../transcript_vi"
    audio_dir = "../gen_audio"
    
    if crawl:
        # Step 1: Download
        download_successful = run_downloader(output_dir=raw_corpus_dir)
        if not download_successful:
            print("\nPipeline stopped due to errors in the download step.")
            return
    else:
        print("Skipping download step as requested.")

    # Step 2: Preprocess
    run_preprocessing(input_dir=raw_corpus_dir, teencode_path="teencode.txt")
    
    # Step 3: Translate and Generate Audio
    print(f"\n{'='*20}\nStarting translation and TTS process...\n{'='*20}")
    translator = ContentTranslator()
    translator.process_directory(raw_corpus_dir, transcript_dir, audio_dir)
    print(f"--- Processing complete. Transcripts in '{transcript_dir}', Audio in '{audio_dir}' ---")
    print("\nPipeline finished.")

if __name__ == "__main__":
    # Set to False to run without downloading (if files are already in raw_corpus)
    CRAWL_ENABLED = True 
    run_full_pipeline(crawl=CRAWL_ENABLED)
