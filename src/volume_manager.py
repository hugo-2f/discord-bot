import atexit
import json
import subprocess
from collections import defaultdict
from typing import Dict

from constants import AUDIO_NAMES, DEFAULT_VOLUME, VOLUMES_PATH, VOLUMES_RELATIVE_PATH

# Internal state
_volumes: Dict[str, float] = defaultdict(lambda: DEFAULT_VOLUME)
_volumes_changed: bool = False


def fetch_and_initialize_volumes() -> None:
    """Fetch the latest volumes.json from git and load it into memory."""
    try:
        subprocess.run(["git", "fetch"], check=True)
        subprocess.run(
            ["git", "checkout", "origin/main", "--", str(VOLUMES_RELATIVE_PATH)],
            check=True,
        )
        print("[volume_manager] Successfully fetched volumes.json")
    except subprocess.CalledProcessError as e:
        print(f"[volume_manager] Failed to fetch newest volumes: {e}")

    try:
        with open(VOLUMES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            _volumes.clear()
            _volumes.update(data)
    except FileNotFoundError:
        print(f"[volume_manager] '{VOLUMES_PATH}' not found. Using defaults.")
    except json.JSONDecodeError:
        print(
            f"[volume_manager] Error: Failed to parse '{VOLUMES_PATH}'. Using defaults."
        )


def get_volume(audio_name: str) -> float:
    return _volumes[audio_name]


def set_volume(audio_name: str, value: float) -> None:
    """Set the volume for a given audio, with validation and change tracking."""
    if audio_name not in AUDIO_NAMES:
        print(f"[volume_manager] Warning: '{audio_name}' not in AUDIO_NAMES.")
        return
    value = max(0.0, min(1.0, value))  # Clamp between 0 and 1
    _volumes[audio_name] = value
    set_volumes_changed()


def all_volumes() -> Dict[str, float]:
    return dict(_volumes)


def set_volumes_changed() -> None:
    global _volumes_changed
    _volumes_changed = True


@atexit.register
def save_and_push_volumes() -> None:
    """Save volumes.json and push to git if there were changes."""
    if not _volumes_changed:
        print("[volume_manager] No volume changes to save.")
        return
    # Remove unnecessary entries
    to_remove = [
        audio
        for audio, vol in _volumes.items()
        if audio not in AUDIO_NAMES or vol == DEFAULT_VOLUME
    ]
    for audio in to_remove:
        del _volumes[audio]

    # Save to file
    with open(VOLUMES_PATH, "w", encoding="utf-8") as f:
        json.dump(_volumes, f, indent=4)

    # Push to git
    try:
        subprocess.run(["git", "add", str(VOLUMES_RELATIVE_PATH)], check=True)
        subprocess.run(["git", "commit", "-m", "update volumes.json"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("[volume_manager] volumes.json pushed to GitHub")
    except subprocess.CalledProcessError as e:
        print(f"[volume_manager] Failed to push volumes.json: {e}")
