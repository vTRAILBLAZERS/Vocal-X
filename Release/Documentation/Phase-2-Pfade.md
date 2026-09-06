# Phase 2 – Programm- und Benutzerdaten

Die zentrale Auflösung liegt in App/vocal_pipeline/paths.py. Der Parameter root bezeichnet weiterhin den Installations-/Ressourcenordner. data_root(root) liefert den getrennten beschreibbaren Bereich. Dadurch bleiben Modelladapter und Engine-Aufrufe kompatibel.

## Layout

Installation: App, Models, Config/core-model-download-report.json, Pipelines/Presets, Tools/AnyEnhance-Code, später Runtime.

Benutzerdaten: Config (Einstellungen/Queue/Worker-Anfragen), Processing/Jobs, Cache, Temp, Preview, Logs, Session, License, Pipelines/Custom. Fertige Ausgaben verwenden weiterhin den frei gewählten Output-Ordner.

Im Release wird Release/runtime-layout.json nach App/runtime-layout.json kopiert. Modus installed nutzt %LOCALAPPDATA%/Vocal X und verlangt die gebündelte Runtime unter Runtime/python.exe. Es gibt in diesem Modus keinen stillen Rückfall auf eine persönliche Python-Installation. AnyEnhance-Zusatzpakete werden unter Runtime/anyenhance erwartet; das tatsächliche Runtime-Paket folgt in der Packaging-Phase.

Ohne Marker bleibt ein Entwicklungs-Checkout im bisherigen Projektmodus. Der aktuelle Entwicklerbestand wurde nicht verschoben: vorhandene Einstellungen, Queue, Outputs und rund 6 GiB Jobs bleiben erreichbar. Ein Release-Build muss den installed-Marker verbindlich setzen und prüfen; das Fehlen des Markers darf nicht als fertiger Release durchgehen.

Für Tests und alternative Datenorte unterstützen CLI und Worker --data-root (absoluter Pfad). Intern wird VOCAL_X_DATA_ROOT weitergegeben. Im Installationsmodus werden Datenpfade innerhalb des Programmordners abgelehnt. GUI-Worker erhalten ihren Datenpfad ausdrücklich, damit Jobzustand und GUI denselben Ordner verwenden.

## Modelle und Presets

Der Core-Modellreport enthält nun relative Models/...-Pfade. Alte absolute Reportpfade werden am Models-Verzeichnis rebasiert; Pfade außerhalb des Modellordners werden abgelehnt. Mitgelieferte Presets werden aus dem Programmordner gelesen; neue/importierte eigene Presets landen im Benutzerdatenordner. Externe Audio- und Output-Pfade bleiben absichtlich absolute Benutzerpfade.

## Prüfung und Grenzen

Automatisierte Tests verwenden andere Installations- und Benutzerdatenordner mit Leerzeichen. Geprüft werden GUI-Sitzungsspeicherung, CLI, Worker, Export, Resume, unveränderte Programmdateien, Originalschutz, ein Final-Ergebnis, Modellpfade, Preset-Zuordnung und fehlende Runtime. Der Portabilitätstest verwendet DSP-Export ohne GPU; er beweist keinen vollständigen Modelllauf auf einem fremden Rechner.

Der Entwicklungs-PC bleibt weiterhin von seiner vorhandenen Python-Installation abhängig. Die neue Pfadarchitektur ist die Voraussetzung für das spätere portable Runtime-Paket, kein Ersatz für dieses Paket und keinen Clean-PC-Test.

Backup vor Änderung: Backups/PrePaths-20260906-142419.
