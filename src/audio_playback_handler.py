import asyncio
import logging

import discord

import constants
import volume_manager

logger = logging.getLogger(__name__)

stop_playing = False


def audio_exists(audio_name: str) -> bool:
    """
    Check if the given audio name exists in the audio list.
    Args:
        audio_name: The name or index of the audio.
    Returns:
        True if the audio exists, False otherwise.
    """
    try:
        idx = int(audio_name) - 1
        return 0 <= idx < len(constants.AUDIO_NAMES)
    except (ValueError, TypeError):
        pass
    return audio_name in constants.AUDIO_NAMES_SET


def get_audio_source(audio_name: str) -> discord.FFmpegPCMAudio | None:
    """
    Get the audio source for the given audio name.
    Args:
        audio_name: The name of the audio.
    Returns:
        The audio source if found, else None.
    """
    if not audio_exists(audio_name):
        return None
    mp3_path = constants.AUDIO_DIR / f"{audio_name}.mp3"
    m4a_path = constants.AUDIO_DIR / f"{audio_name}.m4a"
    if mp3_path.exists():
        return discord.FFmpegPCMAudio(str(mp3_path))
    elif m4a_path.exists():
        return discord.FFmpegPCMAudio(str(m4a_path))
    else:
        logger.warning(f"Issue with {audio_name}: no mp3 or m4a file")
        return None


async def play_audio(voice_client: discord.VoiceClient, audio_name: str) -> bool:
    """
    Play the specified audio in the given voice client.
    Args:
        voice_client: The Discord voice client.
        audio_name: The name of the audio to play.
    Returns:
        True if playback completed, False if stopped or not found.
    """
    global stop_playing
    audio_source = get_audio_source(audio_name)
    if not audio_source:
        logger.error(f"Audio not found: {audio_name}")
        return False
    logger.info(f"Playing {audio_name}")
    volume = volume_manager.get_volume(audio_name)
    audio_player = discord.PCMVolumeTransformer(audio_source, volume=volume)
    voice_client.play(audio_player)
    while voice_client.is_playing():
        await asyncio.sleep(0.5)
        if stop_playing:
            stop_playing = False
            voice_client.stop()
            logger.info("Audio stopped")
            return False
    return True


def get_stop_playing() -> bool:
    """Return the current stop_playing state."""
    return stop_playing


def set_stop_playing() -> None:
    """Set the stop_playing flag to True."""
    global stop_playing
    stop_playing = True
