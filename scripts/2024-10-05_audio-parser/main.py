import os
import pathlib
import ssl

from pydub import AudioSegment

ssl._create_default_https_context = ssl._create_unverified_context
ROOT_PATH = pathlib.Path(__file__).parent.parent


def export_audio(input_file, output_format="wav"):
    """
    Converts an audio file to the specified format and saves it.

    :param input_file: pathlib.Path to the input audio file (e.g., "sample.flac").
    :param output_format: The desired output audio format (default is "wav").
    :return: pathlib.Path to the exported audio file.
    """
    audio = AudioSegment.from_file(input_file)
    output_file = pathlib.Path(input_file).with_suffix(f".{output_format}")
    audio.export(output_file, format=output_format)
    return output_file


def extract_audio_metadata(audio_file, bit_rate=16):
    """
    Extracts metadata from an audio file, including sample width, channel count,
    duration, sample rate, and calculates the approximate file size.

    :param audio_file: pathlib.Path to the audio file (e.g., "audio.wav").
    :param bit_rate: The bit rate in bits per sample (default is 16).
    :return: A dictionary containing audio properties and the estimated file size in bytes.
    """
    audio = AudioSegment.from_file(audio_file)

    channel_count = audio.channels
    sample_width = audio.sample_width
    duration_in_sec = len(audio) / 1000
    sample_rate = audio.frame_rate

    file_size = (sample_rate * bit_rate * channel_count * duration_in_sec) / 8

    return {
        "sample_width": sample_width,
        "channel_count": channel_count,
        "duration_in_sec": duration_in_sec,
        "sample_rate": sample_rate,
        "bit_rate": bit_rate,
        "file_size_bytes": file_size,
    }


def calculate_chunk_duration(audio_file, chunk_size_mb):
    """
    Calculates the duration in seconds for each chunk to meet the desired size threshold.

    :param audio_file: pathlib.Path to the MP3 audio file.
    :param chunk_size_mb: The desired size of each chunk in megabytes (MB).
    :return: Duration in seconds for each chunk.
    """
    audio = AudioSegment.from_file(audio_file, format="mp3")

    chunk_size_bytes = chunk_size_mb * 1024 * 1024
    file_size_bytes = pathlib.Path(audio_file).stat().st_size
    num_chunks = file_size_bytes / chunk_size_bytes

    total_duration_sec = len(audio) / 1000
    chunk_duration_sec = total_duration_sec / num_chunks
    return chunk_duration_sec


def punctuation_assistant(client, ascii_transcript):
    system_prompt = """
You are a helpful assistant that adds punctuation to text.
Preserve the original words and only insert necessary punctuation such as periods,
commas, capialization, symbols like dollar sings or percentage signs, and formatting.
Use only the context provided. If there is no context provided say, 'No context provided'\n
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": ascii_transcript},
        ],
    )
    return response


if __name__ == "__main__":
    original_audio = AudioSegment.from_file(ROOT_PATH / "data/podcasts/lex_ai_sam_altman_2.mp3")
    chunk_duration = calculate_chunk_duration(
        ROOT_PATH / "data/podcasts/lex_ai_sam_altman_2.mp3", 3
    )

    chunk_duration_milliseconds = int(chunk_duration * 1000)
    start_time = 0
    i = 0

    output_dir_trimmed = ROOT_PATH / "data/podcasts/trimmed"

    if not os.path.isdir(output_dir_trimmed):
        os.makedirs(output_dir_trimmed)

    while start_time < len(original_audio):
        segment = original_audio[start_time : start_time + chunk_duration_milliseconds]
        segment.export(os.path.join(output_dir_trimmed, f"trimmed_{i:02d}.wav"), format="wav")
        start_time += chunk_duration_milliseconds
        i += 1
