"""
Download Kokoro-82M v1.0 ONNX model and voice weights for 100% offline natural TTS.
Run:
    python scripts/download_kokoro.py
"""

import os
import urllib.request
import ssl

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

# Kokoro v1.0 official models
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"

MODEL_PATH = os.path.join(MODELS_DIR, "kokoro-v1.0.onnx")
VOICES_PATH = os.path.join(MODELS_DIR, "voices-v1.0.bin")

def download_file(url: str, dest: str):
    if os.path.exists(dest) and os.path.getsize(dest) > 10_000_000:
        print(f"✅ Already exists: {os.path.basename(dest)} ({os.path.getsize(dest):,} bytes)")
        return
    print(f"📥 Downloading {os.path.basename(dest)} from:\n   {url}")
    
    # Bypass local SSL verification issues if any
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
    urllib.request.install_opener(opener)

    def reporthook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = downloaded * 100 / total_size
            print(f"\r   Progress: {percent:.1f}% ({downloaded // (1024*1024)}MB / {total_size // (1024*1024)}MB)", end="")

    urllib.request.urlretrieve(url, dest, reporthook=reporthook)
    print("\n   Done!")

if __name__ == "__main__":
    print("=== Downloading Kokoro-82M v1.0 Offline Voice Models ===")
    download_file(MODEL_URL, MODEL_PATH)
    download_file(VOICES_URL, VOICES_PATH)
    print("🎉 All Kokoro v1.0 models ready in:", MODELS_DIR)
