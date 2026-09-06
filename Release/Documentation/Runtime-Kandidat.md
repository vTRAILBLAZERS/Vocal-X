# Lokaler Laufzeitkandidat – 06.09.2026

Unter `Release/Staging/RuntimeCandidate-9e5b047509cd` liegt erstmals eine separate
Python-Laufzeitkopie. `latest-runtime-candidate.json` benennt den aktuellen Kandidaten.
Die bestehende App verwendet weiterhin ihre bisherige Umgebung.

Der Kandidat enthält Python 3.12.0, die vorhandenen Hauptbibliotheken und separat
die zusätzlichen AnyEnhance-Pakete. Er wurde aus dem lokalen Installationsbestand
kopiert, nicht aus einem frisch heruntergeladenen Wheel-Satz gebaut. Absolute
`.pth`-Verknüpfungen wurden weggelassen; `python312._pth` definiert relative Pfade.
Dieses Isolationsverhalten ist in der [Python-Dokumentation](https://docs.python.org/3.12/using/windows.html#finding-modules) beschrieben.

Der lokale Test bestand mit absichtlich ungültigem PYTHONHOME und PYTHONPATH sowie
auf Windows/System32 beschränktem PATH:

- Isolierter Python-Start, keine extern geladenen Python-Module.
- Qt-Fenster im Offscreen-Modus.
- WAV-FLOAT schreiben/lesen mit identischen Samples.
- CUDA-Matrixrechnung auf der RTX 5080.
- Imports von RoFormer und AnyEnhance-Abhängigkeiten einschließlich Wav2Vec2BertModel.

Das ist noch kein kompletter GUI- oder Modell-Audiotest. Windows-DLLs und der
installierte Grafiktreiber bleiben Voraussetzungen; der Test belegt keine
Unabhängigkeit von allen Systemkomponenten. Ein frischer Windows-PC wurde nicht getestet.

145 Paketinstallationen wurden inventarisiert; 255 Lizenz-/Hinweisdateien wurden
unverändert gesammelt. Deren Vorhandensein bedeutet keine abgeschlossene rechtliche
Prüfung. `runtime-manifest.json` enthält die Datei-Prüfsummen und Paketliste,
`verification.json` die erneute Prüfung und Pakete ohne gefundene Lizenzdatei.
Auch Python-Patchstand, nicht benötigte Entwicklungspakete, Bibliotheksbedingungen
und ein reproduzierbarer Build aus fixierten Originalpaketen bleiben zu bearbeiten.

Werkzeuge:

- `build_runtime_candidate.py`: neue Kopie in einem neuen Kandidatenordner erstellen.
- `Test-Runtime-Candidate.ps1`: isolierten Test mit Kopierblock ausführen.
- `verify_runtime_candidate.py`: alle erfassten Dateien erneut gegen SHA-256 prüfen.

Noch kein Installer, keine Modellauslieferung und keine externe Release-Freigabe.
