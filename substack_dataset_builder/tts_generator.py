from gtts import gTTS
import os

class TTSGenerator:
    def __init__(self, output_dir="gen_audio", lang='vi'):
        self.output_dir = output_dir
        self.lang = lang
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def generate_audio(self, text, filename_no_ext):
        """
        Generates audio from text and saves it to the output directory.
        Returns the relative path to the generated audio file.
        """
        if not text or not text.strip():
            return None

        # gTTS saves as mp3
        output_filename = f"{filename_no_ext}.mp3"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Skip if already exists to save time/API calls
        if os.path.exists(output_path):
            return output_path

        try:
            tts = gTTS(text=text, lang=self.lang)
            tts.save(output_path)
            return output_path
        except Exception as e:
            print(f"TTS Generation Error for {filename_no_ext}: {e}")
            return None
