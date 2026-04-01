---
created: 2026-04-01T21:26:30.135Z
title: Build simple Gradio frontend UI interact with FastAPI
area: ui
files: []
---

## Problem

The library has no interactive interface — callers must write Python code to generate audio files. A demo/exploration UI would make it easier to test presets, tune volumes, and preview output without writing code.

## Solution

Build a simple Gradio frontend that talks to a FastAPI backend wrapper around `musicboxfactory`. The UI should expose the key parameters (soundfont path, melody preset or custom notes, ambient type, melody/ambient volumes, duration) and let the user generate and download a WAV file from the browser. FastAPI serves as the HTTP layer between Gradio and the library.

Out of scope for the core library (v1 is library-only); this is a separate demo/tooling layer.
