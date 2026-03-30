# Feature Research

**Domain:** Baby sleep audio / music box synthesizer — Python library
**Researched:** 2026-03-30
**Confidence:** MEDIUM (baby sleep app ecosystem well-documented via consumer apps; Python synthesis library norms verified via existing open-source libraries; some implementation specifics extrapolated from audio DSP literature)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Music box tone synthesis (plucked tine timbre) | Core promise of the library; any "music box generator" that produces generic sine waves will feel wrong | HIGH | Short attack + exponential decay envelope per note; per-note sinusoidal with inharmonic upper partials to add warmth; Karplus-Strong or additive synthesis are the two canonical approaches |
| Exponential amplitude envelope per note | Plucked/struck instruments always use fast attack + exponential release — a linear or missing envelope sounds mechanical and harsh | MEDIUM | Attack phase is very brief (~5ms); decay time-constant should be tunable (fast decay = high notes, slow decay = low notes mirrors physical tines) |
| Built-in lullaby presets | Users expect to call `generate("twinkle_twinkle")` without supplying note sequences | LOW | At minimum: Twinkle Twinkle, Brahms' Lullaby, You Are My Sunshine — these are universal across all baby sleep products |
| Custom note sequence input | Library users (developers) will want to program arbitrary melodies | LOW | Data model: list of (pitch, duration) tuples; pitch as MIDI number or note name string; duration in beats or seconds |
| White noise generation | White noise is the single most common baby sleep sound; its absence is a hard gap | LOW | Gaussian random samples at target sample rate; trivial with numpy |
| Pink noise generation | More perceptually flat than white; preferred by many parents; expected alongside white | MEDIUM | FFT-based spectrum shaping (shape white noise in freq domain to 1/f PSD, IFFT back) or Voss-McCartney algorithm |
| Brown / Brownian noise generation | Deeper rumble; widely used in sleep machines under "fan" or "ocean" categories | MEDIUM | Cumulative sum (integration) of white noise; must normalise to prevent DC offset and clipping |
| Melody + ambient layering | The distinguishing product feature — a lullaby alone or noise alone is not the point; the blend is the product | MEDIUM | Linear mix with configurable per-layer amplitude weights; both signals normalised to [-1, 1] before mix |
| Configurable output duration | Users need 30-min, 60-min, or 8-hour files; duration is a first-class parameter | LOW | Tile/repeat melody sequence to fill duration; ambient is continuous generation |
| Seamless loop output | Audio that clicks at the loop point immediately sounds broken; sleep machines are used on repeat all night | MEDIUM | Loop point must be at a zero-crossing; melody sequence length should fit an integer number of times into total duration; ambient noise must start and end at zero-crossing (crossfade tail onto head if needed) |
| WAV file output | The universal, lossless, dependency-free output format; expected from any audio generation library | LOW | stdlib `wave` module is sufficient; 16-bit PCM at 44100 Hz is the standard |
| Configurable sample rate | 44100 Hz default; 22050 Hz option for smaller files acceptable for sleep audio | LOW | Parameterise; affects all synthesis and noise generation |

---

### Differentiators (Competitive Advantage)

