# Phase 3 – Aktivierung und Verarbeitungssperre

Implementiert: Lizenzdialog (Deutsch/Englisch), Lizenzmenü und Einstellungszugang, First-Run-Reihenfolge GPU → Aktivierung → Output, maskierter Status und Gültigkeitsdatum. Die GUI zeigt zentral Vocal X BETA v0.1.0-beta.1; Engine-Version bleibt für bestehende Resume-Identitäten unverändert.

## Aktivieren

1. GUI neu starten. Bei kompatibler GPU erscheint die Aktivierung, sofern noch keine gültige Lizenz vorhanden ist. Sie ist jederzeit über Vocal X → Lizenz / Aktivierung bzw. die Einstellungen erreichbar.
2. Eine zugeteilte Beta-Seriennummer eingeben und „Anfragecode erzeugen“ wählen.
3. Den Code mit „Anfrage kopieren“ kopieren und dem Herausgeber übermitteln. Das Programm versendet selbst keine Daten.
4. Der Herausgeber speichert ihn als Textdatei und erzeugt mit Tools/LicenseAdmin/license_admin.py einen signierten Token (siehe Phase-1-Lizenzarchitektur).
5. Token einfügen oder die .vxlicense-Datei importieren, dann „Aktivieren“. Nach erfolgreicher Speicherung werden die Eingabefelder geleert. Angezeigt werden nur maskierte Seriennummer, Gerät „Dieser PC“ und Ablaufdatum.
6. Dialog schließen und gegebenenfalls Output-Ordner auswählen.

Die lokale Speicherung liegt unter License/activation.vxlicense im jeweiligen Benutzerdatenbereich, im Installationsmodus unter %LOCALAPPDATA%/Vocal X. Ein ungültiger neuer Token ersetzt keine bestehende gültige Aktivierung.

## Durchsetzung

license_service.py ist der gemeinsame Zugang zum öffentlichen Schlüssel und gespeicherten Token. Der Runner prüft vor jeder Verarbeitung, vor jeder Stufe und vor der Veröffentlichung. Damit sind auch direkter CLI-Aufruf und GUI-Worker abgesichert. Es gibt keinen Entwicklungsmodus ohne Lizenzprüfung. GUI-Buttons und Vorschau werden ebenfalls gesperrt; Lizenz und Diagnose bleiben erreichbar.

Ein bereits laufendes Modell wird bei Lizenzablauf nicht hart mitten im GPU-Aufruf beendet. Vor der nächsten Stufe bzw. finalen Veröffentlichung greift die erneute Prüfung. Vorhandene Zwischenstufen bleiben erhalten. CLI meldet Lizenzfehler mit Exitcode 2; Worker meldet einen strukturierten verständlichen Lizenzfehler ohne Stacktrace. Lizenzdaten werden nicht in die Job-Identität kopiert.

Die Prüfung vertraut wie dokumentiert auf die lokale Uhr und lokale Windows-Gerätemerkmale. Das ist kein Schutz gegen beliebige lokale Programmmanipulation. Die öffentliche Schlüsseldatei gehört zur unveränderlichen Release-Dateiliste; ein späterer Build muss ihre Integrität berücksichtigen.

## Entwicklungs-PC

Keine der zehn echten Beta-Seriennummern wurde automatisch gebunden. Deshalb benötigt auch der aktuelle Entwicklungsbetrieb vor dem nächsten Rendering eine normale Aktivierung. Die Tests erzeugen ausschließlich eigene Schlüssel und Testlizenzen in temporären Verzeichnissen; diese Testhelfer dürfen nicht in den Release.

## Prüfung

- Gültige Aktivierung, Speicherung und erneutes Öffnen; maskierte Anzeige und geleerte Eingabefelder.
- Fehlerhafter Token überschreibt keine bestehende Aktivierung.
- Ohne Lizenz kein GUI-Rendering und keine Output-Ersteinrichtung.
- Fehlende/beschädigte/abgelaufene/manipulierte/fremde Lizenz: reale CLI- und Worker-Unterprozesse brechen mit Exitcode 2 ab, ohne Ergebnisdateien.
- Ablauf vor Veröffentlichung verhindert Final-Output.
- Bestehende Portabilitäts-, Audio-, Engine- und GUI-Tests verwenden signierte temporäre Testlizenzen.

Ein Clean-PC-Test und ein zweiter physischer NVIDIA-PC bleiben Release-Gates.
