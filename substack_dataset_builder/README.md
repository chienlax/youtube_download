# Substack Dataset Builder for Vietlish NLP

This toolkit helps you crawl Substack blogs and translate them to Vietnamese for training NLP models. It uses the external tool `sbstck-dl` for downloading.

## Prerequisites

1.  **Install Python Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Install `sbstck-dl`**:
    Tải sbstck-dl theo các bước sau
    1. Tải go (cmd)
    2. cmd: go env GOPATH -> C:\Users\username\go\bin
    3. Thêm path env
    ```bash
    go install github.com/alexferrari88/sbstck-dl@latest
    ```
    Verify it's installed by running `sbstck-dl --version`.

## Usage

The entire pipeline is automated with a single script.

### Step 1: Add Blog URLs
Open the `urls.txt` file and add the Substack blog URLs you want to download, one URL per line.

```
https://blog1.substack.com
https://anotherblog.substack.com
```

### Step 2: Run the Pipeline
Execute the `run_pipeline.py` script.

```bash
python run_pipeline.py
```

The script will perform the following actions automatically:
1.  **Download**: It reads `urls.txt` and runs `sbstck-dl` for each URL, saving the `.txt` articles into the `raw_corpus/` directory.
2.  **Translate**: After downloading, it scans `raw_corpus/`, translates each article into Vietnamese, and saves the new files into the `transcript_vi/` directory.
3. **Gen Audio**: 

The pipeline will skip any files that have already been translated, so you can safely re-run it after adding new URLs.

