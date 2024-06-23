from typing import cast

import pathlib
import hashlib
from io import StringIO

import streamlit as st
from audiorecorder import audiorecorder
import sh

import uuid

diarize_path = pathlib.Path("./diarize_parallel.py")

diarize_command = sh.python.bake(diarize_path)  # type: ignore

tmp_path = pathlib.Path("/tmp")
tmp_path.mkdir(exist_ok=True, parents=True)

st.title("Streamlit whisper")
display = st.empty()
file = st.file_uploader(label="File to transcribe: ", key="file")
audio = audiorecorder("Click to record", "Click to stop recording")
filename = None

if file is not None:
    filename = tmp_path / hashlib.md5(file.getvalue()).hexdigest()
    filename.write_bytes(file.getvalue())

if len(audio) > 0:
    filename = tmp_path / (hashlib.md5(audio.raw_data).hexdigest() + ".wav")
    audio.export(filename, format="wav")

if filename:
    progress = StringIO()

    p = cast(
        sh.RunningCommand,
        diarize_command(
            "-a",
            str(filename),
            "--whisper-model",
            "large-v3",
            _out=progress,
            _bg=True,
            _err=progress,
        ),
    )

    progress_string = "INIT"
    while p.is_alive():
        if progress_string != progress.getvalue():
            progress_string = progress.getvalue()
            display.text_area(
                "progress",
                "\n".join(progress_string.splitlines()[-6:]),
                key=str(uuid.uuid4()),
                disabled=True,
                height=300,
            )

    p.wait()

    display.text_area(
        "result",
        filename.with_suffix(".txt").read_text(),
        key=str(uuid.uuid4()),
        height=300,
    )
