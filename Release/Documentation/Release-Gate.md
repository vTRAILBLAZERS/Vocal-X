# Vocal X Beta 0.1.0-beta.1 – Release-Gate

**NICHT FÜR EXTERNE TESTER FREIGEGEBEN.**

Erledigt: Phase-0-Bestandsaufnahme, Rückfallkopie, öffentliche Lizenzprüfung, getrenntes Admin-Signierwerkzeug, zehn registrierte Beta-Seriennummern, DPAPI-Schlüsselablage. Bestehende WAV-/Original-/Final-Regeln bleiben erhalten.

Noch erforderlich, in Reihenfolge:

1. Pfadtrennung und relativer Core-Modellreport implementiert und getestet. Noch offen: tatsächliche portable Runtime einschließlich AnyEnhance konsolidieren und auf fremdem Windows prüfen.
2. Lizenz-GUI und durchgängige Prüfung in Runner/Worker/CLI implementiert und getestet. First Run: Hardware → Lizenz → Output. Prüfung vor jedem Job, jeder Stufe und Veröffentlichung; laufende Stufe wird bei Ablauf zu Ende gerechnet.
3. GUI verwendet zentrale App-Version 0.1.0-beta.1 unabhängig von Engine-Resume-Version. EXE-/Installer-Metadaten noch offen.
4. Benutzerfreundliche Fehlermeldungen, Logs und Diagnoseexport mit maskierter Lizenz.
5. Verteilungsrechte für jeden Modellcheckpoint und sämtliche abhängigen Gewichte/Code prüfen. Unklarheit bleibt Blocker.
6. Reproduzierbare Runtime/Build-Dateiliste, Ausschluss Private/Tools/Backups/Benutzerdaten, SHA-256, Metadaten und Signaturvorbereitung.
7. Installer und Uninstaller, Update-Erhalt von Lizenz und Einstellungen.
8. Malwarebytes-Erkennung klären; Defender- und Malwarebytes-Test am tatsächlichen Release-Binary. Keine Ausnahmen oder deaktivierte Schutzsoftware.
9. Clean-Windows-Test und zweites physisches NVIDIA-System; Mindest-VRAM/RAM erst aus Messungen ableiten.

Kein Installer, kein signierter Release und kein Release-SHA-256 vorhanden. Lokale Unit-Tests sind keine Freigabe für externe Weitergabe.
