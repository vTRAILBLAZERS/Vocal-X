# Vocal X – Bedienung des QOL-Updates

Start: `D:\VOCAL AI 2026\Vocal X.exe` oder die Verknüpfung **Vocal X** auf dem Desktop. Eine noch geöffnete alte GUI vorher schließen. Beim ersten Start werden CUDA/GPU geprüft und der gewünschte Ergebnisordner abgefragt. Dieser lässt sich im Menü Vocal X → Einstellungen ändern.

## Normaler Ablauf

1. Preset wählen. Der kurze Text in der Auswahl und die Infobox erklären die tatsächlich aktivierten Schritte. Die Presets sind allgemein verwendbar und nicht auf einen Testtrack abgestimmt.
2. WAV-Dateien hinzufügen (Strg+O), ins Fenster oder auf die EXE ziehen. Andere Formate und unlesbare WAV-Dateien werden abgelehnt; eine Umbenennung von MP3 in WAV genügt nicht.
3. Optional einen Track auswählen, in der Wellenform einen Bereich markieren und „Vorschau rendern“ wählen. Maximal 60 Sekunden; Vorschauen landen nicht im Final-Ordner.
4. Mit „Start / Fortsetzen“ oder Strg+Enter die Warteschlange verarbeiten.
5. „Ergebnisordner öffnen“ führt zum Ergebnis des ausgewählten Tracks, ansonsten zum verfügbaren Ergebnis- bzw. Standardordner.

## Ergebnisse

Unter dem gewählten Output-Ordner liegt pro Track ein Ordner. **Finale Vocal** enthält genau eine aktuelle WAV: standardmäßig `Trackname_VocalX.wav`. Ein neuer erfolgreicher Durchlauf ersetzt sie; frühere Ausgaben werden unter History aufbewahrt. Zwischenstufen haben eigene Ordner, optionales FLAC liegt unter Formats. Originaldateien bleiben unverändert. Ist eine alte Ausgabe in einem anderen Programm gesperrt, diese schließen und den Job fortsetzen.

## Warteschlange und Player

- Strg-/Umschalt-Klick und Strg+A: Mehrfachauswahl. Entf entfernt nur Queue-Einträge; „Entfernen rückgängig“ stellt sie wieder her.
- Drag-and-drop sortiert die Queue. Das Kontextmenü bietet Priorisieren, Preset anwenden, Wiederholen, Fortsetzen, Dateiinformationen und Fehlerdetails.
- Die Suche filtert nach Dateinamen. Queue speichern/laden verwendet `.vxqueue`.
- Original/Vocal X und A/B schalten die Wiedergabe um. Leertaste in der Trackliste startet/pausiert, Loop wiederholt den gewählten Bereich. RMS-Abgleich wirkt ausschließlich auf Wiedergabekopien.
- „Nach Schritt pausieren“ beendet den aktuellen Schritt sicher. Beim Abbrechen stehen sofortiger Abbruch und Fertigstellen des aktuellen Tracks zur Auswahl. Fortsetzen verwendet geprüfte Zwischenergebnisse.
- Sitzungszustand wird regelmäßig gespeichert. Nach unerwartetem Ende wird eine Wiederherstellung angeboten.

## Presets und Einstellungen

Stern markiert Favoriten; zuletzt verwendete Presets sind im Menü erreichbar. „Erweitert“ zeigt die vorhandenen Modell- und Effektparameter sowie Logs. Eigene Presets können mit deutschen und englischen Beschreibungen gespeichert, dupliziert und als `.vxpreset` importiert/exportiert werden. Sprache, Design, Output, Dateinamensschema, Benachrichtigungen, Fensterposition und weitere Einstellungen werden gespeichert. Einstellungen können separat exportiert/importiert werden.

## Praktische Grenzen

- „Aktive Stelle“ findet einen energiereichen Abschnitt; es ist keine KI-Gesangserkennung.
- Der Hörvergleich nutzt RMS, keine LUFS-Messung. Bei einem vollständigen Mix und einer isolierten Stimme bleibt der Vergleich inhaltlich unterschiedlich.
- Fortschritt und Restzeit sind Schätzungen aus verfügbaren Modellmeldungen und abgeschlossenen Tracks. Nicht jede Engine liefert kontinuierliche Prozentwerte.
- Eco/Maximum verändern bei KI-Restaurierung die Generationsschritte (8/32); Balanced erhält den Preset-Wert. Separation wird dadurch nicht automatisch beschleunigt. Precision und Chunk-Größen werden nicht pauschal verändert.
- Windows-Benachrichtigung und Taskleistenanzeige hängen von den Windows-Einstellungen ab. Standby/Herunterfahren verlangen eine ausdrückliche Auswahl und Bestätigung; Standard ist „Nichts tun“.
- Die EXE startet die bestehende lokale Python-Umgebung. Diese muss im Projekt bleiben; dies ist noch kein unabhängig installierbares Komplettpaket.

## Prüfen

`App\Test-QOL.ps1` prüft Engine, Ausgabe-Schutz, GUI, Player und Branding. Am Ende erscheint immer der KOPIERBLOCK FÜR CHATGPT. Der bereits ausgeführte echte CUDA-Vorschaulauf ist in `Temp\QOL-Work\gpu-preview-report.json` dokumentiert; der normale Testblock startet keinen neuen langen Modelllauf.
