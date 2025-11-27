import asyncio

import discord

from constants import AUDIO_DIR, AUDIO_NAMES
from github_integration import volumes

stop_playing = False


async def play_audio(voice_client, audio_name):
    """
    :return: only for replay command: True if continue replaying,
             False if audio not found or stop was called during replay
    """
    global stop_playing

    audio_source = get_audio_source(audio_name)
    if not audio_source:
        print(f"Audio not found: {audio_name}")
        return False

    print(f"Playing {audio_name}")
    volume = volumes[audio_name]
    audio_player = discord.PCMVolumeTransformer(audio_source, volume=volume)
    voice_client.play(audio_player)
    while voice_client.is_playing():
        await asyncio.sleep(0.5)
        if stop_playing:
            stop_playing = False
            voice_client.stop()
            print("Audio stopped")
            return False
    return True


def get_audio_source(audio_name):
    try:
        idx = int(audio_name) - 1
        audio_name = AUDIO_NAMES[idx]
    except ValueError:
        pass

    if audio_name not in AUDIO_NAMES:  # audio needs to exist
        return None

    mp3_path = AUDIO_DIR / f"{audio_name}.mp3"
    m4a_path = AUDIO_DIR / f"{audio_name}.m4a"
    if mp3_path.exists():
        return discord.FFmpegPCMAudio(str(mp3_path))
    elif m4a_path.exists():
        return discord.FFmpegPCMAudio(str(m4a_path))
    else:
        print(f"Issue with {audio_name}: no mp3 or m4a file")
        return None


def get_stop_playing():
    return stop_playing


def set_stop_playing():
    global stop_playing
    stop_playing = True
