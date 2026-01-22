# YouTube Transcript Generator

CLI tool that downloads YouTube videos as audio and generates transcripts using OpenAI's Whisper API.

## Requirements

- Python 3.13+
- [uv](https://github.com/astral-sh/uv)
- [ffmpeg](https://ffmpeg.org/) (for audio conversion)
- OpenAI API key

## Installation

```bash
git clone https://github.com/dbtreasure/Youtube-Transcript-Generator.git
cd Youtube-Transcript-Generator
uv sync
```

Create a `.env` file with your OpenAI API key:

```
OPENAI_API_KEY=sk-your-key-here
```

## Usage

```bash
uv run yt-transcribe "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Options

| Option | Description |
|--------|-------------|
| `-o, --output-dir PATH` | Base directory for output (default: `./transcripts`) |
| `--keep-audio / --no-keep-audio` | Keep or delete the audio file after transcription (default: keep) |

### Output

For each video, creates a directory under `./transcripts/`:

```
transcripts/
└── Video_Title_VIDEO_ID/
    ├── audio.mp3
    └── transcript.txt
```

## How It Works

1. Fetches video metadata using yt-dlp
2. Downloads best quality audio and converts to MP3 (192kbps)
3. If audio exceeds 24MB, splits into 10-minute chunks (Whisper API limit is 25MB)
4. Sends audio to OpenAI Whisper API for transcription
5. Combines chunk transcripts and saves to `transcript.txt`

## License

MIT
