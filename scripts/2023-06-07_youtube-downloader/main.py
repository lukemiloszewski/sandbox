"""
Script to download youtube videos and extract audio and subtitles.

Requirements:
    - ffmpeg (https://github.com/yt-dlp/FFmpeg-Builds)
    - yt-dlp
"""

import pathlib

from typing import Optional

from yt_dlp import YoutubeDL


def create_subtitles_options(
    output_directory: Optional[str] = None, output_file: Optional[str] = None
) -> dict:
    """
    Create options to download subtitles file ONLY (no audio/video files), in vtt format

    CLI command: yt-dlp --skip-download --write-auto-subs --sub-format ass/srt/best -o "%(title)s.%(ext)s" --compat-options no-certifi {}
    """
    if output_directory is None:
        output_path = pathlib.Path(".")
    else:
        output_path = pathlib.Path(output_directory)
        if not output_path.is_dir():
            raise ValueError(f"Invalid directory: {output_directory}")

    if output_file is None:
        output_file = "%(title)s"

    options = {
        "nocheckcertificate": True,
        "skip_download": True,
        "writeautomaticsub": True,
        "subtitlesformat": "ass/srt/best",
        "outtmpl": str(output_path / f"{output_file}.%(ext)s"),
    }
    return options


def create_audio_options(
    output_directory: Optional[str] = None, output_file: Optional[str] = None
) -> dict:
    """
    Create options to download audio file ONLY (no subtitles/video files), in mp3 format

    CLI command: yt-dlp -x --audio-format mp3 -o "%(title)s.%(ext)s" --compat-options no-certifi -- {URL}
    """
    if output_directory is None:
        output_path = pathlib.Path(".")
    else:
        output_path = pathlib.Path(output_directory)
        if not output_path.is_dir():
            raise ValueError(f"Invalid directory: {output_directory}")

    if output_file is None:
        output_file = "%(title)s"

    options = {
        "nocheckcertificate": True,
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
                # "ffmpeg_location": "..."
            }
        ],
        "outtmpl": str(output_path / f"{output_file}.%(ext)s"),
    }
    return options


def download_yt_file(url: str, options: dict):
    """
    Download a youtube file, with the given options
    """
    with YoutubeDL(options) as ydl:
        ydl.download([url])


if __name__ == "__main__":
    url = "https://www.youtube.com/watch?v=jvqFAi7vkBc"  # lex and sam altman

    # download audio file
    options = create_audio_options(output_directory="data")
    download_yt_file(url, options)

    # download subtitles file
    options = create_subtitles_options(output_directory="data")
    download_yt_file(url, options)
