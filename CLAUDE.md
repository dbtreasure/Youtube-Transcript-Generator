# Claude Code Instructions

## Project Overview

YouTube Transcript Generator - a CLI tool that downloads YouTube audio and transcribes it using OpenAI Whisper.

## Tech Stack

- Python 3.13+
- uv for package management
- yt-dlp for YouTube downloads
- pydub for audio chunking
- OpenAI Whisper API for transcription
- click for CLI

## Key Files

- `youtube_transcript_generator/cli.py` - Main CLI implementation
- `pyproject.toml` - Project config and dependencies
- `.env` - OpenAI API key (not committed)

## Commands

```bash
# Run the CLI
uv run yt-transcribe "https://youtube.com/watch?v=..."

# Sync dependencies
uv sync

# Add a dependency
uv add <package>
```

## Important Notes

- The `.env` file must use `override=True` in `load_dotenv()` to override shell environment variables
- Audio files >24MB are chunked into 10-minute segments due to Whisper API's 25MB limit
- `audioop-lts` is required for pydub compatibility with Python 3.13
- ffmpeg must be installed for audio conversion

## Output Structure

```
transcripts/
└── {sanitized_title}_{video_id}/
    ├── audio.mp3
    └── transcript.txt
```

## Testing

Test with any YouTube URL:
```bash
uv run yt-transcribe "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```
