# Vocal X

**Vocal X** is a Windows desktop application for AI-assisted vocal separation, restoration and processing.

Current development version: **Vocal X Beta v0.1.0-beta.1**

> Vocal X is currently in private beta development and is not yet prepared for public distribution.

## Repository contents

This repository contains the application source code, GUI, preset definitions, processing logic, tests, release documentation and developer tools.

The following are intentionally excluded:

- AI model weights
- Python virtual environments
- Private signing keys
- Activation databases and private license material
- User audio
- Processing jobs
- Cache and logs
- Output and preview files
- Temporary files
- Compiled EXE and installer builds

## Branches

### develop

Default branch for active development.

### main

Stable and release-oriented branch.

Direct pushes to main should not be used.

### Feature branches

New work should normally start from develop.

Examples:

- feature/waveform-preview
- feature/preset-manager
- feature/installer
- fix/output-folder
- fix/license-dialog

Recommended workflow:

feature/* -> Pull Request -> develop -> testing -> Pull Request -> main

## Developer setup

After cloning the repository:

1. Switch to the develop branch.
2. Run the developer setup script once it is available.
3. Configure the required local Python/CUDA environment.
4. Install or provide the approved Vocal X model set locally.

## Git protection

The repository contains .githooks/pre-push.

It prevents accidental direct pushes to main when the repository hook configuration is enabled.

## Development platform

Current development target:

- Windows 11 64-bit
- Git for Windows
- PowerShell
- Python
- NVIDIA GPU with CUDA support for AI processing

Exact minimum GPU, VRAM, RAM and storage requirements are still being benchmarked.

## AI models

Model weights are intentionally not stored in Git.

Common excluded formats include:

- .ckpt
- .pth
- .pt
- .safetensors
- .onnx

Redistribution rights and licenses must be verified before any model is distributed with Vocal X.

## Licensing security

The application may contain public verification material required to validate signed Vocal X licenses.

Private signing material must never be committed.

The complete Private/ directory is excluded from Git.

Examples of private files that must remain local:

- signing-key.dpapi
- serial-hashes.json

## Audio

Do not commit source songs, vocals, previews or processed user audio.

Vocal X application input is being standardized around valid WAV files.

## Release flow

feature -> develop -> tests -> release validation -> main -> packaged beta

Current beta target: **0.1.0-beta.1**

## Security

Never commit credentials, private keys, activation tokens, real tester license data or private user content.

If a secret is ever committed, deleting it in a later commit is not sufficient. It must be treated as compromised.

## Repository owner

GitHub: **vTRAILBLAZERS**
