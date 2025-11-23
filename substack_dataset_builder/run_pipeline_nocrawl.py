import os
from translator import ContentTranslator
from preprocessor import run_preprocessing

def run_translation(input_dir="raw_corpus", output_dir="transcript_vi", audio_dir="gen_audio"):
    """
    Translates all .txt files from the input directory to the output directory.
    Also generates audio files.
    """
    print(f"\n{'='*20}\nStarting translation and TTS process...\n{'='*20}")
    translator = ContentTranslator()
    translator.process_directory(input_dir, output_dir, audio_output_dir=audio_dir)
    print(f"--- Processing complete. Transcripts in '{output_dir}', Audio in '{audio_dir}' ---")


if __name__ == "__main__":
    print("Starting pipeline without crawling/downloading...")
    
    # Step 1: Preprocess raw data (assuming it already exists)
    run_preprocessing(input_dir="../raw_corpus", teencode_path="teencode.txt")
    
    # Step 2: Translate and Generate Audio
    run_translation(input_dir="../raw_corpus", output_dir="../transcript_vi", audio_dir="../gen_audio")
    
    print("\nPipeline finished.")
