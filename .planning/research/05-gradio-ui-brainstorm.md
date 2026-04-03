# Research: Build Gradio UI with FastAPI

**Status:** Draft
**Context:** Creating a web interface for `musicboxfactory` library to allow non-technical users to generate audio.

## Goals
- Provide an interactive UI (Gradio) for parameter selection.
- Expose a REST API (FastAPI) for programmatic access.
- Enable WAV generation and preview in the browser.

## Tech Stack
- **FastAPI**: Backend web framework.
- **Gradio**: UI framework.
- **uvicorn**: ASGI server for running the app.
- **musicboxfactory**: The core library.

## API Design
`POST /generate`
- **Request Body**:
  - `sf2_path`: string
  - `instrument`: string (music_box, celesta, bells)
  - `melody_type`: string (preset, sequence, procedural)
  - `melody_preset`: string (twinkle, brahms, mary)
  - `melody_sequence`: list of (note, duration) — optional
  - `ambient_type`: string (white, pink, brown, womb)
  - `melody_vol`: float (0.0 - 1.0)
  - `ambient_vol`: float (0.0 - 1.0)
  - `duration`: float (seconds)
  - `fade_in`: float (seconds)
- **Response**:
  - `file_path`: string (link to temporary WAV)

## UI Layout (Gradio)
1. **Inputs Group**:
   - Textbox: Soundfont Path (default value or picker).
   - Dropdown: Instrument (music_box, celesta, bells).
   - Radio: Melody Source (Preset, Procedural).
   - Dropdown: Lullaby Preset (Twinkle, etc.).
   - Dropdown: Ambient Type (White, Pink, Brown, Womb).
   - Slider: Melody Volume.
   - Slider: Ambient Volume.
   - Number: Duration (seconds).
2. **Action**:
   - Button: "Generate Audio".
3. **Output**:
   - Audio: Generated WAV player.
   - File: Download link.

## Implementation Details
- **Gradio in FastAPI**: Use `gradio.mount_gradio_app(app, io, path="/ui")`.
- **Temp Storage**: Use `tempfile` for audio generation and clean up after some time.
- **Concurrency**: Audio generation is CPU-bound but should be fast (~seconds). Use a thread pool or simple async.

## Questions/Risks
- **SF2 Path**: How to handle it? Users might not have a .sf2 file locally. Should we bundle a small free one?
- **libfluidsynth3**: The system must have the C library installed for the backend to work.
- **Deployment**: Where would this be hosted? HF Spaces? Local only?
