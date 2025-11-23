import pandas as pd
from deep_translator import GoogleTranslator
import os
import time
from tts_generator import TTSGenerator

class ContentTranslator:
    def __init__(self, method='online'):
        self.method = method
        if method == 'online':
            self.translator = GoogleTranslator(source='auto', target='vi')
        else:
            # Offline setup placeholder
            print("Offline mode is not implemented in this version.")
            self.translator = None

    def translate_text(self, text):
        if not self.translator or not text or len(text.strip()) == 0:
            return ""
        
        try:
            # Split into chunks to avoid length limits
            chunks = [text[i:i+4500] for i in range(0, len(text), 4500)]
            translated_chunks = []
            
            for chunk in chunks:
                translated = self.translator.translate(chunk)
                translated_chunks.append(translated)
                time.sleep(0.5) # Be polite to the API
            
            return " ".join(translated_chunks)
        except Exception as e:
            print(f"Translation error: {e}")
            return f"TRANSLATION_ERROR: {e}"

    def process_directory(self, input_dir, output_dir, audio_output_dir="gen_audio"):
        """
        Translates all .txt files in a directory and saves as CSV.
        Also generates audio for the processed transcript.
        """
        if not os.path.exists(input_dir):
            print(f"Error: Input directory '{input_dir}' not found.")
            return
            
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Initialize TTS Generator
        tts_gen = TTSGenerator(output_dir=audio_output_dir, lang='vi')

        print(f"Scanning '{input_dir}' for .txt files...")
        for filename in os.listdir(input_dir):
            if filename.endswith(".txt"):
                input_path = os.path.join(input_dir, filename)
                # Change extension to .csv
                filename_no_ext = os.path.splitext(filename)[0]
                output_filename = filename_no_ext + ".csv"
                output_path = os.path.join(output_dir, output_filename)

                # Skip if already translated
                if os.path.exists(output_path):
                    print(f"Skipping '{filename}' (already exists in destination).")
                    continue

                print(f"Processing '{filename}'...")
                with open(input_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Generate Audio from processed content
                print(f"  -> Generating audio...")
                audio_path = tts_gen.generate_audio(content, filename_no_ext)
                audio_id = os.path.basename(audio_path) if audio_path else ""
                
                print(f"  -> Translating...")
                translated_content = self.translate_text(content)
                
                # Create DataFrame and save as CSV
                df = pd.DataFrame({
                    'transcript_processed': [content],
                    'transcript_vi': [translated_content],
                    'audio_id': [audio_id],
                    'audio_path': [audio_path]
                })
                
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
                
                print(f"  -> Saved to '{output_path}'")

if __name__ == "__main__":
    # This part is now controlled by run_pipeline.py
    # You can still run it manually for testing.
    print("This script is intended to be called from 'run_pipeline.py'.")
    print("Running a manual test...")
    
    # Create dummy files for testing
    if not os.path.exists("../raw_corpus"):
        os.makedirs("../raw_corpus")
    with open("../raw_corpus/test1.txt", "w") as f:
        f.write("Hello thế giới. Đây là test này.")
        
    translator = ContentTranslator(method='online')
    translator.process_directory(input_dir="../raw_corpus", output_dir="../transcript_vi")

