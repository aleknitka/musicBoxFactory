from __future__ import annotations

import gradio as gr
from musicboxfactory.ui.logic import generate_audio
from musicboxfactory.ui.models import AudioRequest

def create_ui() -> gr.Blocks:
    """Create the Gradio interface for Music Box Factory."""
    
    with gr.Blocks(title="Music Box Factory", theme=gr.themes.Soft()) as interface:
        gr.Markdown("# 🎵 Music Box Factory")
        gr.Markdown(
            "Generate seamlessly loopable baby sleep audio using a combination of "
            "music box melodies and soothing ambient noise."
        )
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 🎹 Melody Settings")
                sf2_path = gr.Textbox(
                    label="Soundfont Path (.sf2)",
                    placeholder="/path/to/FluidR3_GM.sf2",
                    value="/usr/share/sounds/sf2/FluidR3_GM.sf2",
                    info="Required: Path to a valid soundfont file on the server."
                )
                instrument = gr.Dropdown(
                    choices=["music_box", "celesta", "bells"],
                    value="music_box",
                    label="Instrument"
                )
                melody_type = gr.Radio(
                    choices=["preset", "procedural"],
                    value="preset",
                    label="Melody Generation Mode"
                )
                melody_preset = gr.Dropdown(
                    choices=["twinkle", "brahms", "mary"],
                    value="twinkle",
                    label="Lullaby Preset",
                    visible=True
                )
                
                # Toggle visibility based on melody type
                def toggle_melody(m_type):
                    return gr.update(visible=(m_type == "preset"))
                
                melody_type.change(fn=toggle_melody, inputs=melody_type, outputs=melody_preset)

            with gr.Column():
                gr.Markdown("### 🌊 Ambient Settings")
                ambient_type = gr.Dropdown(
                    choices=["white", "pink", "brown", "womb"],
                    value="white",
                    label="Ambient Noise Type"
                )
                
                gr.Markdown("### 🎚️ Mixing & Output")
                melody_vol = gr.Slider(0.0, 1.0, value=0.5, label="Melody Volume")
                ambient_vol = gr.Slider(0.0, 1.0, value=0.2, label="Ambient Volume")
                duration = gr.Slider(10, 300, value=30, step=10, label="Duration (seconds)")
                fade_in = gr.Slider(0, 10, value=2, step=1, label="Fade-in (seconds)")

        generate_btn = gr.Button("🚀 Generate Audio", variant="primary")
        
        output_audio = gr.Audio(label="Generated Audio Preview", type="filepath")
        status_msg = gr.Markdown("")

        def on_generate(
            sf2, instr, m_type, m_preset, a_type, m_vol, a_vol, dur, f_in
        ):
            try:
                # 1. Create request model
                request = AudioRequest(
                    sf2_path=sf2,
                    instrument=instr,
                    melody_type=m_type,
                    melody_preset=m_preset,
                    ambient_type=a_type,
                    melody_vol=m_vol,
                    ambient_vol=a_vol,
                    duration=dur,
                    fade_in=f_in
                )
                
                # 2. Call generation logic
                # NOTE: In a Gradio/FastAPI mount, this is called by the FastAPI server
                # We return the absolute path, Gradio handles the file serving or conversion
                file_path = generate_audio(request)
                
                return file_path, "✅ Audio generated successfully!"
                
            except Exception as e:
                return None, f"❌ **Error:** {str(e)}"

        generate_btn.click(
            fn=on_generate,
            inputs=[
                sf2_path, instrument, melody_type, melody_preset,
                ambient_type, melody_vol, ambient_vol, duration, fade_in
            ],
            outputs=[output_audio, status_msg]
        )
        
        gr.Markdown(
            "---"
            "\n**Tip:** Ensure `libfluidsynth3` is installed on your system for audio rendering to work."
        )

    return interface
