# VOCAL AI Pipeline Engine v1

Start: `.venv\Scripts\python.exe App\pipeline.py run --preset "Clean Acapella" --input "D:\Musik\Song.wav"`

Resume: denselben Befehl mit `--resume JOB-ID` aufrufen. Die ID steht im ausgegebenen Job-Pfad. JSON-Dateien können über einen vollständigen Pfad an `--preset` übergeben werden. Custom Template liegt unter Pipelines/Custom.

Jeder Job liegt unter Processing/Jobs mit state.json, job.log, Temp und Export. Zwischenstems bleiben für Resume erhalten. Jobs werden gegen parallele Ausführung gesperrt. Änderungen an Quelle, JSON, Engine-Version oder Modell-Dateien verweigern Resume; dann einen neuen Job starten. Beschädigte/fehlende Ergebnisse werden ab der betroffenen Stufe neu erzeugt. Optionale Fehler reichen die Eingabe durch und führen zum Status completed_with_warnings; Resume versucht sie erneut.

Stage-Felder: id, type, input (source, previous oder früherer output-Alias), output (eindeutiger Alias), enabled, optional, parameters, model (Slug oder null), engine (BS, MEL, DSP). Deaktivierte Stufen reichen ihre Eingabe durch. Export muss als letzte Stufe aktiv und erforderlich sein. Modellkatalog: vorhandener Config/core-model-download-report.json, alle 10 Slugs auswählbar. Keine automatischen Downloads.

Clean Acapella: Leap Xe, Dereverb, Deesser, Export. Dry Studio Vocal: alle sechs Stufen. Maximum Vocal: Deux, 30 Prozent Dereverb-Beimischung, Deesser, Export; der Name ist keine Qualitätsgarantie. Custom Template: Leap Xe, Deesser, Export; weitere Stufen vorbereitet.

Modellparameter: device (cuda/cpu), stem (vocals/dry), wet (0 bis 1, lineare Beimischung, keine Modellstärke). DSP-Deesser: frequency_hz, threshold_db, max_reduction_db; stereogekoppelte Hochband-Kompression. Cleanup: highpass_hz, ausschließlich Hochpass, kein KI-Denoiser. Export: flac boolean. WAV bleibt 32-bit Float; FLAC ist PCM 24-bit, bei Überpegel wird nur die FLAC-Kopie abgesenkt. Die ursprüngliche Samplerate und Mono/Stereo-Anordnung bleiben erhalten. Audio wird im Speicher verarbeitet; lange Dateien benötigen ausreichend RAM und Plattenplatz.

Tests: App/Test-Pipeline.ps1, optional -AudioFile und -Preset. Der Testblock endet auch bei Fehlern mit dem Kopierblock. Synthetische Tests prüfen Technik, nicht die Hörqualität auf Musik. Keine GUI.
