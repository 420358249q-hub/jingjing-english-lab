"""
Download Kokoro-82M ONNX model and voice weights for 100% offline natural TTS.
Run:
    python scripts/download_kokoro.py
"""

import os
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/voices.bin"

MODEL_PATH = os.path.join(MODELS_DIR, "kokoro-v0_19.onnx")
VOICES_PATH = os.path.join(MODELS_DIR, "voices.bin")

def download_file(url: str, dest: str):
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        print(f"✅ Already exists: {os.path.basename(dest)} ({os.path.getsize(dest):,} bytes)")
        return
    print(f"📥 Downloading {os.path.basename(dest)} from:\n   {url}")
    
    def reporthook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = downloaded * 100 / total_size
            print(f"\r   Progress: {percent:.1f}% ({downloaded // (1024*1024)}MB / {total_size // (1024*1024)}MB)", end="")

    urllib.request.urlretrieve(url, dest, reporthook=reporthook)
    print("\n   Done!")

if __name__ == "__main__":
    print("=== Downloading Kokoro-82M Offline Voice Models ===")
    download_file(MODEL_URL, MODEL_PATH)
    download_file(VOICES_URL, VOICES_PATH)
    print("🎉 All Kokoro models ready in:", MODELS_DIR)

