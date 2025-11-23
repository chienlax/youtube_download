import os
import subprocess
from translator import ContentTranslator
from preprocessor import run_preprocessing

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
            # Using shell=True helps find commands in the system's PATH on Windows
            subprocess.run(command, check=True, shell=True)
            print(f"--- Successfully downloaded from {url} ---")
        except subprocess.CalledProcessError as e:
            print(f"--- Error downloading from {url}: {e} ---")
        except FileNotFoundError:
            print("\nCRITICAL ERROR: 'sbstck-dl' command not found.")
            print("Please ensure the 'sbstck-dl' tool is installed and accessible in your system's PATH.")
            return False
    
    return True

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
    # Step 1: Download all articles using sbstck-dl
    download_successful = run_downloader(output_dir="../raw_corpus")

    # Step 2: If download was successful, proceed to preprocessing and translation
    if download_successful:
        # Step 2a: Preprocess raw data
        run_preprocessing(input_dir="../raw_corpus", teencode_path="teencode.txt")
        
        # Step 2b: Translate and Generate Audio
        run_translation(input_dir="../raw_corpus", output_dir="../transcript_vi", audio_dir="../gen_audio")
    else:
        print("\nPipeline stopped due to errors in the download step.")
