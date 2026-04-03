# Phase 5 Research: User Interface (Gradio + FastAPI)

**Goal:** Create an interactive web interface for the `musicboxfactory` library that allows users to generate and preview baby sleep audio without writing Python code.

## Tech Stack Analysis

### FastAPI
- **Why:** Industry standard for Python APIs. Fast, asynchronous, and provides automatic Swagger docs.
- **Role:** Handles the business logic of calling `musicboxfactory`, manages temporary file lifecycle, and serves as the backend for the Gradio UI.
- **Endpoints:**
  - `POST /api/v1/generate`: Accepts audio parameters, returns a task ID or temporary file URL.

### Gradio
- **Why:** Rapid prototyping of ML and audio interfaces. Built-in audio player and simple component-based layout.
- **Role:** The user-facing dashboard.
- **Integration:** Can be mounted inside FastAPI using `gradio.mount_gradio_app`.

### uvicorn
- **Why:** High-performance ASGI server to run the FastAPI app.

## Implementation Details

### Application Structure
```text
src/musicboxfactory/
├── ...
└── ui/
    ├── __init__.py
    ├── app.py          # FastAPI app + Gradio mount
    └── logic.py        # Helper functions for generation and temp files
```

### Temporary File Management
- Use `tempfile.NamedTemporaryFile(suffix=".wav", delete=False)` for generation.
- Implement a cleanup routine (e.g., using `BackgroundTasks` in FastAPI) to delete old files after a certain period (e.g., 1 hour).
- Serve the files using FastAPI's `StaticFiles`.

### Component Mapping
- **Input Components:**
  - `gr.Textbox` for Soundfont path.
  - `gr.Dropdown` for Instruments (`music_box`, `celesta`, `bells`).
  - `gr.Radio` for Melody Type (`Preset`, `Procedural`).
  - `gr.Dropdown` for Lullaby Presets (`Twinkle Twinkle`, `Brahms' Lullaby`, etc.).
  - `gr.Dropdown` for Ambient Noise (`White`, `Pink`, `Brown`, `Womb`).
  - `gr.Slider` for Melody Volume (0.0 - 1.0).
  - `gr.Slider` for Ambient Volume (0.0 - 1.0).
  - `gr.Number` for Duration (seconds, default 30).
  - `gr.Slider` for Fade-in (seconds, default 2.0).
- **Output Components:**
  - `gr.Audio` for browser-based preview and download.

## Gaps & Risks

- **SF2 Accessibility:** The backend must have access to a `.sf2` file. Research if we can bundle a small one or provide a clear error message.
- **Fluidsynth Dependency:** The system must have `libfluidsynth3` installed. This should be clearly documented in the UI and README.
- **Concurrency:** Audio generation is CPU intensive. If many users access the UI simultaneously, it could overwhelm the server. A task queue (e.g., Celery) might be needed for a production-scale app, but for this demo, FastAPI's `BackgroundTasks` or simply `await run_in_threadpool` should suffice.

## Proposed Plans

### Plan 05-01: Scaffolding and API
- Define FastAPI app and Pydantic models for the request.
- Implement the `generate` logic that calls `Mixer`, `Synth`, etc.
- Set up static file serving for generated WAVs.
- Write unit tests for the API endpoint.

### Plan 05-02: Gradio UI and Integration
- Build the Gradio interface with the mapped components.
- Mount the Gradio app onto FastAPI.
- Implement the callback that connects the UI to the API.
- Add basic styling and instructions.
