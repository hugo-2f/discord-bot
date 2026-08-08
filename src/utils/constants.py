import tomllib
from pathlib import Path

# === Project root and paths ===
ROOT_DIR: Path = Path(__file__).resolve().parent.parent.parent
AUDIO_DIR: Path = ROOT_DIR / "audios"
VOLUMES_PATH: Path = AUDIO_DIR / "_volumes.json"
VOLUMES_RELATIVE_PATH: Path = VOLUMES_PATH.relative_to(ROOT_DIR)

# === Text channel ID ===
with open(ROOT_DIR / "variables.toml", "rb") as file:
    config = tomllib.load(file)
CURRENT_CHANNEL_ID: int = config["CHANNEL_IDS"][config["SETTINGS"]["default_channel"]]

# === Audio settings ===
AUDIO_EXTENSIONS = [".mp3", ".m4a"]
DEFAULT_VOLUME: float = 0.3

# === Audio file names and list ===
# Note: This will read the directory at import time.
AUDIO_NAMES = sorted(
    f.stem
    for f in AUDIO_DIR.iterdir()
    if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS
)
AUDIO_NAMES_SET = set(AUDIO_NAMES)
AUDIO_LIST = "\n".join(f"{idx + 1}. {name}" for idx, name in enumerate(AUDIO_NAMES))

# === Translation settings ===
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
