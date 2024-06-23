import hashlib

from fastapi import FastAPI, HTTPException, UploadFile, BackgroundTasks

import pathlib
import sh
import asyncio

app = FastAPI(root_path="/api/")

diarize_path = pathlib.Path("./diarize_parallel.py")
diarize_command = sh.python.bake(diarize_path)  # type: ignore

output_path = pathlib.Path("./output")
output_path.mkdir(exist_ok=True, parents=True)

job_lock = asyncio.Lock()


def check_file_path(file_path: pathlib.Path):
    if not (file_path.is_relative_to(output_path) and file_path.exists()):
        raise HTTPException(status_code=400, detail="Invalid file path")


async def transcribe(filename: pathlib.Path):
    check_file_path(filename)

    if not filename.with_suffix(".done").exists():
        async with job_lock:
            p = diarize_command(
                "-a",
                str(filename),
                "--whisper-model",
                "large-v3",
                _out=filename.with_suffix(".log"),
                _err=filename.with_suffix(".log"),
                _bg=True,
            )
            while p.is_alive():
                await asyncio.sleep(1)
            p.wait()

        filename.with_suffix(".done").touch()


@app.post("/upload")
async def upload(file: UploadFile, background_tasks: BackgroundTasks):
    file_data = await file.read()
    token = hashlib.md5(file_data).hexdigest()
    filename = output_path / token
    filename.write_bytes(file_data)

    background_tasks.add_task(transcribe, filename)

    return {"token": token}


@app.get("/progress/{token}")
async def progress(token: str):
    filename = output_path / token
    check_file_path(filename)

    try:
        log = filename.with_suffix(".log").read_text(errors="ignore", encoding="utf-8")
    except FileNotFoundError:
        log = ""

    return {
        "progress": log,
        "done": (
            filename.with_suffix(".done").exists()
            and filename.with_suffix(".txt").exists()
        ),
    }


@app.get("/result/{token}")
async def result(token: str):
    filename = output_path / token
    check_file_path(filename)

    done = (
        filename.with_suffix(".done").exists() and filename.with_suffix(".txt").exists()
    )

    return {
        "result": filename.with_suffix(".txt").read_text() if done else None,
        "done": done,
    }
