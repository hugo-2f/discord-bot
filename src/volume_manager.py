import atexit
import json
import logging
import subprocess
from collections import defaultdict
from typing import Dict

import constants

logger = logging.getLogger(__name__)

_volumes: Dict[str, float] = defaultdict(lambda: constants.DEFAULT_VOLUME)
_volumes_changed: bool = False


def fetch_and_initialize_volumes() -> None:
    """
    Fetch the latest volumes.json from GitHub and load it into memory.
    """
    try:
        subprocess.run(["git", "fetch"], check=True)
        subprocess.run(
            [
                "git",
                "checkout",
                "origin/main",
                "--",
                str(constants.VOLUMES_RELATIVE_PATH),
            ],
            check=True,
        )
        logger.info("Successfully fetched volumes.json")
    except subprocess.CalledProcessError as e:
        logger.warning(f"Failed to fetch newest volumes: {e}")

    try:
        with open(constants.VOLUMES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            _volumes.clear()
            _volumes.update(data)
    except FileNotFoundError:
        logger.warning(f"'{constants.VOLUMES_PATH}' not found. Using defaults.")
    except json.JSONDecodeError:
        logger.error(f"Failed to parse '{constants.VOLUMES_PATH}'. Using defaults.")


def get_volume(audio_name: str) -> float:
    """
    Get the volume for a given audio.
    Args:
        audio_name: The name of the audio.
    Returns:
        The volume as a float.
    """
    if audio_name not in constants.AUDIO_NAMES_SET:
        logger.warning(f"'{audio_name}' not in AUDIO_NAMES.")
        return -1
    return _volumes[audio_name]


def set_volume(audio_name: str, value: float) -> None:
    """
    Set the volume for a given audio, with validation and change tracking.
    Args:
        audio_name: The name of the audio.
        value: The volume value (0.0 to 1.0).
    """
    if audio_name not in constants.AUDIO_NAMES_SET:
        logger.warning(f"'{audio_name}' not in AUDIO_NAMES.")
        return
    value = max(0.0, min(1.0, value))
    _volumes[audio_name] = value
    set_volumes_changed()


def all_volumes() -> Dict[str, float]:
    """
    Get a copy of all volumes.
    Returns:
        A dictionary of audio names to volumes.
    """
    return dict(_volumes)


def set_volumes_changed() -> None:
    """
    Mark that the volumes have changed and need to be saved.
    """
    global _volumes_changed
    _volumes_changed = True


@atexit.register
def save_and_push_volumes() -> None:
    """
    Save volumes.json and push to git if there were changes.
    """
    if not _volumes_changed:
        logger.info("No volume changes to save.")
        return
    to_remove = [
        audio
        for audio, vol in _volumes.items()
        if audio not in constants.AUDIO_NAMES_SET or vol == constants.DEFAULT_VOLUME
    ]
    for audio in to_remove:
        del _volumes[audio]
    with open(constants.VOLUMES_PATH, "w", encoding="utf-8") as f:
        json.dump(_volumes, f, indent=4)
    try:
        subprocess.run(["git", "add", str(constants.VOLUMES_RELATIVE_PATH)], check=True)
        subprocess.run(["git", "commit", "-m", "update volumes.json"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        logger.info("volumes.json pushed to GitHub")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to push volumes.json: {e}")
