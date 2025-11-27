import os
from pathlib import Path

CURRENT_DIR = os.path.dirname(__file__)
AUDIO_EXTENSIONS = [".mp3", ".m4a"]
AUDIO_DIR = Path(__file__).resolve().parent.parent / "audios"
AUDIO_NAMES = sorted(
    f.stem
    for f in AUDIO_DIR.iterdir()
    if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS
)
AUDIO_LIST = "\n".join(f"{idx + 1}. {name}" for idx, name in enumerate(AUDIO_NAMES))
VOLUMES_PATH = AUDIO_DIR / "volumes.json"
DEFAULT_VOLUME = 0.4