Features that set this library apart from generic noise generators or MIDI renderers.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Womb / heartbeat ambient type | Distinctive and strongly associated with infant soothing; not in most generic noise libraries | MEDIUM | Low-frequency rumble (brown-weighted bass boost) + rhythmic LFO-shaped pulse at ~60 BPM; pulse is a low-sine bump, not a click |
| Per-note tonal warmth control (inharmonicity) | Makes the synthesised music box sound like a real physical instrument rather than a MIDI piano | MEDIUM | Add 2-3 upper partials with slightly stretched frequency ratios (e.g. 2.02×, 3.05× fundamental) and shorter decay envelopes; small amount goes a long way |
| Melody tempo / BPM parameter | Lets users slow down or speed up the lullaby without re-specifying notes | LOW | Scale all note durations by a factor derived from BPM; default ~60-72 BPM is sleep-inducing |
| Fade-in / fade-out on the output file | Prevents the jarring onset and offset that can wake a baby when playback starts or ends | LOW | Apply a short (1-2s) linear or raised-cosine ramp at file start and end |
| Note reverb / room tail (very short) | Adds warmth and naturalness; real music boxes resonate in a physical space | HIGH | Convolution reverb requires an IR, adding a dependency; a simple Schroeder or FDN algorithmic reverb in numpy is feasible but complex; consider deferring |
| Ambient volume envelope (pulse pattern) | Heartbeat ambient is more convincing if the low rumble subtly swells with the pulse rather than being static | MEDIUM | LFO-modulate the amplitude of the brown noise base with a ~60 BPM sinusoidal envelope |
| Multiple ambient layers simultaneously | Some sleep machines allow mixing e.g. pink noise + heartbeat; adds flexibility | MEDIUM | Extend the layer mixer to accept a list of ambient types, each with its own weight |
| Preset metadata (name, BPM, key, description) | Enables library consumers to display preset info in a UI without hard-coding it | LOW | Dataclass or TypedDict per preset; negligible implementation cost |

---

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems and are explicitly out of scope.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Audio playback / `play()` function | "Just play it" is the most natural thing to ask | Requires `sounddevice`, `pyaudio`, or `pygame` — platform-dependent C extensions that break on headless systems, Docker, CI, and embedded targets; defeats the library-first model | Document one-liner using `sounddevice` or `subprocess + aplay`; keep the library output-only |
| MP3 / OGG output | Smaller files are appealing | Requires `pydub`/`ffmpeg` or `mutagen` — large dependencies; MP3 encoding has patent history; WAV is lossless and universally accepted | WAV is sufficient; users who need MP3 can run ffmpeg on the output |
| Real-time / streaming audio generation | Feels more flexible; useful for live playback | Requires a fundamentally different architecture (ring buffers, callback threads, latency management); incompatible with the current render-to-array model | Render a long file (e.g. 8 hours) and play it with any player |
| MIDI file input | Power users want to import existing MIDI arrangements | Adds `mido` or `pretty_midi` dependency; MIDI tempo tracks and channel handling are non-trivial edge cases; out of scope for v1 | Note sequence tuples cover the same musical ground for the target use case |
| Rain, ocean, nature sounds | Wider ambient variety is appealing | Nature sounds require either audio samples (files) or complex stochastic physical modelling; fundamentally different from signal-generated noise; out of scope | The white / pink / brown / womb set covers the spectrum of sleep-relevant textures |
| CLI interface | Makes the library immediately usable from terminal | A CLI is a separate concern; entrypoint registration, argparse, help text — adds surface area that must be maintained; library API is primary | Users can write a 5-line wrapper script; document an example |
| Audio normalisation / loudness targeting (LUFS) | Professional audio quality | `pyloudnorm` or equivalent adds dependency; LUFS targeting is overkill for a sleep sound generator | Simple peak normalisation to 90% of full scale is sufficient and pure-numpy |
| Melody harmonisation (auto-chords) | Enriches the sound without user specifying chords | Requires music theory logic (key detection, chord selection) — significant complexity; wrong chords are worse than no chords | Single-voice melody is authentic to the music box instrument |

---

## Feature Dependencies

```
WAV file output
    └──requires──> Sample rate parameter
    └──requires──> Configurable output duration

Melody layer
    └──requires──> Music box tone synthesis
                       └──requires──> Exponential amplitude envelope per note
    └──requires──> Built-in lullaby presets OR custom note sequence input
    └──enhanced-by──> Per-note inharmonicity (warmth control)
    └──enhanced-by──> Melody tempo / BPM parameter

Ambient layer
    └──requires──> At least one noise type (white / pink / brown)
    └──enhanced-by──> Womb / heartbeat pulse type
                           └──requires──> Brown noise base
                           └──requires──> LFO amplitude envelope

Melody + ambient layering
    └──requires──> Melody layer
    └──requires──> Ambient layer

Seamless loop output
    └──requires──> Melody + ambient layering (or either layer alone)
    └──requires──> Zero-crossing enforcement at loop boundary

Fade-in / fade-out
    └──requires──> WAV file output (applied as post-process on final array)

Womb / heartbeat type
    └──requires──> Brown noise generation
    └──enhanced-by──> Ambient volume envelope (pulse modulation)
```

