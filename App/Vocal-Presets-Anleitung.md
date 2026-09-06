# Vocal-Presets

Alle vier Presets verwenden zunächst Leap Xe zur Trennung und exportieren WAV 32-bit Float. Das Modell kann in der GUI geändert werden. Echo und Cleanup bleiben ausgeschaltet, solange kein konkreter Bedarf besteht.

| Preset | Nachbearbeitung |
| --- | --- |
| Natürlich | Keine. Referenz zum Vergleich. |
| Schonend | 25 % bearbeitetes De-Reverb-Signal, 75 % reine Trennung. Kein De-Esser. |
| Trocken | 60 % bearbeitetes De-Reverb-Signal, 40 % reine Trennung. Kein De-Esser. |
| Zischlaute kontrollieren | Keine Hallreduktion. De-Esser ab 6.500 Hz, Schwelle −24 dB, maximal 3 dB Absenkung. |

Die Prozentwerte sind Mischanteile, keine gemessene Hallmenge. Die Einstellungen sind Ausgangspunkte, keine automatisch auf jede Stimme abgestimmten Werte. Trocken ist relativ zu den anderen Presets gemeint und garantiert keine vollständig trockene Vocal.

Installation: Die vier JSON-Dateien in D:\VOCAL AI 2026\Pipelines\Presets kopieren und die GUI neu starten. Alternativ übernimmt das beiliegende Install-Presets.ps1 die Installation mit Sicherung, Strukturprüfung und Kopierblock. Es kopiert auch die bereits vorbereitete schonendere Vocal, sofern sie im übergeordneten Ordner des Installers liegt.

Bestehende Warteschlangeneinträge behalten ihre bisherigen Einstellungen. Für einen neuen Vergleich ein neues Preset wählen und den Song erneut hinzufügen.

Zum Beurteilen zunächst Natürlich und Schonend bei ähnlicher Lautstärke vergleichen. Trocken nur verwenden, wenn mehr Hallreduktion nötig ist. Zischlaute kontrollieren gezielt für störende S-/Sch-Laute verwenden. Es ist noch keine automatische KI-Empfehlung integriert.
