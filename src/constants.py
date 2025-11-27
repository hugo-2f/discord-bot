from pathlib import Path

# === Project Root and Paths ===
ROOT_DIR: Path = Path(__file__).resolve().parent.parent
AUDIO_DIR: Path = ROOT_DIR / "audios"
VOLUMES_PATH: Path = AUDIO_DIR / "volumes.json"
VOLUMES_RELATIVE_PATH: Path = VOLUMES_PATH.relative_to(ROOT_DIR)

# === Audio Settings ===
AUDIO_EXTENSIONS = [".mp3", ".m4a"]
DEFAULT_VOLUME: float = 0.4

# === Audio File Names and List ===
# Note: This will read the directory at import time.
AUDIO_NAMES = sorted(
    f.stem
    for f in AUDIO_DIR.iterdir()
    if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS
)
AUDIO_NAMES_SET = set(AUDIO_NAMES)
AUDIO_LIST = "\n".join(f"{idx + 1}. {name}" for idx, name in enumerate(AUDIO_NAMES))

# === Translation Settings ===
# To add to this list, see emojipedia.org
COUNTRY_FLAGS = {
    "🇺🇸": "en",
    "🇫🇷": "fr",
    "🇪🇸": "es",
    "🇯🇵": "ja",
    "🇨🇳": "zh-cn",
    "🇩🇪": "de",
    "🇮🇹": "it",
    "🇷🇺": "ru",
    "🇰🇷": "ko",
    "🇧🇷": "pt",
}
