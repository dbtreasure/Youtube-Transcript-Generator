import re
import sys
from pathlib import Path

import click
from dotenv import load_dotenv
from openai import OpenAI
from pydub import AudioSegment
import yt_dlp

MAX_FILE_SIZE_MB = 24
CHUNK_DURATION_MS = 10 * 60 * 1000  # 10 minutes in milliseconds


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use as a directory/file name."""
    sanitized = re.sub(r'[<>:"/\\|?*]', "", name)
    sanitized = sanitized.strip(". ")
    sanitized = re.sub(r"\s+", "_", sanitized)
    return sanitized[:200]


def get_video_info(url: str) -> dict:
    """Extract video info without downloading."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


def download_audio(url: str, output_dir: Path) -> Path:
    """Download audio from YouTube video."""
    output_template = str(output_dir / "audio.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "outtmpl": output_template,
        "quiet": False,
        "no_warnings": False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return output_dir / "audio.mp3"


def get_file_size_mb(path: Path) -> float:
    """Get file size in megabytes."""
    return path.stat().st_size / (1024 * 1024)


def split_audio(audio_path: Path, output_dir: Path) -> list[Path]:
    """Split audio file into chunks if it exceeds the size limit."""
    file_size_mb = get_file_size_mb(audio_path)

    if file_size_mb <= MAX_FILE_SIZE_MB:
        return [audio_path]

    click.echo(f"Audio file is {file_size_mb:.1f} MB, splitting into chunks...")

    audio = AudioSegment.from_mp3(audio_path)
    chunks = []
    chunk_num = 0

    for start_ms in range(0, len(audio), CHUNK_DURATION_MS):
        chunk = audio[start_ms : start_ms + CHUNK_DURATION_MS]
        chunk_path = output_dir / f"audio_chunk_{chunk_num:03d}.mp3"
        chunk.export(chunk_path, format="mp3", bitrate="192k")
        chunks.append(chunk_path)
        chunk_num += 1

    click.echo(f"Split into {len(chunks)} chunks")
    return chunks


def transcribe_audio_file(audio_path: Path, client: OpenAI) -> str:
    """Transcribe a single audio file using OpenAI Whisper API."""
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text",
        )
    return transcript


def transcribe_audio(audio_path: Path, output_dir: Path, client: OpenAI) -> str:
    """Transcribe audio, chunking if necessary."""
    chunks = split_audio(audio_path, output_dir)

    if len(chunks) == 1:
        return transcribe_audio_file(chunks[0], client)

    transcripts = []
    for i, chunk_path in enumerate(chunks):
        click.echo(f"Transcribing chunk {i + 1}/{len(chunks)}...")
        transcript = transcribe_audio_file(chunk_path, client)
        transcripts.append(transcript)
        if chunk_path != audio_path:
            chunk_path.unlink()

    return " ".join(transcripts)


@click.command()
@click.argument("url")
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("./transcripts"),
    help="Base directory for output (default: ./transcripts)",
)
@click.option(
    "--keep-audio/--no-keep-audio",
    default=True,
    help="Keep the downloaded audio file (default: keep)",
)
def main(url: str, output_dir: Path, keep_audio: bool):
    """Download YouTube audio and generate transcript.

    URL: The YouTube video URL to process.
    """
    load_dotenv(override=True)

    client = OpenAI()

    click.echo(f"Fetching video info for: {url}")
    try:
        info = get_video_info(url)
    except Exception as e:
        click.echo(f"Error fetching video info: {e}", err=True)
        sys.exit(1)

    title = info.get("title", "unknown_video")
    video_id = info.get("id", "unknown_id")
    click.echo(f"Video title: {title}")

    safe_title = sanitize_filename(title)
    video_dir = output_dir / f"{safe_title}_{video_id}"
    video_dir.mkdir(parents=True, exist_ok=True)
    click.echo(f"Output directory: {video_dir}")

    click.echo("Downloading audio...")
    try:
        audio_path = download_audio(url, video_dir)
    except Exception as e:
        click.echo(f"Error downloading audio: {e}", err=True)
        sys.exit(1)

    click.echo(f"Audio downloaded: {audio_path}")

    click.echo("Transcribing audio with OpenAI Whisper...")
    try:
        transcript = transcribe_audio(audio_path, video_dir, client)
    except Exception as e:
        click.echo(f"Error transcribing audio: {e}", err=True)
        sys.exit(1)

    transcript_path = video_dir / "transcript.txt"
    transcript_path.write_text(transcript)
    click.echo(f"Transcript saved: {transcript_path}")

    if not keep_audio:
        audio_path.unlink()
        click.echo("Audio file removed.")

    click.echo("Done!")


if __name__ == "__main__":
    main()
