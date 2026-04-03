from __future__ import annotations

import os
import gradio as gr
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles

from musicboxfactory.ui.logic import generate_audio, cleanup_old_files, TEMP_DIR
from musicboxfactory.ui.models import AudioRequest, AudioResponse
from musicboxfactory.ui.interface import create_ui

app = FastAPI(
    title="Music Box Factory API",
    description="REST API to generate baby sleep audio",
    version="0.1.0",
)

# Serve generated WAV files as static files
app.mount("/static", StaticFiles(directory=str(TEMP_DIR)), name="static")

# Mount Gradio UI
ui = create_ui()
app = gr.mount_gradio_app(app, ui, path="/ui")


@app.get("/")
async def root():
    """Root endpoint for status check."""
    return {"message": "Music Box Factory API is running", "ui_path": "/ui"}


@app.post("/api/v1/generate", response_model=AudioResponse)
async def generate(request: AudioRequest, background_tasks: BackgroundTasks):
    """Generate audio and return the public URL to the WAV file."""
    try:
        # 1. Run generation
        # NOTE: Audio generation is CPU intensive; for a production app, we would
        # use a task queue like Celery. For this demo, we run it in the main thread
        # but keep it fast.
        file_path = generate_audio(request)
        
        # 2. Get relative path for static URL
        filename = os.path.basename(file_path)
        public_url = f"/static/{filename}"
        
        # 3. Schedule cleanup of old files
        background_tasks.add_task(cleanup_old_files)
        
        return AudioResponse(file_path=public_url, message="Audio generated successfully")
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
