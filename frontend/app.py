import pathlib
import time
import requests

import streamlit as st
from audiorecorder import audiorecorder

import uuid

url = "https://localhost:8000/"

tmp_path = pathlib.Path("/tmp/tmp")
tmp_path.parent.mkdir(exist_ok=True, parents=True)

st.title("Streamlit whisper")
display = st.empty()
file = st.file_uploader(label="File to transcribe: ", key="file")
audio = audiorecorder(key="recorder")
filename = None
transcribe = False

if file is not None:
    tmp_path.write_bytes(file.getvalue())
    transcribe = True

if len(audio) > 0:
    audio.export(tmp_path, format="wav")
    transcribe = True

if transcribe:
    response = requests.post(url + "upload", files={"file": open(tmp_path, "rb")})
    token = response.json()["token"]

    done = False
    progress_string = "INIT"

    while not done:
        time.sleep(0.1)
        response = requests.get(url + "progress/" + token)
        done = response.json()["done"]

        if progress_string != response.json()["progress"]:
            progress_string = response.json()["progress"]

            display.text_area(
                "progress",
                "\n".join(progress_string.splitlines()[-7:]),
                key=str(uuid.uuid4()),
                disabled=True,
                height=300,
            )

    response = requests.get(url + "result/" + token)
    display.text_area(
        "result",
        response.json()["result"],
        key=str(uuid.uuid4()),
        height=300,
    )
    transcribe = False
