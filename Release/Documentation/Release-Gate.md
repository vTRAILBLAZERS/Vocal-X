# Vocal X Beta 0.1.0-beta.1 – Release-Gate

**NICHT FÜR EXTERNE TESTER FREIGEGEBEN.**

Erledigt: Phase-0-Bestandsaufnahme, Rückfallkopie, öffentliche Lizenzprüfung, getrenntes Admin-Signierwerkzeug, zehn registrierte Beta-Seriennummern, DPAPI-Schlüsselablage. Bestehende WAV-/Original-/Final-Regeln bleiben erhalten.

Noch erforderlich, in Reihenfolge:

1. Pfadtrennung und relativer Core-Modellreport implementiert und getestet. Lokaler Laufzeitkandidat erstellt; isolierter Qt-/WAV-/CUDA-/AnyEnhance-Importtest bestanden. Noch offen: vollständige App-/Modellintegration, reproduzierbarer Build und Prüfung auf fremdem Windows. Details: Runtime-Kandidat.md.
2. Lizenz-GUI und durchgängige Prüfung in Runner/Worker/CLI implementiert und getestet. First Run: Hardware → Lizenz → Output. Prüfung vor jedem Job, jeder Stufe und Veröffentlichung; laufende Stufe wird bei Ablauf zu Ende gerechnet.
3. GUI verwendet zentrale App-Version 0.1.0-beta.1 unabhängig von Engine-Resume-Version. EXE-/Installer-Metadaten noch offen.
4. Implementiert und getestet: nicht modaler Fehlerdialog, zentrale Logs und Diagnoseexport mit maskierter Lizenz und Tokenfilterung.
5. Verteilungsrechte für jeden Modellcheckpoint und sämtliche abhängigen Gewichte/Code prüfen. Unklarheit bleibt Blocker.
6. Reproduzierbare Runtime/Build-Dateiliste, Ausschluss Private/Tools/Backups/Benutzerdaten, SHA-256, Metadaten und Signaturvorbereitung.
7. Installer und Uninstaller, Update-Erhalt von Lizenz und Einstellungen.
8. Malwarebytes-Erkennung klären; Defender- und Malwarebytes-Test am tatsächlichen Release-Binary. Keine Ausnahmen oder deaktivierte Schutzsoftware.
9. Clean-Windows-Test: NICHT DURCHGEFÜHRT, laut Nutzer kein frischer PC verfügbar. Zweites physisches NVIDIA-System weiterhin offen; Mindest-VRAM/RAM erst aus Messungen ableiten. Lokale Tests ersetzen diese Nachweise nicht.

Kein Installer, kein signierter Release und kein Release-SHA-256 vorhanden. Lokale Unit-Tests sind keine Freigabe für externe Weitergabe.
