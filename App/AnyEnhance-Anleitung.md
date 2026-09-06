# KI-Restaurierung (experimentell)

Die neue Stage `restoration` nutzt **AnyEnhance-v1 CCF-AATC Baseline** mit 45,68 Millionen trainierbaren Parametern. Diese kleinere Veröffentlichung wurde für Sprachrestaurierung trainiert. Sie ist **nicht** die große AnyEnhance-Gesangsversion aus dem ursprünglichen Paper. Deren Gewichte waren auffindbar, die verlinkte vollständige Implementierung jedoch nicht. Die Anwendung auf Gesang ist deshalb experimentell.

## Bedienung

- **KI-Restaurierung - Experimentell**: Erst Leap Xe zur Vocal-Trennung, dann Restaurierung, dann Export. Keine zusätzliche Hallreduktion und kein De-Esser.
- **KI-Restaurierung - Bereits isolierte Vocal**: Restauriert eine bereits isolierte Vocal direkt. Keinen kompletten Musikmix als Eingang wählen.
- In bestehenden Presets ist die zusätzliche Stufe zunächst ausgeschaltet. Sie lässt sich in der GUI aktivieren.
- **Bearbeiteter Anteil**: 1,0 gibt ausschließlich die Rekonstruktion aus; kleinere Werte mischen Originalanteile samt verbliebenen Effekten hinzu. Dies ist kein Distortion-Stärkeregler. Beim Mischen sind Phaseneffekte möglich.
- **Generationsschritte**: 4 bis 40, Standard 20. Mehr Schritte benötigen mehr Rechenzeit und garantieren keine bessere Stimme.

Die Baseline gibt eine rekonstruierte Mono-Stimme aus. Bei Stereo-Eingaben werden beide Ausgabekanäle mit dieser Rekonstruktion befüllt; bei Beimischung bleibt ein Teil des ursprünglichen Stereobildes. Samplerate und Länge bleiben erhalten. Sie kann Stimmfarbe, Konsonanten, Atemgeräusche und Gesangsdetails verändern. Vollständig trockene, identische Original-Vocals sind nicht garantiert.

Zunächst kurze Ausschnitte mit „Natürlich“ vergleichen. Zur Vorschau wurden sechs Sekunden aus dem vorhandenen Track geprüft. Die technische Prüfung ist kein Hörqualitätstest.

## Dateien und Resume

Ergebnisse erscheinen wie bisher unter `Output/<Trackname>`, mit eigenem nummeriertem Restaurierungsordner und `Finale Vocal`. Job-Dateien bleiben unter `Processing/Jobs`. Resume prüft auch die Restaurierungsgewichte und den Adapter-Code. Bei geänderten Modellen oder Pipeline-Einstellungen einen neuen Job starten.

Zusatzbibliotheken liegen in `.venv-anyenhance` und werden nur beim Laden dieser Stage eingebunden. Vorhandenes PyTorch/CUDA wird aus `.venv` genutzt. Die ursprüngliche Umgebung wurde nicht aktualisiert. In der Zusatzumgebung kann `pip check` einen Konflikt zwischen dem für Audiotools benötigten älteren Protobuf und dem mit sichtbaren ONNX-Paket melden; der Restaurierungspfad verwendet ONNX nicht.

Code: `Tools/AnyEnhance-v1`; Gewichte und SHA-256-Nachweise: `Models/AnyEnhance-v1/provenance.json`. Keine automatischen Downloads beim Verarbeiten von Audio. Modellgewichte werden vor dem Laden auf ihre dokumentierten Prüfsummen geprüft.

Offizielle Baseline: https://github.com/viewfinder-annn/AnyEnhance-v1

Testbefehl: `.venv\Scripts\python.exe App\pipeline.py run --preset "KI-Restaurierung - Bereits isolierte Vocal" --input "D:\Pfad\Vocal.wav"`

PowerShell-Prüfung: `App/Test-Restoration.ps1`. Sie endet immer mit dem Kopierblock. Die GUI nach der Installation neu starten und neue Warteschlangeneinträge hinzufügen.
