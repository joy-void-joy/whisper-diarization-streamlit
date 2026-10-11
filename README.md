# whisper-diarization-streamlit

> [!IMPORTANT]
> **This project has moved to [joy-void-joy/whisper-diarize](https://github.com/joy-void-joy/whisper-diarize).**
> It's a rewrite with a new web UI (file queue, live recording), a voice bank that puts names on
> speakers, a more accurate diarization pipeline and a CLI. This repository is archived and
> kept for reference only.

Streamlit port of [whisper-diarization](https://github.com/MahmoudAshraf97/whisper-diarization)

![preview](https://github.com/joy-void-joy/whisper-diarization-streamlit/assets/56257405/5847eabc-42f6-48ea-af8c-803efd7e3f1d)

Supports diarization and long files. Does not yet support demucs music background removal as demucs' pytorch version are not compatible (TODO: make a fork of it with updated python version)

# How to use

Install this repository with ./install_poetry.sh (due to a bug in youtokentome dependency specification, poetry install will not work by itself. Once the script is run, however, poetry works correctly)

In ./backend, run `fastapi dev`
In ./frontend, run `stramlit run app.py`

Then head to https://localhost:5801, and you can upload files or record and have fast transcription and diarization.
