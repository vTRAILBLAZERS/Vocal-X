"""User interface translations. Preset definitions and model identifiers stay unchanged."""
LANG='de'
EN={
'Aktiv':'Enabled','Bei Fehler überspringen':'Skip on error','Modell':'Model','Auswählen':'Browse',
'Referenzstimme':'Reference voice','Referenzstimme auswählen':'Choose reference voice',
'Optional: trockene Aufnahme derselben Stimme':'Optional: dry recording of the same voice',
'AnyEnhance 360M · Sprache und Gesang\nSelf-Critic aktiv · rekonstruierte Mono-Stimme':'AnyEnhance 360M · Speech and singing\nSelf-Critic enabled · Reconstructed mono voice',
'AnyEnhance-v1 Baseline · für Sprache trainiert\nGesang experimentell · rekonstruierte Mono-Stimme':'AnyEnhance-v1 Baseline · Trained on speech\nSinging is experimental · Reconstructed mono voice',
'Generationsschritte':'Generation steps','Bearbeiteter Anteil':'Processed mix','Ab Frequenz (Hz)':'Frequency (Hz)',
'Schwelle (dB)':'Threshold (dB)','Max. Absenkung (dB)':'Max. reduction (dB)','Hochpass (Hz)':'High-pass (Hz)',
'Zusätzlich FLAC · 24-bit PCM':'Also export FLAC · 24-bit PCM','Hochpassfilter; keine Rauschunterdrückung.':'High-pass filter; no noise reduction.',
'KI-Restaurierung (experimentell)':'AI restoration (experimental)','Vocals isolieren':'Isolate vocals','Hall reduzieren':'Reduce reverb',
'Echo reduzieren':'Reduce echo','Zischlaute reduzieren':'Reduce sibilance','Tieffrequentes Rumpeln entfernen':'Remove low-frequency rumble',
'Wartet':'Pending','Läuft':'Running','Fertig':'Completed','Fertig mit Hinweisen':'Completed with warnings','Fehler':'Error','Unterbrochen':'Interrupted',
'Als eigenes Preset speichern':'Save as custom preset','Dateien hinzufügen':'Add files','Ausgewählte entfernen':'Remove selected',
'Job fortsetzen …':'Import job …','Jede Datei übernimmt das links gewählte Preset beim Hinzufügen.':'Each file uses the preset selected on the left when added.',
'Audiodatei':'Audio file','Warteschlange starten':'Start queue','Nach Song pausieren':'Pause after track','Aktuellen abbrechen':'Cancel current',
'Ausgewählten fortsetzen':'Resume selected','Ergebnisordner öffnen':'Open output folder','Bereit. Dateien hinzufügen und Warteschlange starten.':'Ready. Add files and start the queue.',
'VERARBEITUNGSLOG':'PROCESSING LOG','Kein gültiges Preset vorhanden.':'No valid preset available.',
'Eigenes Preset':'Custom preset','Name:':'Name:','Ungültiges Warteschlangenformat':'Invalid queue format','Ungültiger Eintrag':'Invalid entry',
'Audiodateien auswählen':'Choose audio files','Audio (*.wav *.flac *.aif *.aiff *.ogg *.mp3);;Alle Dateien (*)':'Audio (*.wav *.flac *.aif *.aiff *.ogg *.mp3);;All files (*)',
'Job-Zustand auswählen':'Choose job state','Bitte einen Job aus Processing/Jobs wählen.':'Please choose a job from Processing/Jobs.',
'Dieser Job steht bereits in der Warteschlange.':'This job is already in the queue.',
'Pausiert nach dem aktuellen Song.':'Will pause after the current track.','Warteschlange pausiert.':'Queue paused.',
'Warteschlange beendet. Ergebnisse und mögliche Fehler stehen in der Liste.':'Queue finished. Results and any errors are listed above.',
'Modelle und Eingabe werden geprüft …':'Checking models and input …','Verarbeitung wird abgebrochen …':'Cancelling processing …',
'%v / %m Stufen':'%v / %m stages','Vorbereitung / Abschluss':'Preparing / finishing',
'Verarbeitung läuft':'Processing in progress','Aktuelle Verarbeitung abbrechen und schließen? Fertige Stufen bleiben für Resume erhalten.':'Cancel processing and close? Completed stages will be kept for resume.',
'Die Desktop-App ist bereits geöffnet.':'The desktop app is already open.','Vocal X – Startfehler':'Vocal X – Startup error',
'Sprache':'Language','Entf: nur aus der Warteschlange entfernen. Audiodateien bleiben erhalten.':'Delete: remove from the queue only. Audio files are kept.',
'Öffnet den ausgewählten Track, sonst das letzte Ergebnis oder Output.':'Opens the selected track, otherwise the latest result or Output.',
'Ergebnisordner konnte nicht geöffnet werden:':'Could not open output folder:',
'Warteschlange konnte nicht geladen werden:':'Could not load queue:', 'Preset nicht geladen:':'Preset not loaded:',
'Verarbeitung beendet mit Exitcode':'Processing ended with exit code','Siehe Log.':'See log.',
'Natürlich':'Natural','Schonend':'Gentle','Trocken':'Dry','Zischlaute kontrollieren':'Control sibilance',
'AnyEnhance 360M - Isolierte Vocal':'AnyEnhance 360M - Isolated vocal','AnyEnhance 360M - Song zu Vocal':'AnyEnhance 360M - Song to vocal',
'KI-Restaurierung - Bereits isolierte Vocal':'AI restoration - Isolated vocal','KI-Restaurierung - Experimentell':'AI restoration - Experimental',
}
def tr(text):
 return EN.get(text,text) if LANG=='en' else text

def original(text):
 return next((de for de,en in EN.items() if en==text),text)

def set_language(language):
 global LANG
 LANG=language if language in ('de','en') else 'de'
