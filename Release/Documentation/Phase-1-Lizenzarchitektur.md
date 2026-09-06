# Phase 1 – Offline-Lizenzierung

Status: Protokoll und Admin-Tool implementiert. Noch keine GUI-Aktivierung und keine Produktionssperre in Worker/CLI integriert. Das ist die Grundlage für Phase 3, noch kein freigegebener Lizenzschutz.

## Trennung

- App/vocal_license.py: ausschließlich Anfrageformat, Gerätehash, Tokenprüfung und lokale Aktivierungsdatei. Kein privater Schlüssel und keine Liste gültiger Seriennummern.
- App/license-public-key.json: Ed25519 Public Key; darf mit ausgeliefert werden. Im endgültigen Paket muss die Vertrauenswurzel gegen versehentlichen Austausch im Build geprüft werden; lokales Patchen einer Offline-App ist grundsätzlich nicht ausgeschlossen.
- Tools/LicenseAdmin: ausschließlich Entwicklerwerkzeug, niemals in den Installer kopieren.
- Private/LicenseAdmin/signing-key.dpapi: PRIVATER SIGNIERSCHLÜSSEL, NICHT VERTEILEN. Mit Windows DPAPI an das aktuelle Windows-Konto geschützt. Eine bloße Kopie auf einen anderen Rechner ist kein verlässliches Schlüsselbackup. Vor Windows-Neuinstallation ist ein gesonderter, passwortgeschützter Offline-Export/Recovery-Prozess erforderlich; dieser ist noch nicht implementiert.
- Private/LicenseAdmin/serial-hashes.json: genau zehn SHA-256-Hashes der vorgegebenen Beta-Seriennummern.
- Private/LicenseAdmin/issuance.sqlite: wird bei erster Ausstellung angelegt; transaktionales Register, eine Gerätebindung je Seriennummer. Gemeinsam mit dem Schlüssel sichern, niemals verteilen.

Private und Backups sind in .gitignore ausgeschlossen. Das ist zusätzlich zur notwendigen expliziten Release-Dateiliste zu verstehen, nicht als alleinige Verpackungssicherheit. Noch kein Release-Paket wurde erstellt.

## Admin-Ablauf

Das Werkzeug wird mit der vorhandenen Entwickler-Python-Umgebung ausgeführt:

`python Tools/LicenseAdmin/license_admin.py issue --request-file Anfrage.txt --output Aktivierung.vxlicense`

Die Anfrage enthält Seriennummer, Produkt und gehashten Device Fingerprint. Das Werkzeug prüft die registrierte Seriennummer. Der Token wird ausschließlich in die Ausgabedatei geschrieben, nicht auf der Konsole ausgegeben. Dieselbe Anfrage liefert den bereits ausgestellten Token zurück. Ein zweites Gerät wird abgelehnt. Keine automatische Gerätefreigabe: ein alter Offline-Token kann nicht aus der Ferne widerrufen werden.

Standardablauf: Ende des 31.12.2026, definiert als exklusive UTC-Grenze 01.01.2027 00:00. Abweichende frühere Grenze über --expires im Format YYYY-MM-DDTHH:MM:SSZ möglich. Die Beta-Grenze steht zentral in vocal_license.BETA_EXPIRES. Typ Beta, maximal ein Gerät, erlaubte App-Versionsfamilie 0.1.x. Keine der zehn echten Seriennummern wurde durch Tests verbraucht.

## Gerätekennung und Grenzen

Gerätekennung v1 verwendet Windows MachineGuid, SystemManufacturer und SystemProductName. Nur ein SHA-256-Hash verlässt den Rechner. Kein Benutzername, Computername, MAC-Adresse oder USB-Gerät. Windows-Neuinstallation oder Änderung der verwendeten Systemmerkmale kann Neuausstellung erfordern. Fehlende Merkmale führen zu einer verständlichen Fehlermeldung statt einer instabilen Ersatzkennung.

Die Anfrage ist kein kryptografischer Hardwarebeweis. Ein administrativ manipuliertes oder geklontes Betriebssystem kann Merkmale nachbilden. Signaturen verhindern die unbemerkte Änderung des Tokens, aber kein beliebiges Patchen der lokalen Anwendung. Das Ablaufdatum nutzt die lokale UTC-Uhr; vollständiger Schutz gegen Uhr-Rollback erfordert eine vertrauenswürdige externe Zeitquelle. Diese Offline-Beta beansprucht keinen manipulationssicheren DRM-Schutz.

## Quellen der technischen Verfahren

Ed25519-Signatur und Verifikation: https://cryptography.io/en/41.0.7/hazmat/primitives/asymmetric/ed25519/
Windows DPAPI: https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata

## Nächster Entwicklungsblock

Installationsressourcen und beschreibbare Benutzerdaten zentral trennen. Anschließend Hardware → Lizenz → Output als First Run integrieren und Lizenzprüfung vor jeder Verarbeitung in GUI, Worker und CLI durchführen. Der vorhandene Entwicklungsbetrieb bleibt bis dahin unverändert; keine stillschweigende Lizenzumgehung in einem Release vorsehen.
