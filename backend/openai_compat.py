"""OpenAI-compatible transcription server wrapping whisper-diarization.

Exposes ``POST /v1/audio/transcriptions`` (the OpenAI Audio API shape) so any
OpenAI-compatible client can upload audio and receive a speaker-diarized
transcript. Internally it drives ``whisper-diarization/diarize_parallel.py`` —
the same pipeline the Streamlit app and ``main.py`` use — and returns the
``.txt`` it produces. The ``serve`` subcommand runs it under uvicorn.
"""

import argparse
import asyncio
import os
import sys
import tempfile
import uuid
from pathlib import Path

import sh
from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse, Response

BACKEND_DIR = Path(__file__).resolve().parent
DIARIZE_DIR = BACKEND_DIR / "whisper-diarization"
DIARIZE_SCRIPT = "diarize_parallel.py"

# The OpenAI ``model`` field names a hosted model that has no meaning locally;
# the pipeline always runs this whisper-diarization model. Override via env.
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "large-v3")

app = FastAPI(title="whisper-diarization openai-compat")

# diarize_parallel.py writes fixed paths under its own directory and is
# compute-bound, so two concurrent runs would corrupt each other — serialize.
job_lock = asyncio.Lock()


def run_diarization(audio: Path) -> str:
    """Run the diarization pipeline on ``audio`` and return the transcript text."""
    log = audio.with_suffix(".log")
    try:
        sh.Command(sys.executable)(
            DIARIZE_SCRIPT,
            "-a",
            str(audio),
            "--whisper-model",
            WHISPER_MODEL,
            _cwd=DIARIZE_DIR,
            _out=str(log),
            _err=str(log),
        )
    except sh.ErrorReturnCode as exc:
        tail = log.read_text(errors="ignore")[-2000:] if log.exists() else str(exc)
        raise HTTPException(status_code=500, detail=f"diarization failed:\n{tail}")

    transcript = audio.with_suffix(".txt")
    if not transcript.exists():
        raise HTTPException(status_code=500, detail="diarization produced no transcript")
    return transcript.read_text(encoding="utf-8-sig").strip()


@app.post("/v1/audio/transcriptions")
async def transcriptions(
    file: UploadFile,
    response_format: str = Form(default="json"),
) -> Response:
    """Transcribe uploaded audio, OpenAI ``/v1/audio/transcriptions``-style."""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="empty audio upload")

    with tempfile.TemporaryDirectory() as tmp:
        audio = Path(tmp) / (Path(file.filename or "").name or f"{uuid.uuid4().hex}.wav")
        audio.write_bytes(data)

        async with job_lock:
            text = await asyncio.to_thread(run_diarization, audio)

        srt = audio.with_suffix(".srt")
        match response_format:
            case "text":
                return PlainTextResponse(text)
            case "srt" if srt.exists():
                return PlainTextResponse(srt.read_text(encoding="utf-8-sig"))
            case _:
                return JSONResponse({"text": text})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve", help="Run the HTTP server")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.command == "serve":
        import uvicorn

        uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
