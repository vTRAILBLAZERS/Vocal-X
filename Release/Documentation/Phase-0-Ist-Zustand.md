# Phase 0 – Ist-Zustand (06.09.2026)

Vocal X ist eine funktionierende lokale PySide6-Desktopanwendung, noch kein portabler Release. Engine-Version 1.0.0; Ziel-App-Version 0.1.0-beta.1. App-Version und Resume-Engine-Version müssen getrennt werden, damit eine reine Versionsanzeige vorhandene Jobs nicht ungültig macht.

## Tatsächlicher Aufbau

- GUI: App/vocal_gui.py, qol_window.py, qol_audio.py, qol_windows.py; Übersetzungen gui_i18n.py und bilinguale Texte; Preset-Metadaten preset_info.py und Preset-JSONs.
- Launcher: selbst kompilierter C#-Wrapper Vocal X.exe; beide VBS-Dateien leiten darauf weiter. Malwarebytes-Anomalie ist ungeklärt. Kein Installer, kein unabhängiges Runtime-Paket, kein reproduzierbarer Release-Build vorhanden.
- Icon: assets/taskbar-x.ico aus dem vom Nutzer gelieferten grünen X; Verknüpfungen und Fenster verwenden dieses Icon. EXE-Ressource noch nicht aktualisiert.
- Engine: runner.py mit Modell-Hashprüfung, Stage-Chaining, Resume, Job-Lock, Logging. Modelle über models.py sowie restoration.py/restoration_full.py. DSP separat. Worker startet .venv/Scripts/python.exe.
- Programm-/Benutzerdaten noch vermischt: Config, Processing/Jobs, Cache, Preview im Projekt. Output auswählbar; Veröffentlichung schützt Original und führt eine aktuelle finale WAV, separate History und Formats.
- WAV-Prüfung in policy.py: tatsächlicher Container, Subtyp, Größe und Kanäle; GUI-Importwege und Runner verwenden sie.
- First Run: CUDA-Erkennung und Output-Auswahl vorhanden; keine Lizenzoberfläche bzw. Lizenzprüfung vorhanden.
- 12 Presets einschließlich Custom Template. Aktiv verwendete Core-Slugs: LEAP XE, Deux, Super Big Dereverb, Echo V2; weitere Core-Modelle im erweiterten Editor wählbar. AnyEnhance baseline und 360M in eigenen Presets.
- Modellordner: BS ca. 1,26 GiB; MEL ca. 4,35 GiB; AnyEnhance v1 ca. 0,95 GiB; AnyEnhance 360M ca. 3,80 GiB. Auswahl für Release erst nach Rechteprüfung.

## Runtime und Pfade

Python 3.12.0; .venv/pyvenv.cfg verweist auf die persönliche Installation unter C:/Users/marho/AppData/Local/Programs/Python/Python312. Einfaches Kopieren der venv reicht nicht. PyTorch/torchaudio 2.11.0+cu128, PySide6 6.11.2, NumPy 2.5.2, SciPy 1.18.1, soundfile 0.14.0. CUDA-Testsystem RTX 5080, Runtime 12.8, VRAM 15,89 GiB. Keine Aussage über Mindesthardware.

Core-Modellreport speichert absolute Checkpoint-/Config-Pfade. AnyEnhance ergänzt sys.path um .venv-anyenhance/Lib/site-packages und Tools-Unterordner. GUI-ROOT ist aus __file__ abgeleitet, erwartet aber beschreibbare Unterordner neben App. Aktive Modelladapter enthalten keine direkt hartcodierten D:-Literale; trotzdem bestehen strukturelle Entwicklerpfad-Abhängigkeiten. Backups, Reports, Sessions und Testdateien enthalten weitere absolute Pfade und dürfen nicht blind paketiert werden.

## Tests und Risiken

Sechs bestehende Testsuiten bestanden vor Release-Arbeiten. Sie ersetzen weder Clean-PC- noch Zweit-GPU-Test. Kein Nachweis eines unabhängigen Installers oder Malwarebytes-Freigabe. Modell-/Weight-Lizenzen müssen einzeln geprüft werden, insbesondere rekonstruierter AnyEnhance-Code und abhängige Gewichte. Noch kein extern freigegebener Build.

## Nächste Änderungen

Phase 1: Ed25519-Challenge/Response, getrenntes Admin-Tool, DPAPI-geschützter privater Schlüssel, zehn Seriennummern nur im Admin-Bereich, Gerätebindung und Ablaufprüfung, automatisierte Negativtests. Danach Phase 2: Installationspfad und Benutzerdaten trennen. Danach First-Run-Integration und durchgängige Lizenzsperre in GUI/Worker/CLI. Bis dahin ist das Lizenzmodul allein noch kein aktivierter Produktschutz.
