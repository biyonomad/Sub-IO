# Subio Backend

A small FastAPI service that turns uploaded videos into a TXT transcript and an SRT subtitle file using local open-source Whisper. Personal local app — no accounts, no payments. Optional AI translation of the outputs into English/German/Turkish/Ukrainian via OpenAI when explicitly enabled.

## Setup

Requires Python 3.11 or newer.

```bash
cd subio-backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` if you need to change `CORS_ORIGINS` or any other setting. Defaults match the spec.

## ffmpeg requirement

Both `ffmpeg` and `ffprobe` must be on `PATH`. They are not pip packages.

- macOS: `brew install ffmpeg`
- Debian / Ubuntu: `sudo apt install ffmpeg`
- Verify: `ffmpeg -version` and `ffprobe -version`

## First Whisper model download

The first transcription downloads the configured model (default: `turbo`, ~1.5 GB) into `~/.cache/whisper/`. This is a one-time cost. Subsequent runs reuse the cached model. If you'd rather use a smaller model, set `WHISPER_MODEL=base` (or `small`, `medium`, etc.) in `.env`.

## Start the backend

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server logs `Application startup complete.` when ready. Health check:

```bash
curl http://localhost:8000/api/health
```

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/health` | Liveness probe |
| GET | `/api/config/languages` | Supported source languages |
| GET | `/api/config/presets` | The 3 SRT subtitle presets |
| GET | `/api/config/plans` | Active plans (single Local plan for personal use) |
| POST | `/api/upload` | Upload a video file (multipart `file`) |
| POST | `/api/transcribe` | Start a transcription job |
| GET | `/api/jobs/{job_id}` | Job status (poll until `done` or `failed`) |
| GET | `/api/preview/{file_id}` | Inline TXT/SRT body for in-browser preview |
| GET | `/api/download/{file_id}` | TXT/SRT as a file attachment |

### Error shape

```json
{ "error": { "code": "FILE_TOO_LARGE", "message": "Upload exceeds 5120 MB" } }
```

Codes: `FILE_TOO_LARGE`, `UNSUPPORTED_FORMAT`, `VIDEO_TOO_LONG`, `AUDIO_TOO_LONG`, `UPLOAD_NOT_FOUND`, `INVALID_LANGUAGE`, `INVALID_PRESET`, `JOB_NOT_FOUND`, `FILE_NOT_FOUND`, `INTERNAL_ERROR`.

## Test flow with a short video

```bash
# 1. Confirm config
curl http://localhost:8000/api/config/plans

# 2. Upload (use a short mp4, < 30 minutes)
curl -F "file=@sample.mp4" http://localhost:8000/api/upload
# -> { "upload_id": "...", "filename": "sample.mp4", "size_bytes": ..., "duration_seconds": ... }

# 3. Start transcription
curl -X POST http://localhost:8000/api/transcribe \
  -H "Content-Type: application/json" \
  -d '{"upload_id":"<UPLOAD_ID>","language":"auto","preset_id":"youtube_standard"}'
# -> { "job_id": "..." }

# 4. Poll
curl http://localhost:8000/api/jobs/<JOB_ID>
# repeat until "status":"done"

# 5. Preview
curl http://localhost:8000/api/preview/<srt_file_id>

# 6. Download
curl -OJ http://localhost:8000/api/download/<srt_file_id>
```

## Configuration reference

All knobs live in `.env` (see `.env.example`):

| Variable | Default | Notes |
| --- | --- | --- |
| `APP_NAME` | `Subio` | Reported by `/api/health` |
| `APP_VERSION` | `1.0.0` | |
| `HOST` / `PORT` | `0.0.0.0` / `8000` | uvicorn binding (set on the CLI) |
| `MAX_UPLOAD_SIZE_MB` | `5120` | 5 GB per upload |
| `MAX_VIDEO_DURATION_MINUTES` | `30` | Enforced after probing the upload |
| `MAX_AUDIO_DURATION_MINUTES` | `30` | Enforced after audio extraction |
| `TRANSCRIPTION_PROVIDER` | `local_whisper` | Reserved; only local Whisper is implemented |
| `WHISPER_MODEL` | `turbo` | Any name accepted by `whisper.load_model` |
| `WHISPER_DEVICE` | `auto` | `auto` picks `cuda` / `mps` / `cpu` |
| `STORAGE_DIR` | `storage` | Local disk root |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173` | Comma-separated |
| `ENABLE_TRANSLATION` | `false` | Set `true` to allow `translate=true` on `/api/transcribe` |
| `TRANSLATION_PROVIDER` | `openai` | Only `openai` is implemented |
| `OPENAI_API_KEY` | _(empty)_ | Required when `ENABLE_TRANSLATION=true` |
| `OPENAI_TRANSLATION_MODEL` | `gpt-4.1-mini` | Any chat model that supports `response_format=json_object` |

## Optional: AI translation

Set `ENABLE_TRANSLATION=true` and `OPENAI_API_KEY=...` in `.env`, then on `POST /api/transcribe` send:

```json
{ "upload_id":"...", "language":"auto", "preset_id":"youtube_standard",
  "translate": true, "target_language": "en" }
```

Supported `target_language` values: `en`, `de`, `tr`, `uk`. When the job finishes, `outputs.translated_txt` and `outputs.translated_srt` will be populated alongside the original `outputs.txt` / `outputs.srt`. The translated SRT preserves the original cue indices and timestamps exactly — only the body text changes.

`/api/config/languages` exposes `translation_available` and `supported_target_languages` so the frontend can show/hide the option dynamically.

## Notes for personal local use

Subio is a local personal app. The following simplifications are intentional and fine for personal use:

- **Local disk storage** under `STORAGE_DIR` — files are not deleted automatically; clear the `storage/` folder when it grows.
- **No rate limiting** — only you reach this server.
- **In-memory job store** — jobs and file IDs are lost on restart, so finish a transcription before stopping the server.
- **`BackgroundTasks` worker** — single-process, runs inside the API process; perfectly adequate for one user.
