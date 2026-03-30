# Pitfalls Research

**Domain:** Python audio synthesis library — music box melody + ambient noise, WAV output
**Researched:** 2026-03-30
**Confidence:** HIGH (core numpy/WAV mechanics), MEDIUM (perceptual quality guidance)

---

## Critical Pitfalls

### Pitfall 1: Loop-Point Click from Non-Zero Sample Value at Boundary

**What goes wrong:**
The generated WAV ends at a non-zero amplitude. When a player loops the file, the jump from the final sample value back to the first sample value creates a discontinuity that audible as a click or pop. For sleep audio played on repeat for hours, even a subtle click is disqualifying.

**Why it happens:**
Developers render the audio to the requested duration (e.g. 60 minutes) and write it out without checking whether the waveform ends near zero. Ambient noise signals are random and end at an arbitrary amplitude. Music box notes scheduled near the end of the file may be mid-decay. Neither condition is zero-crossing-aligned automatically.

**How to avoid:**
- Apply a short fade-out (2–10 ms, i.e. 88–441 samples at 44100 Hz) at the very end of the file so the signal reaches exactly 0.0 before the final sample. A symmetric fade-in at the start keeps the matched boundary.
- For music box notes, ensure no note's envelope extends beyond the render boundary; if it does, either truncate or extend the render length to complete the decay naturally.
- Add a post-render assertion: `assert abs(audio[-1]) < 1e-4` before writing.
- For noise layers, a short crossfade of the tail into the head produces a truly seamless loop (Audacity's "Crossfade Clips" technique: ~100–200 samples).

**Warning signs:**
- Listening to a looped playback of the generated file produces a periodic tick or thump.
- The last sample value printed via `audio[-1]` is far from 0.
- Phase mismatch is especially audible on brown/womb noise due to its strong low-frequency content.

**Phase to address:** Tone synthesis phase (note rendering) and WAV output phase (loop boundary logic).

---

### Pitfall 2: Silent Integer Overflow When Converting float64/float32 to int16

**What goes wrong:**
Mixed audio exceeds the float range [-1.0, 1.0] before conversion, or is not explicitly clipped. NumPy's direct cast `(audio * 32767).astype(np.int16)` wraps overflowing values silently — values slightly above 1.0 become large negative numbers, producing extreme crackling distortion. NumPy does **not** warn about overflow in array operations; only scalar operations trigger warnings.

**Why it happens:**
Additive mixing of melody + ambient layers sums their amplitudes. Two layers each at 0.7 amplitude sum to 1.4, which overflows int16. Developers test with individual layers at safe levels but don't test the combined signal.

**How to avoid:**
- Always normalize or clip after mixing, before conversion: `np.clip(mixed, -1.0, 1.0)` or divide by the peak: `mixed /= np.max(np.abs(mixed)) + 1e-9`.
- Prefer normalization to a target peak (e.g. -1 dBFS = 0.891 amplitude) rather than hard clipping, to preserve dynamics.
- Work in float64 throughout synthesis; convert to int16 only at the final WAV write step.
- Add a unit test that generates both layers at maximum configured amplitude and asserts the final array contains no values outside [-1.0, 1.0] before conversion.

**Warning signs:**
- Crackling or extreme distortion in the output, especially louder at higher mix levels.
- `np.any(np.abs(mixed) > 1.0)` returns True before the write step.
- The symptom is worse when both melody and ambient are configured loud simultaneously.

**Phase to address:** Mixing/layering phase. Establish normalization as a required step in the render pipeline before WAV write.

---

### Pitfall 3: Brown Noise DC Drift from Unbounded Cumulative Sum

**What goes wrong:**
The naive brown noise implementation uses `np.cumsum(white_noise)`, which performs a random walk (Brownian motion). Over a 60-minute render, the signal drifts far from zero — potentially saturating the entire range. After normalization the result sounds correct, but the signal spends most of its time at extreme values near ±1.0, losing the perceptual character of brown noise.

**Why it happens:**
Brownian noise is mathematically defined as the integral of white noise, which has no mean-reverting property. For short buffers the drift is manageable; for long buffers (millions of samples) it becomes severe.

**How to avoid:**
- Use a leaky integrator instead of raw cumsum: `y[i] = alpha * y[i-1] + white[i]` where `alpha ≈ 0.998–0.999`. This creates Ornstein-Uhlenbeck noise, which is audibly equivalent to brown noise but stays bounded.
- Alternatively, generate brown noise via FFT shaping (power ∝ 1/f²): generate white noise in the frequency domain, scale by 1/f², inverse FFT back. This produces stationary noise with correct spectrum and no drift.
- After generation, always remove DC offset: `signal -= signal.mean()` before normalization.

**Warning signs:**
- The raw cumsum output, when plotted, shows a monotone ramp or large-scale drift rather than a symmetric waveform.
- After normalization, most sample values cluster near ±1.0 rather than being normally distributed.
- The audio sounds more like a slow pan or rumble building to a wall rather than constant texture.

**Phase to address:** Ambient noise generation phase.

---

### Pitfall 4: Pink Noise Spectral Inaccuracy at Low Frequencies

**What goes wrong:**
FFT-based pink noise generation produces correct high-frequency spectrum but is inaccurate at very low frequencies (below ~20 Hz and in the lowest audible octave) because the FFT bin resolution is insufficient. For short buffer sizes the low-frequency bins have too few samples to express true 1/f behavior. The result sounds "thin" or lacks the warmth that pink noise is valued for in sleep audio.

**Why it happens:**
Pink noise requires power proportional to 1/f across all frequencies. At low frequencies, a short FFT has only a few bins. When generating a 60-minute file as a single FFT operation the resolution is fine, but generating it in chunks (for memory reasons) loses low-frequency accuracy at chunk boundaries.

**How to avoid:**
- Generate the entire noise signal in one FFT pass rather than in chunks; for a 60-minute file at 44100 Hz this is ~158 million samples — feasible in memory on modern hardware (~600 MB float32).
- If chunked generation is required, use a proper IIR filter implementation (Butterworth cascade approximating 1/f slope) rather than per-chunk FFT. The `colorednoise` library (PyPI: `colorednoise`) implements FFT-based generation correctly with explicit low-frequency handling.
- Verify spectrum accuracy by computing `np.fft.rfft` on the output and checking the slope is -10 dB/decade (pink = -3 dB/octave).

**Warning signs:**
- The first 2–3 seconds of a chunk-generated file sound slightly brighter or thinner than the rest.
- Spectral analysis shows a flat region at low frequencies rather than a rising 1/f slope.

**Phase to address:** Ambient noise generation phase.

---

### Pitfall 5: Music Box Tine Timbre Sounds Like a Pure Sine (Too Clinical)

**What goes wrong:**
A simple `amplitude * np.sin(2 * np.pi * freq * t) * envelope` produces a pure tone that sounds nothing like a real music box tine. Real tines have inharmonic partials: prominent overtones at approximately 2.76×, 5.4×, and 8.9× the fundamental (not integer multiples), plus a slight metallic attack transient. A pure sine decay sounds sterile and toy-like.

**Why it happens:**
Developers reach for the simplest possible implementation first. The single-sinusoid exponential decay model is mathematically tidy and covers the core spec ("plucked tone with decay") but does not capture the inharmonic character that makes the sound recognizable.

**How to avoid:**
- Add 2–4 inharmonic partials using additive synthesis. A practical approximation for music box tines:
  - Fundamental: amplitude 1.0
  - 2nd partial: ~2.756× fundamental, amplitude 0.25–0.35
  - 3rd partial: ~5.4× fundamental, amplitude 0.08–0.12
  - Each partial has its own shorter decay constant (higher partials decay faster)
- Alternatively, use a brief noise burst (2–5 ms) multiplied by a sharp attack envelope to simulate the mechanical pluck impact before the tone settles.
- Tune partial ratios empirically by comparing against recordings of real music boxes; published research on marimba/xylophone bar physics gives good starting ratios.

**Warning signs:**
- The output sounds like a theremin or pure tone test signal rather than a music box.
- Frequency analysis of the output shows a single spectral peak per note with no sidelobes.
- Subjective "warmth" and "shimmer" are absent.

**Phase to address:** Tone synthesis phase — establish target timbre early and validate against perceptual reference.

---

### Pitfall 6: Karplus-Strong Tuning Inaccuracy at High Frequencies

**What goes wrong:**
If Karplus-Strong is used for music box tone synthesis, the delay line length must be an integer number of samples (`delay = sample_rate / frequency`). Rounding to the nearest integer introduces pitch error. At A4 (440 Hz, delay ≈ 100 samples) the error is ±0.5%, which is perceptible. At higher frequencies (C6 = 1047 Hz, delay ≈ 42 samples) rounding to integer creates a tuning error of over 1%, which is clearly out of tune.

**Why it happens:**
Integer array indexing forces integer delay lengths. Developers test with middle-register notes, where the error is below JND, and don't notice the problem until high notes are tested.

**How to avoid:**
- If using Karplus-Strong, implement a first-order allpass filter for fractional delay correction (Jaffe-Smith 1983 method), keeping the fractional delay `d` in the range [0.418, 1.418] for numerical stability.
- Alternatively, avoid Karplus-Strong entirely for music box. Additive synthesis with inharmonic sinusoids (Pitfall 5) has exact frequency control with no delay-line issues and is simpler to implement correctly.
- For the melody's note range (typically C4–C6 for lullabies), verify tuning accuracy by computing the actual frequency from the synthesized waveform using zero-crossing period measurement.

**Warning signs:**
- High notes in the melody sound slightly sharp or flat compared to a reference tone.
- Notes above C5 sound noticeably out of tune while middle-register notes are fine.
- Period measurement of synthesized tone does not match expected fundamental period.

**Phase to address:** Tone synthesis phase — choose synthesis method before implementation; validate tuning across the full musical range.

---

### Pitfall 7: WAV Header Written with Wrong Parameters (wave Module Traps)

**What goes wrong:**
Python's `wave` module requires parameters to be set in a specific way. Common mistakes:
- `setsampwidth()` takes bytes not bits (2 for 16-bit, not 16).
- `setnchannels()` must be set before `setnframes()` or the header is wrong.
- `writeframes()` requires bytes already encoded as little-endian int16; passing a raw numpy array without `.tobytes()` causes corrupt output.
- Not closing the wave writer (or not using it as a context manager) leaves the header's frame count field at 0, producing files that some players refuse to open.

**Why it happens:**
The `wave` module API is dated and not Pythonic. Its parameter names (`sampwidth`, `nchannels`, `framerate`) are terse and the units are non-obvious. The module does not raise errors for many wrong inputs — it just writes bad data.

**How to avoid:**
- Always use `wave.open()` as a context manager (`with wave.open(...) as w`).
- Set parameters explicitly and in order: nchannels → sampwidth → framerate → (write frames).
- Convert numpy array to int16 bytes explicitly: `(audio * 32767).astype('<i2').tobytes()` (little-endian int16).
- Write a single test after first implementation that opens the written file and reads back the header parameters, asserting they match what was intended.
- Consider `scipy.io.wavfile.write()` as an alternative — it accepts numpy arrays directly, handles the header automatically, and is harder to misuse.

**Warning signs:**
- Output file opens in one player but not another.
- File duration reported by `soxi` or `ffprobe` is 0 seconds or wildly wrong.
- Audio plays back at wrong speed (wrong sample rate in header).

**Phase to address:** WAV output phase — first pass must include a round-trip read-back test.

---

### Pitfall 8: Note Scheduling Produces Click at Note Onset

**What goes wrong:**
When a note starts at a non-zero phase of its sine wave (i.e. the sine function is not at 0 at t=0 of the note's window), the sudden onset creates a click. This is the same discontinuity problem as loop points but within the file. It is especially audible in music box tones because they start from silence.

**Why it happens:**
`np.sin(2 * np.pi * freq * t)` where `t` starts at a non-integer cycle boundary produces a non-zero initial value. If the amplitude envelope has an instant attack (rises from 0 to full immediately), but the sine value at t=0 is not 0, there is a step from silence to a non-zero value.

**How to avoid:**
- Use a short attack window (5–10 ms linear or raised cosine ramp) so the note amplitude rises from 0 even if the sine is non-zero at t=0. This is standard in all synthesis.
- Alternatively, always start the sine phase at 0: `np.sin(2 * np.pi * freq * (t - t[0]))` rather than using global sample indices.
- For additive synthesis with multiple partials, each partial naturally starts at 0 phase if `t` starts at 0 for each note.

**Warning signs:**
- Individual notes produce a faint tick at their beginning when played in isolation.
- The click is more audible for lower-frequency notes (where the non-zero initial value represents a larger fraction of the waveform amplitude).

**Phase to address:** Tone synthesis phase — build attack envelope into the first implementation, not as a later refinement.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Single sinusoid per note (no partials) | Simple, fast to implement | Tones sound clinical, not music-box-like; requires rewrite to add inharmonic character | MVP proof-of-concept only; not for any user-facing release |
| Raw `np.cumsum()` for brown noise | One-line implementation | DC drift at long durations; normalization masks but does not fix the spectral distortion | Never for long-form output (>10 sec) |
| Hard clip at ±1.0 instead of normalize | Prevents overflow | Audible distortion if any peaks exceed 1.0 by more than ~3 dB | Only acceptable if mix levels are mathematically guaranteed to stay below 1.0 |
| Skip fade-out at loop boundary | Saves ~10 lines of code | Click on every loop repetition; disqualifying for sleep audio use case | Never acceptable |
| Use `scipy.io.wavfile.write` instead of `wave` | Simpler, safer API | Adds scipy dependency (already likely needed for noise filtering) | Always acceptable — the API is strictly better than `wave` for this use case |
| Generate noise per-chunk to save memory | Handles arbitrary durations | Spectral discontinuities at chunk boundaries; incorrect pink noise spectrum | Only if chunk size ≥ several seconds and a proper overlap-add strategy is implemented |

---

## Integration Gotchas

This project has no external service integrations. The relevant "integration" concerns are internal: numpy arrays entering the wave/scipy WAV writer.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| numpy float64 → `wave.writeframes()` | Pass raw array bytes without dtype conversion; produces garbage audio | Convert: `(audio * 32767).astype('<i2').tobytes()` |
| numpy float64 → `scipy.io.wavfile.write` | Pass float64 when int16 is required for 16-bit output | Convert to int16 first, or pass float32 (scipy accepts float32 for 32-bit WAV) |
| Mixed-rate synthesis (e.g. envelope at note rate, signal at sample rate) | Envelope computed at note-resolution, applied to wrong-length signal array | Always generate envelope at sample resolution matching the signal array length |
| Noise layer + melody layer addition | Shape mismatch when durations differ by rounding | Enforce same array length before addition; pad shorter array with zeros |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Python for-loop over samples | Extremely slow synthesis (minutes for 1-hour file) | Vectorize all synthesis with numpy array operations from the start | Any duration > ~1 second |
| Generating noise in float64 for 60-min file | ~2.5 GB memory for a single channel | Use float32 for noise buffers; synthesis precision is not lost | Files > ~10 minutes |
| Per-note FFT for Karplus-Strong | O(N log N) per note × number of notes | Use time-domain ring buffer; or use additive synthesis (no FFT needed) | Melodies with > ~50 notes |
| Re-generating noise on every call | Slow API if user calls the function repeatedly | Accept a seed parameter; use `np.random.default_rng(seed)` for reproducible, cacheable noise | Repeated calls in testing or batch generation |

---

## Security Mistakes

Not applicable — this is an offline audio generation library with no network access, user authentication, or file input from untrusted sources. The only user-facing input is note sequences (pitch names + durations), which should be validated against an allowed pitch set to prevent unexpected behavior.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Accepting arbitrary frequency floats without range check | User-provided 0 Hz or negative frequency causes division by zero or numerical instability in synthesis | Validate frequency is in [20, 20000] Hz range at API boundary |
| Accepting negative or zero duration | Creates zero-length or negative-length numpy array, causing cryptic downstream errors | Validate duration > 0 at API entry point |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No way to set random seed | Non-reproducible output; user cannot regenerate identical file | Accept optional `seed: int` parameter; document that same seed + same parameters = identical output |
| Relative volume parameters are raw linear amplitudes | Unintuitive; users think 0.5 = "half volume" but perceptually it sounds like ~70% due to dB scaling | Accept linear 0.0–1.0 but document the perceptual behavior, or accept dB values (negative float) |
| WAV output is 16-bit PCM regardless of input | Fine for most uses; limits headroom during mixing | Document the 16-bit output; or expose a `bit_depth=16/24` parameter for users who need higher quality |
| No duration validation | User requests 0.1 second file; music box notes longer than duration are silently truncated | Warn when note events extend beyond the rendered duration |

---

## "Looks Done But Isn't" Checklist

- [ ] **Seamless loop:** Plays the output file on repeat 20+ times without audible click at the loop boundary — verify `audio[0]` and `audio[-1]` are both near 0.
- [ ] **Tuning accuracy:** Every note in the chromatic scale from C4–C6 is within ±5 cents of equal temperament — verify by zero-crossing frequency measurement.
- [ ] **Music box timbre:** Output includes inharmonic partials, not just a pure sine — verify by spectral analysis showing multiple peaks per note.
- [ ] **Noise spectrum:** Pink noise slope is -3 dB/octave and brown noise is -6 dB/octave — verify by computing PSD of generated noise.
- [ ] **No overflow in mixing:** Combined melody + ambient at maximum configured levels does not clip — verify `np.max(np.abs(mixed)) <= 1.0` before WAV write.
- [ ] **WAV header correctness:** Read back the written file with `wave.open()` and assert sample_rate, channels, sample_width match expected values.
- [ ] **Brown noise no DC drift:** Brown noise signal mean is < 0.01 after generation, before normalization — verify `abs(brown.mean()) < 0.01`.
- [ ] **Note onset is click-free:** Each individual note played in isolation has no click at onset — verify by listening and by checking `note_array[0]` ≈ 0.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Loop-point click discovered post-release | LOW | Add fade-out/in at boundaries; re-render; no API change needed |
| int16 overflow distortion in mixed output | LOW | Add `np.clip` before conversion; re-render |
| Brown noise DC drift in long files | MEDIUM | Replace `cumsum` with leaky integrator or FFT method; re-render; no API change needed |
| Music box sounds like pure sine (no partials) | MEDIUM | Add partial synthesis to tone generator; re-render; no API change needed |
| Karplus-Strong tuning inaccuracy | HIGH (if already shipped) | Replace synthesis approach with additive synthesis; this is an implementation swap, not a small fix |
| WAV header corruption | LOW | Switch to `scipy.io.wavfile.write`; add round-trip test |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Loop-point click at WAV boundary | WAV output / render pipeline | Play file on loop 20× without click; assert `abs(audio[-1]) < 1e-4` |
| int16 overflow from mixed layers | Mixing / layering phase | Unit test: mix both layers at max amplitude, assert no sample > 1.0 |
| Brown noise DC drift | Ambient noise generation phase | Assert `abs(brown_signal.mean()) < 0.01` before normalization |
| Pink noise low-frequency inaccuracy | Ambient noise generation phase | Compute PSD, assert slope is -10 dB/decade ± 2 dB over 20–2000 Hz |
| Music box tine timbre (pure sine) | Tone synthesis phase | Spectral analysis shows inharmonic partials; subjective listening test |
| Karplus-Strong tuning inaccuracy | Tone synthesis phase (design decision) | Choose synthesis method; validate tuning across C4–C6 before committing |
| Note onset click | Tone synthesis phase | Listen to single note in isolation; assert `note_array[0]` ≈ 0 |
| WAV header corruption | WAV output phase | Round-trip read-back test asserting header parameters match |

---

## Sources

- NumPy silent integer overflow issue: https://github.com/numpy/numpy/issues/10782
- sounddevice int32 crackling (overflow in practice): https://github.com/spatialaudio/python-sounddevice/issues/347
- Karplus-Strong tuning inaccuracy and allpass correction: https://en.wikipedia.org/wiki/Karplus%E2%80%93Strong_string_synthesis
- KVR Audio: Tuning a modified Karplus-Strong loop: https://www.kvraudio.com/forum/viewtopic.php?t=511662
- KVR Audio: How to compensate for LP detuning in Karplus-Strong: https://www.kvraudio.com/forum/viewtopic.php?t=539626
- Brown noise DC drift / leaky integrator solution: https://en.wikipedia.org/wiki/Brownian_noise
- Pink noise generation accuracy: https://github.com/felixpatzelt/colorednoise
- Pink noise FFT method: https://www.dsprelated.com/showarticle/908.php
- Seamless loop zero-crossing requirement: https://lmms.io/forum/viewtopic.php?t=25928
- Crossfade loop technique (2–4ms): https://creatorsoundspro.com/looping-audio-seamlessly-a-practical-guide-for-game-developers-video-editors/
- WAV format loop crossfade: https://www.soundonsound.com/techniques/making-seamless-sample-loops-your-hard-disk-recorder
- Additive synthesis and inharmonic partials for bell/tine sounds: https://en.wikipedia.org/wiki/Additive_synthesis
- Inharmonic overtones in bell/tine synthesis: https://northcoastsynthesis.com/news/maximizing-inharmonicity/
- JUCE forum: avoiding clicks/pops at loop points: https://forum.juce.com/t/avoid-clicks-and-pops-when-looping-over-a-part-of-a-sample/38124

---
*Pitfalls research for: Python audio synthesis / music box baby sleep sound generator*
*Researched: 2026-03-30*
