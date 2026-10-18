"""One-time setup: download Kokoro neural voice model files.

Usage:
    python3 -m companion.voice.setup_kokoro

Downloads (~340 MB total) into ~/.novamind/kokoro/:
    - kokoro-v1.0.onnx
    - voices-v1.0.bin
Also installs: pip install kokoro-onnx soundfile
"""
import os
import sys
import subprocess
import urllib.request

BASE_URL = ("https://github.com/thewh1teagle/kokoro-onnx"
            "/releases/download/model-files-v1.0")
FILES = ["kokoro-v1.0.onnx", "voices-v1.0.bin"]


def _download(url: str, dest: str):
    print(f"Downloading {os.path.basename(dest)} ...")
    tmp = dest + ".part"
    try:
        with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
            total = int(r.headers.get("Content-Length") or 0)
            done = 0
            while True:
                chunk = r.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if total:
                    pct = done * 100 // total
                    print(f"\r  {pct}% ({done // 1048576} MB / {total // 1048576} MB)",
                          end="", flush=True)
        print()
        os.replace(tmp, dest)
    except Exception as e:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise RuntimeError(f"Download failed: {e}")


def main():
    from companion.voice.kokoro_tts import MODEL_DIR
    os.makedirs(MODEL_DIR, exist_ok=True)

    print("Step 1/2: installing Python packages ...")
    subprocess.run([sys.executable, "-m", "pip", "install",
                    "kokoro-onnx", "soundfile"], check=False)

    print("Step 2/2: downloading voice model (~340 MB, one time) ...")
    for name in FILES:
        dest = os.path.join(MODEL_DIR, name)
        if os.path.isfile(dest) and os.path.getsize(dest) > 10_000_000:
            print(f"  {name} already present, skipping.")
            continue
        _download(f"{BASE_URL}/{name}", dest)

    from companion.voice import kokoro_tts
    kokoro_tts._availability = None  # re-check
    if kokoro_tts.is_available():
        print("\nKokoro voice ready! Restart the companion — Minu will now "
              "speak with a natural AI voice.")
    else:
        print("\nSomething is missing. Check the errors above and re-run.")


if __name__ == "__main__":
    main()
