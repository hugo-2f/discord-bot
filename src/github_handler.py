import atexit
import json
import subprocess
import sys
from collections import defaultdict

from constants import AUDIO_NAMES, VOLUMES_PATH, VOLUMES_RELATIVE_PATH

# initialize audio volumes
DEFAULT_VOLUME = 0.4
volumes = None
volumes_changed = False


def set_volumes_changed():
    """Mark that the audio volumes have been changed and need to be saved."""
    global volumes_changed
    volumes_changed = True


def fetch_newest_volumes():
    """Fetch the latest volumes.json from the GitHub repository."""
    try:
        subprocess.run(["git", "fetch"], check=True)
        subprocess.run(
            ["git", "checkout", "origin/main", "--", str(VOLUMES_RELATIVE_PATH)],
            check=True,
        )
        print("[fetch_newest_volumes] Successfully fetched volumes.json")
    except subprocess.CalledProcessError as e:
        print(f"[fetch_newest_volumes] Failed to fetch newest volumes: {e}")


def initialize_volumes():
    """Load audio volumes from the volumes.json file."""
    global volumes
    try:
        with open(VOLUMES_PATH, "r", encoding="utf-8") as f:
            volume_file_content = f.read()
            volumes = defaultdict(
                lambda: DEFAULT_VOLUME, json.loads(volume_file_content)
            )
    except FileNotFoundError:
        print(f"[initialize_volumes] '{VOLUMES_PATH}' not found")
        sys.exit()
    except json.JSONDecodeError:
        print(
            f"[initialize_volumes] Error: Failed to parse '{VOLUMES_PATH}'. Ensure it contains valid JSON."
        )
        sys.exit()


@atexit.register
def update_volumes() -> None:
    """Update and push volumes.json to GitHub if there are changes."""
    global volumes_changed
    if not volumes or not volumes_changed:
        print("[update_volumes] Volumes not changed, no need to push to GitHub")
        return

    # remove unnecessary entries in VOLUMES
    to_remove = []
    for audio, volume in volumes.items():
        if audio not in AUDIO_NAMES or volume == DEFAULT_VOLUME:
            to_remove.append(audio)
    for audio in to_remove:
        del volumes[audio]

    # Push to GitHub
    try:
        subprocess.run(["git", "add", VOLUMES_RELATIVE_PATH], check=True)
        subprocess.run(["git", "commit", "-m", "update volumes.json"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("[update_volumes] volumes.json pushed to GitHub")
    except subprocess.CalledProcessError as e:
        print(f"[update_volumes] Failed to push volumes.json: {e}")


def main() -> None:
    """Startup routine to fetch and initialize volumes."""
    fetch_newest_volumes()
    initialize_volumes()


if __name__ == "__main__":
    main()
