# AnyEnhance 360M im Projekt

Die grosse Originalversion ist als eigenes Modell eingebunden. GUI neu starten und eines dieser Presets waehlen:
- AnyEnhance 360M - Isolierte Vocal: fuer eine bereits isolierte Stimme.
- AnyEnhance 360M - Song zu Vocal: zuerst Vocal-Separation, danach Rekonstruktion.

Self-Critic ist aktiv. 20 Generationsschritte sind voreingestellt. Referenzstimme ist optional; am besten eine trockene, saubere Aufnahme derselben Stimme. Das Modell rekonstruiert Mono. Bei Stereoausgabe erhalten beide Kanaele dieselbe rekonstruierte Stimme; mit reduziertem Bearbeitungsanteil wird die Eingabe beigemischt. Keine Garantie auf vollstaendige Entfernung kreativer Effekte oder originalgetreue Rekonstruktion.

Alle Modelle liegen lokal unter Models/AnyEnhance-360M, inklusive DAC und W2V-BERT. W2V-BERT ist auch fuer Inferenz erforderlich: der Originalcode importiert es erst beim ersten Audioabschnitt. Die fruehere Recherche-Einschaetzung hierzu ist korrigiert.

Pruefung: App/Test-AnyEnhance360M.ps1 (schnell), mit -GPU auch neue echte Audiotests. Beide enden mit dem KOPIERBLOCK. Testaudio liegt in Temp/AnyEnhance360M-Test. Ausgabe wie gewohnt unter Output/<Trackname>/Finale Vocal und den Schrittordnern. Die Testreferenz ist fuer den technischen Funktionstest, nicht als Empfehlung fuer beste Klangqualitaet gedacht.

CLI: .venv/Scripts/python.exe App/pipeline.py run --preset "AnyEnhance 360M - Isolierte Vocal" --input "D:/Pfad/Vocal.wav"

Codequelle: https://github.com/open-mmlab/Amphion/pull/386
Gewichte: https://modelscope.cn/models/amphion/anyenhance
Hilfsmodell: https://huggingface.co/facebook/w2v-bert-2.0
Code-Lizenz MIT; ModelScope-Karte nennt CC-BY-NC-4.0 fuer Gewichte.
