# Paketvorbereitung – 06.09.2026

Der Projektinhaber bestätigt: Vocal X bleibt dauerhaft nicht kommerziell.
NC-Modelle sind deshalb grundsätzlich Kandidaten. Ihre Attribution, konkreten
Dateirechte und gegebenenfalls Share-Alike-Bedingungen müssen trotzdem erhalten
bleiben. Die App-Aktivierung darf Rechte an Drittmaterial nicht pauschal einschränken.

`Release/package_plan.py` erzeugt einen Prüfplan, keinen Installer. Er liest die
aktuellen eingebauten Presets und verwendet eine ausdrückliche Liste von App-Dateien.
Private Schlüssel, Lizenzverwaltung, Testschlüssel, Benutzerdaten, Backups und die
von Malwarebytes beanstandete EXE gelangen nicht in diese Liste. Jede geplante Datei
erhält Größe und SHA-256. Die installierte Pfadkonfiguration wird als
`App/runtime-layout.json` eingeplant. Ungeklärte Presets werden zurückgehalten.
Gewichte werden überhaupt noch nicht kopiert; dafür ist ein eigener geprüfter
Datei- und Lizenzumfang erforderlich.

Nächste notwendige Arbeiten:

1. Exakte Modellgewichte und YAML-Dateien ihren Original-Lizenzangaben zuordnen,
   Lizenztexte und Urheberhinweise lokal für das Paket sichern. Deux und Sucial
   kommen unter ihren NC-Bedingungen infrage; nicht geklärte Modelle bleiben offen.
2. Eine eigenständige Python-Laufzeit samt Bibliotheken und Lizenzhinweisen bauen.
   Die bestehende Entwicklungsumgebung verweist auf die persönliche Python-Installation
   und ist kein portables Paket. AnyEnhance braucht zusätzlich Code und Abhängigkeiten.
3. Einen überprüfbaren Launcher und Installer erstellen. Die beanstandete EXE wird
   nicht wiederhergestellt; Virenschutz-Ausnahmen sind kein Bestandteil des Plans.
4. Paketstart, Aktivierung, Audioverarbeitung, erneutes Rendern, Fehlerbehandlung,
   Ausgabe und Deinstallation am tatsächlich erzeugten Paket prüfen.

Ein frischer Windows-PC steht laut Nutzer nicht zur Verfügung. Dieser Test bleibt
ausdrücklich nicht durchgeführt. Lokale Prüfungen ersetzen ihn nicht.

Prüfung: `Release/Test-Package-Plan.ps1`. Ein Exitcode 0 bestätigt einen erfolgreich
erzeugten Prüfplan, keine Release-Freigabe. Die Gründe stehen in `package-plan.json`.
