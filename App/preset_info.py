"""Descriptions derived from enabled stages; bilingual data persists in preset JSON."""
LABELS={'vocal_separation':('Stimme vom Instrumental trennen','Separate vocals from the instrumental'),'dereverb':('Hall reduzieren','Reduce reverb'),'deecho':('Echo reduzieren','Reduce echo'),'deesser':('Zischlaute reduzieren','Reduce sibilance'),'cleanup':('Tiefes Rumpeln filtern','Filter low rumble'),'restoration':('Stimme mit KI rekonstruieren','Reconstruct the voice with AI'),'export':('Als WAV exportieren','Export WAV')}
def describe(p):
 stages=[s for s in p['stages'] if s['enabled']];types={s['type'] for s in stages};models=sum(s['engine']!='DSP' for s in stages)
 result={}
 for lang,n in [('de',0),('en',1)]:
  reconstruction='restoration' in types;separation='vocal_separation' in types
  short=('KI-Rekonstruktion für eine trockenere Stimme.' if reconstruction else 'Vocal-Trennung mit nachgeschalteter Bearbeitung.' if len(types)>2 else 'Natürliche Vocal-Trennung ohne zusätzliche Reinigung.' if separation else 'Bearbeitung einer bereits isolierten Vocal.') if lang=='de' else ('AI reconstruction for a drier voice.' if reconstruction else 'Vocal separation with additional processing.' if len(types)>2 else 'Natural vocal separation without extra cleanup.' if separation else 'Process an already isolated vocal.')
  details=[]
  for s in stages:
   line=LABELS[s['type']][n]
   if 'wet' in s['parameters']:line+=f" ({s['parameters']['wet']:.0%})"
   if s['type']=='deesser':line+=f" ({s['parameters'].get('frequency_hz',5500)} Hz, max. {s['parameters'].get('max_reduction_db',6)} dB)"
   details.append(line)
  caveat=('Rekonstruktion kann Klangfarbe und Details verändern; das Ergebnis ist mono.' if reconstruction else 'Stärkere Reinigung kann Höhen oder Details reduzieren.' if types & {'dereverb','deecho','deesser'} else 'Instrumentalreste können im Ergebnis verbleiben.') if lang=='de' else ('Reconstruction may change timbre and details; output is mono.' if reconstruction else 'Stronger cleanup may reduce high frequencies or details.' if types & {'dereverb','deecho','deesser'} else 'Some instrumental bleed may remain.')
  result[lang]={'short':short,'description':' → '.join(details)+'. '+caveat,'use_case':('Komplette Songs / Remixe' if separation else 'Bereits isolierte Vocals') if lang=='de' else ('Full songs / remixes' if separation else 'Isolated vocals'),'intensity':('Stark' if reconstruction else 'Mittel' if len(types)>2 else 'Schonend') if lang=='de' else ('Strong' if reconstruction else 'Medium' if len(types)>2 else 'Gentle'),'models':models}
 return result
