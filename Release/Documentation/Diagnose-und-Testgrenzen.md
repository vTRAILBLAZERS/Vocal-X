# Diagnosefunktionen und verbleibende Testgrenzen

Hilfe → Diagnosebericht erstellen speichert einen Textbericht zur ausgewählten Datei oder zum letzten abgeschlossenen GUI-Job. Er enthält Version, Windows, GPU/CUDA/VRAM, Modell-Dateiprüfung, Preset-Stufen, WAV-Prüfung und letzten Fehler. Die Modellprüfung prüft Vorhandensein; sie ist keine vollständige Gewichts-/Hashprüfung. Es wird nichts automatisch versendet.

Lizenznummern sind maskiert, Anfrage- und Aktivierungstokens sowie PEM-Privatschlüssel werden herausgefiltert. Audioinhalte und beliebige Konfigurationsdateien werden nicht aufgenommen. Benutzerprofilpfade werden ersetzt. Installations-, Outputpfade und technische Fehler können weiterhin Angaben enthalten, die vor dem Weitergeben geprüft werden sollten.

Logs liegen unter Logs im Benutzerdatenordner, im installierten Layout unter %LOCALAPPDATA%/Vocal X/Logs. Täglich wird VocalX_YYYY-MM-DD.log angelegt. Die strukturierten Einträge enthalten UTC-Zeit, App-/Windows-Version, GPU-Diagnose, Stage/Modell, Dauer und Fehler. Bestehende technische Joblogs bleiben zur Fehlersuche erhalten und werden nicht automatisch in Diagnoseberichte kopiert.

Der neue Fehlerdialog ist nicht modal. Die Queue kann weiterlaufen; Details werden erst auf Wunsch eingeblendet. Erneut versuchen reiht denselben Track für Resume ein. Ein vorhandener Diagnose-Zieldateiname wird nicht überschrieben; bitte einen neuen Namen wählen.

## Clean-PC-Test

Der Nutzer kann keinen frischen Windows-PC testen. Status: NICHT DURCHGEFÜHRT / DERZEIT NICHT VERFÜGBAR. Ein erfolgreicher Test wird nicht behauptet, die bisherige Freigabebedingung bleibt unerfüllt.

Lokale Tests mit getrennten Programm-/Datenordnern sind vorhanden. Ein neuer Windows-Benutzer, eine VM oder ein zweiter NVIDIA-Rechner wurden im Rahmen dieses Diagnose-Updates nicht getestet. Solche Prüfungen könnten zusätzliche Fehler aufdecken; sie sind kein automatisch gleichwertiger Ersatz für alle bisher geforderten Tests.

Die externe Beta bleibt vorerst nicht freigegeben. Zusätzlich offen bleiben Runtime/Installer, Modellrechte, Antivirus-Klärung und das zweite NVIDIA-System. Eine spätere Verteilung mit verbleibenden Testlücken müsste ausdrücklich als solche entschieden und dokumentiert werden.