### Dependency Notes

- **Melody layer requires tone synthesis with envelope:** A music box tone without an exponential decay envelope is just a sine wave beep — the envelope IS the timbre.
- **Seamless loop requires both melody duration and loop boundary management:** Melody sequence must be tiled to exactly fill the requested duration; ambient noise must be generated with zero-crossing start/end.
- **Womb/heartbeat requires brown noise base:** The ambient rumble beneath the heartbeat pulse is brown-noise-shaped; pink or white would sound wrong for this type.
- **Inharmonicity enhances but does not require tone synthesis:** It is an additive refinement on top of a working fundamental; implement after the basic tone sounds correct.
- **Fade-in/fade-out has no upstream dependencies beyond final audio array:** It is a post-process step applied to whatever is already rendered; safe to add after core is working.

---

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the core concept and deliver value.

- [ ] Music box tone synthesis — short attack + exponential decay sinusoidal tone per note; this is the core differentiator and must be right
- [ ] Exponential amplitude envelope per note — baked into tone synthesis; not separable
- [ ] White noise generation — simplest ambient; validates the layer mixing model
- [ ] Pink noise generation — second most common sleep ambient; validates spectrum shaping
- [ ] Brown noise generation — enables womb/heartbeat type; third ambient pillar
- [ ] Built-in lullaby presets (minimum 3: Twinkle Twinkle, Brahms' Lullaby, one more) — enables zero-config usage
- [ ] Custom note sequence input — enables developer use case
- [ ] Melody + ambient layering with configurable relative volumes — the product promise
- [ ] WAV file output, configurable duration — deliverable artifact
- [ ] Seamless loop at loop boundary — correctness requirement; a clicking loop is broken

### Add After Validation (v1.x)

Features to add once core is working and used.

- [ ] Womb / heartbeat ambient type — high value for infant use case; builds on brown noise already in v1
- [ ] Fade-in / fade-out on output file — low complexity post-process; quality-of-life improvement
- [ ] Per-note inharmonicity / warmth control — tonal quality improvement; add once basic synthesis is validated
- [ ] Melody tempo / BPM parameter — user-facing control; simple duration scaling
- [ ] Preset metadata dataclass — useful for library consumers building UIs
- [ ] Multiple simultaneous ambient layers — flexibility upgrade once single-layer model is validated

### Future Consideration (v2+)

Features to defer until product-market fit established and user feedback collected.

- [ ] Note reverb / room tail — high complexity; requires algorithmic reverb implementation in numpy; validate that users want it before investing
- [ ] Ambient volume envelope / pulse modulation — refinement of heartbeat type; defer until heartbeat basic is in place and validated
- [ ] Additional lullaby presets beyond 3 — accumulate based on user requests rather than guessing

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Music box tone synthesis (envelope) | HIGH | HIGH | P1 |
| White noise generation | HIGH | LOW | P1 |
| Pink noise generation | HIGH | MEDIUM | P1 |
| Brown noise generation | HIGH | MEDIUM | P1 |
| Built-in lullaby presets | HIGH | LOW | P1 |
| Custom note sequence input | HIGH | LOW | P1 |
| Melody + ambient layering | HIGH | MEDIUM | P1 |
| WAV file output | HIGH | LOW | P1 |
| Seamless loop | HIGH | MEDIUM | P1 |
| Configurable duration | HIGH | LOW | P1 |
| Womb / heartbeat ambient | MEDIUM | MEDIUM | P2 |
| Fade-in / fade-out | MEDIUM | LOW | P2 |
| Per-note inharmonicity | MEDIUM | MEDIUM | P2 |
| BPM / tempo parameter | MEDIUM | LOW | P2 |
| Preset metadata | LOW | LOW | P2 |
| Multiple simultaneous ambients | LOW | MEDIUM | P2 |
| Note reverb / room tail | MEDIUM | HIGH | P3 |
| Additional lullaby presets | LOW | LOW | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor / Ecosystem Analysis

This is a Python library, not a consumer app — the closest comparators are existing Python audio synthesis libraries and consumer baby sleep apps. Both inform the feature set from different angles.

| Feature | Consumer Sleep Apps (e.g. BabySnooze, Sound Sleeper) | Generic Python Audio Libs (e.g. PySynth, synthesizer) | musicboxfactory Approach |
|---------|------------------------------------------------------|-------------------------------------------------------|--------------------------|
| Music box tones | Pre-recorded samples, not synthesised | Generic waveform oscillators, no instrument-specific timbre | Synthesised plucked tine timbre with attack + decay envelope |
| Noise types | White, pink, brown, fan, rain, womb — typically 40+ sounds | Not a focus; some have white noise utility | White, pink, brown, womb/heartbeat — signal-generated only, no samples |
| Melody presets | Pre-recorded audio files | ABC notation or MIDI input | Note sequences (tuples); presets as built-in data |
| Layering | UI mixer in app | Not addressed | Programmatic mix with configurable weights |
| Loop quality | Seamless (critical for sleep apps) | Not addressed | Explicit zero-crossing and tile-fill guarantee |
| Output format | Streams to speaker; no file export | WAV file | WAV file only |
| API style | Mobile app UI | Script/CLI | Python library — callable functions |
| Dependencies | None for user | Varies; some require heavy deps | numpy + stdlib wave only |

**Key insight:** Consumer apps have solved the product problem (what sounds work for sleep) but not the developer library problem (programmatic, dependency-light generation). Existing Python audio libraries solve synthesis but not the sleep-specific timbre and ambient mix. This library occupies the gap.

---

## Sources

- [AI Music for Baby Sleep — Soundverse AI, 2026](https://www.soundverse.ai/blog/article/ai-music-for-baby-sleep-white-noise-apps-1106)
- [BabySnooze: White Noise App — App Store](https://apps.apple.com/us/app/babysnooze-white-noise/id6755329608)
- [Sound Sleeper Baby White Noise — App Store](https://apps.apple.com/us/app/sound-sleeper-baby-white-noise/id507967709)
- [White Noise Baby Sleep Sounds — Google Play](https://play.google.com/store/apps/details?id=com.amikulich.babysleep&hl=en_US)
- [Karplus-Strong String Synthesis — Wikipedia](https://en.wikipedia.org/wiki/Karplus%E2%80%93Strong_string_synthesis)
- [Karplus-Strong with Python — Frolian's Blog](https://flothesof.github.io/Karplus-Strong-algorithm-Python.html)
- [Synthesizing Bells — Sound On Sound](https://www.soundonsound.com/techniques/synthesizing-bells)
- [Additive Synthesis: Risset's Bell — UCSD](http://msp.ucsd.edu/techniques/v0.11/book-html/node71.html)
- [colorednoise: Python pink/brown noise — GitHub](https://github.com/felixpatzelt/colorednoise)
- [Generating White, Pink, Brown Noise in Python — Medium](https://medium.com/@smrati.katiyar/generating-white-ping-brown-blue-noise-using-python-and-save-in-a-audio-file-2db47220cf8e)
- [TIL How To Make Brown Noise in Python — Mat Duggan](https://matduggan.com/til-how-to-make-brown-noise-in-python/)
- [Seamless Audio Loop Techniques — FrontierSoundFX](https://www.frontiersoundfx.com/how-to-seamlessly-loop-any-ambience-audio-file/)
- [Making Audio Loops — Audacity Support](https://support.audacityteam.org/music/working-with-audio-loops/making-audio-loops)
- [PySynth — Python Music Synthesizer](https://mdoege.github.io/PySynth/)
- [python-acoustics generator module — GitHub](https://github.com/python-acoustics/python-acoustics/blob/master/acoustics/generator.py)

---
*Feature research for: Baby sleep audio / music box synthesizer — Python library*
*Researched: 2026-03-30*
