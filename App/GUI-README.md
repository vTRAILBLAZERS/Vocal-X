# VOCAL AI Desktop v1

Start per Doppelklick auf `App/Start-Vocal-AI.vbs`. Alternativ `.venv/Scripts/pythonw.exe App/vocal_gui.py` verwenden. Die Oberfläche nutzt die bereits installierte PySide6-Bibliothek.

1. Links ein Preset wählen und bei Bedarf Modelle, aktive Stufen und Regler einstellen.
2. Mehrere Audiodateien hinzufügen. Jede Datei erhält eine eigene Kopie der aktuellen Pipeline; spätere Änderungen links betreffen nur neu hinzugefügte Dateien.
3. Warteschlange starten. Die Songs laufen nacheinander in einem eigenen Arbeitsprozess. Der Fortschritt zeigt abgeschlossene Stufen, keine geschätzte Restzeit.
4. Fertigen Song auswählen und den Ergebnisordner öffnen. WAV ist 32-bit Float; die optionale FLAC-Kopie verwendet 24-bit PCM.

„Nach Song pausieren“ lässt den aktuellen Song fertig werden. „Aktuellen abbrechen“ beendet seinen Arbeitsprozess und pausiert die Warteschlange. Bereits fertige Stufen bleiben bestehen. Zum Wiederaufnehmen den unterbrochenen/fehlgeschlagenen Eintrag auswählen, „Ausgewählten fortsetzen“ und danach „Warteschlange starten“ drücken. Die Engine prüft Dateien und Einstellungen erneut. Abbruch während der ersten Vorprüfung kann erfolgen, bevor ein Job angelegt wurde; dann startet die Verarbeitung neu.

Die Warteschlange wird unter `Config/gui-queue.json` gespeichert und nach Neustart wiederhergestellt. Sie startet nicht automatisch. Frühere CLI-Jobs lassen sich über „Job fortsetzen …“ durch Auswahl ihrer `state.json` aus `Processing/Jobs` aufnehmen. Fehlgeschlagene Songs werden markiert; die Warteschlange fährt mit dem nächsten Song fort.

„Als eigenes Preset speichern“ legt eine neue JSON-Datei unter `Pipelines/Custom` an. Existierende Presets werden nicht überschrieben. Mit „Ausgewählte entfernen“ werden nur Einträge aus der Warteschlange entfernt; Audio- und Jobdateien bleiben auf der Platte.

Vollständige Arbeitsprozess-Logs: `Config/GUIRequests/*.log`; Stage-Logs und Zwischenstems: `Processing/Jobs/<Job-ID>`. Pro Projekt kann eine Desktop-Instanz laufen. CLI-Jobs sollten nicht gleichzeitig auf derselben GPU laufen.

Modell- und DSP-Regler sind verfügbar. Die Reihenfolge und benutzerdefinierte Verzweigungen werden aus dem JSON übernommen; ein grafischer Editor für neue Stage-Typen, Drag-and-drop-Reihenfolge und Audiovorschau sind in dieser Version nicht enthalten.
