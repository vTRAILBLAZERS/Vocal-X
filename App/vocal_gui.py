"""VOCAL AI desktop interface. One QProcess owns GPU work at a time."""
import copy
import json
import os
import sys
import uuid
from pathlib import Path
from PySide6.QtCore import Qt, QProcess, QTimer, QUrl, QLockFile, QLocale
from PySide6.QtGui import QDesktopServices, QFontDatabase, QPixmap, QIcon, QShortcut, QKeySequence
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QFileDialog, QComboBox, QCheckBox,
    QLineEdit, QDoubleSpinBox, QFormLayout, QGroupBox, QScrollArea, QSplitter,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QPlainTextEdit,
    QProgressBar, QMessageBox, QInputDialog, QSizePolicy)
from vocal_pipeline.paths import data_root,prepare,preset_files,python_executable
from vocal_pipeline.models import catalog
from vocal_pipeline.schema import validate
import gui_i18n
from gui_i18n import tr

ROOT = Path(__file__).resolve().parent.parent
NAMES = {'restoration':tr('KI-Restaurierung (experimentell)'), 'vocal_separation':tr('Vocals isolieren'), 'dereverb':tr('Hall reduzieren'),
         'deecho':tr('Echo reduzieren'), 'deesser':tr('Zischlaute reduzieren'),
         'cleanup':tr('Tieffrequentes Rumpeln entfernen'), 'export':'Export'}
STATUS = {'pending':tr('Wartet'), 'running':tr('Läuft'), 'completed':tr('Fertig'),
          'completed_with_warnings':tr('Fertig mit Hinweisen'), 'failed':tr('Fehler'),
          'interrupted':tr('Unterbrochen')}
STYLE = '''
QWidget { background:#11151e; color:#e5eaf4; font-family:"Segoe UI"; font-size:13px; }
QMainWindow { background:#11151e; }
QLabel#title {font-size:26px; font-weight:700; color:#f5f7ff;}
QLabel#subtitle {color:#9aa8be;}
QPushButton {background:#263248; border:1px solid #36465f; border-radius:6px; padding:8px 12px;}
QPushButton:hover {background:#344764;}
QPushButton:disabled {color:#66758a; background:#1a2230;}
QPushButton#primary {background:#1aa65b; border-color:#46db87; font-weight:600;}
QGroupBox {border:1px solid #2e3b50; border-radius:8px; margin-top:15px; padding:14px 10px 8px; font-weight:600;}
QGroupBox::title {subcontrol-origin:margin; left:12px; padding:0 5px;}
QComboBox,QDoubleSpinBox,QLineEdit {background:#202a3b; border:1px solid #394861; padding:6px; border-radius:4px;}
QTableWidget,QPlainTextEdit {background:#171e2b; border:1px solid #2e3b50; border-radius:6px; selection-background-color:#254d3b;}
QHeaderView::section {background:#202b3c; border:0; padding:8px; font-weight:600;}
QProgressBar {border:0; border-radius:4px; background:#263248; text-align:center; min-height:20px;}
QProgressBar::chunk {background:#2fca75; border-radius:4px;}
QCheckBox {spacing:8px;}
QToolTip {background:#29374d; color:white; border:1px solid #526582;}
'''

def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    tmp.replace(path)

class StageEditor(QGroupBox):
    def __init__(self, stage, models):
        super().__init__(tr(NAMES.get(stage['type'],stage['type'])))
        self.stage=copy.deepcopy(stage); self.models=models; self.fields={}
        form=QFormLayout(self)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.enabled=QCheckBox(tr('Aktiv')); self.enabled.setChecked(stage['enabled'])
        self.optional=QCheckBox(tr('Bei Fehler überspringen')); self.optional.setChecked(stage['optional'])
        flags=QHBoxLayout(); flags.addWidget(self.enabled); flags.addWidget(self.optional)
        form.addRow(flags)
        if stage['type']=='export':
            self.enabled.setEnabled(False); self.optional.setEnabled(False)
        if stage['model'] and stage['type']!='restoration':
            self.model=QComboBox()
            self.model.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Fixed)
            self.model.setMinimumWidth(130)
            for slug in models:
                compatible=('de-reverb' in slug) == (stage['type']!='vocal_separation')
                if compatible or slug==stage['model']:
                    label=slug.replace('roformer-model-','').replace('melband-roformer-','').replace('bs-roformer-','')
                    self.model.addItem(label,slug)
            self.model.setCurrentIndex(self.model.findData(stage['model']))
            form.addRow(tr('Modell'),self.model)
        if stage['type']=='restoration':
            full=stage['model']=='anyenhance-360m-selfcritic-v2'
            warning=QLabel(tr('AnyEnhance 360M · Sprache und Gesang\nSelf-Critic aktiv · rekonstruierte Mono-Stimme') if full else tr('AnyEnhance-v1 Baseline · für Sprache trainiert\nGesang experimentell · rekonstruierte Mono-Stimme'))
            if full:
                self.prompt=QLineEdit(stage['parameters'].get('prompt_path','')); self.prompt.setPlaceholderText(tr('Optional: trockene Aufnahme derselben Stimme'))
                browse=QPushButton(tr('Auswählen'))
                def select_prompt():
                    path,_=QFileDialog.getOpenFileName(self,tr('Referenzstimme auswählen'),'','WAV Audio (*.wav)')
                    if path: self.prompt.setText(path)
                browse.clicked.connect(select_prompt)
                row=QHBoxLayout();row.addWidget(self.prompt);row.addWidget(browse);form.addRow(tr('Referenzstimme'),row)
            warning.setWordWrap(True); form.addRow(warning)
        p=stage['parameters']
        specs={'timesteps':(tr('Generationsschritte'),4,40,1,20),'wet':(tr('Bearbeiteter Anteil'),0,1,.05,1.0),
               'frequency_hz':(tr('Ab Frequenz (Hz)'),1000,16000,100,5500),
               'threshold_db':(tr('Schwelle (dB)'),-80,0,1,-30),
               'max_reduction_db':(tr('Max. Absenkung (dB)'),.1,24,.5,6),
               'highpass_hz':(tr('Hochpass (Hz)'),10,500,5,65)}
        keys=(['wet','timesteps'] if stage['type']=='restoration' else ['wet'] if stage['model'] else ['frequency_hz','threshold_db','max_reduction_db'] if stage['type']=='deesser' else ['highpass_hz'] if stage['type']=='cleanup' else [])
        for k in keys:
            label,lo,hi,step,default=specs[k]
            field=QDoubleSpinBox();field.setLocale(QLocale('en_US' if gui_i18n.LANG=='en' else 'de_DE')); field.setRange(lo,hi); field.setSingleStep(step)
            if k=='timesteps': field.setDecimals(0)
            field.setValue(p.get(k,default)); form.addRow(label,field); self.fields[k]=field
        if stage['type']=='export':
            form.addRow(QLabel('WAV · 32-bit Float'))
            self.flac=QCheckBox(tr('Zusätzlich FLAC · 24-bit PCM')); self.flac.setChecked(p.get('flac',False)); form.addRow(self.flac)
        if stage['type']=='cleanup': form.addRow(QLabel(tr('Hochpassfilter; keine Rauschunterdrückung.')))

    def value(self):
        s=copy.deepcopy(self.stage)
        s['enabled']=self.enabled.isChecked(); s['optional']=self.optional.isChecked()
        for k,f in self.fields.items(): s['parameters'][k]=int(f.value()) if k=='timesteps' else f.value()
        if s['model'] and s['type']!='restoration':
            s['model']=self.model.currentData(); s['engine']=self.models[s['model']]['engine']
        if hasattr(self,'prompt'): s['parameters']['prompt_path']=self.prompt.text().strip()
        if s['type']=='export': s['parameters']['flac']=self.flac.isChecked()
        return s

class Window(QMainWindow):
    def __init__(self, root=ROOT):
        super().__init__(); self.root=Path(root).resolve(); self.data=prepare(self.root); self.models=catalog(self.root)
        self.settings_path=self.data/'Config/gui-settings.json'
        try: self.settings=json.loads(self.settings_path.read_text(encoding='utf-8'))
        except (OSError,ValueError): self.settings={}
        gui_i18n.set_language(self.settings.get('language','de'))
        self.queue_path=self.data/'Config/gui-queue.json'; self.items=[]; self.active=None
        self.process=None; self.auto=False; self.cancelled=False; self.buffer=''; self.log_file=None
        self.setWindowTitle('Vocal X by TRAILBLAZERS'); self.resize(1280,860); self.setMinimumSize(960,640)
        body=QWidget(); self.setCentralWidget(body); layout=QVBoxLayout(body); layout.setContentsMargins(22,18,22,18)
        header=QHBoxLayout(); header.setSpacing(18)
        def logo(name,width,height,bounds=None):
            pix=QPixmap(str(self.root/'App/assets'/name))
            if bounds: pix=pix.copy(*bounds)
            label=QLabel();label.setPixmap(pix.scaled(width,height,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation));label.setContentsMargins(0,0,0,0)
            return label
        header.addWidget(logo('vocal-x.png',170,80,(237,642,1560,730)))
        by=QLabel('by');by.setStyleSheet('font-size:18px;font-weight:600;');header.addWidget(by)
        header.addWidget(logo('trailblazers.png',165,72));header.addStretch()
        header.addWidget(logo('instagram.png',225,40,(37,431,927,138)))
        self.language=QComboBox();self.language.addItem('Deutsch','de');self.language.addItem('English','en')
        self.language.setCurrentIndex(self.language.findData(gui_i18n.LANG));self.language.setMinimumWidth(105)
        self.language_label=QLabel(tr('Sprache'));header.addWidget(self.language_label);header.addWidget(self.language)
        branding=QWidget();branding.setObjectName('branding');branding.setLayout(header);layout.addWidget(branding)
        self.setWindowIcon(QIcon(str(self.root/'App/assets/vocal-x.png')))
        split=QSplitter(); layout.addWidget(split,1)
        left=QWidget(); ll=QVBoxLayout(left); ll.setContentsMargins(0,12,12,0)
        self.presets=QComboBox(); ll.addWidget(QLabel('PRESETS')); ll.addWidget(self.presets)
        self.editor=QWidget(); self.editor_layout=QVBoxLayout(self.editor)
        scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(self.editor); ll.addWidget(scroll)
        self.save_button=QPushButton(tr('Als eigenes Preset speichern')); self.save_button.clicked.connect(self.save_preset); ll.addWidget(self.save_button)
        split.addWidget(left)
        right=QWidget(); rl=QVBoxLayout(right); rl.setContentsMargins(12,12,0,0)
        toolbar=QHBoxLayout()
        self.add_button=self.button(toolbar,tr('Dateien hinzufügen'),self.add_files)
        self.remove_button=self.button(toolbar,tr('Ausgewählte entfernen'),self.remove_selected)
        self.button(toolbar,tr('Job fortsetzen …'),self.import_job)
        rl.addLayout(toolbar)
        note=QLabel(tr('Jede Datei übernimmt das links gewählte Preset beim Hinzufügen.')); note.setObjectName('subtitle'); rl.addWidget(note)
        self.table=QTableWidget(0,3); self.table.setHorizontalHeaderLabels([tr('Audiodatei'),'Preset','Status'])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True); self.table.setColumnWidth(0,270); self.table.setColumnWidth(1,170)
        self.delete_shortcut=QShortcut(QKeySequence(Qt.Key.Key_Delete),self.table)
        self.delete_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.delete_shortcut.activated.connect(self.remove_selected)
        self.remove_button.setToolTip(tr('Entf: nur aus der Warteschlange entfernen. Audiodateien bleiben erhalten.'))
        rl.addWidget(self.table,2)
        actions=QHBoxLayout()
        self.start_button=self.button(actions,tr('Warteschlange starten'),self.start_queue); self.start_button.setObjectName('primary')
        self.pause_button=self.button(actions,tr('Nach Song pausieren'),self.pause_queue)
        self.stop_button=self.button(actions,tr('Aktuellen abbrechen'),self.stop)
        rl.addLayout(actions)
        more=QHBoxLayout(); self.button(more,tr('Ausgewählten fortsetzen'),self.retry_selected)
        self.output_button=self.button(more,tr('Ergebnisordner öffnen'),self.open_output);self.output_button.setToolTip(tr('Öffnet den ausgewählten Track, sonst das letzte Ergebnis oder Output.')); rl.addLayout(more)
        self.status_label=QLabel(tr('Bereit. Dateien hinzufügen und Warteschlange starten.')); self.status_label.setWordWrap(True); rl.addWidget(self.status_label)
        self.progress=QProgressBar(); self.progress.setValue(0); rl.addWidget(self.progress)
        rl.addWidget(QLabel(tr('VERARBEITUNGSLOG')))
        self.log=QPlainTextEdit(); self.log.setReadOnly(True); self.log.setMaximumBlockCount(2500); rl.addWidget(self.log,1)
        split.addWidget(right); split.setSizes([410,820])
        self.load_presets(); self.presets.setCurrentIndex(max(0,self.presets.findText('Clean Acapella')))
        self.presets.currentIndexChanged.connect(self.load_editor); self.load_editor()
        self.restore(); self.render_queue()
        self.timer=QTimer(self); self.timer.timeout.connect(self.poll); self.timer.start(700)
        self.language.currentIndexChanged.connect(self.change_language)
        self.retranslate()

    def button(self,layout,label,slot):
        b=QPushButton(label); b.clicked.connect(slot); layout.addWidget(b); return b

    def load_presets(self):
        self.presets.blockSignals(True); self.presets.clear()
        for f in preset_files(self.root):
            try:
                p=json.loads(f.read_text(encoding='utf-8-sig')); validate(p,self.root)
                self.presets.addItem(tr(p['name']),p)
            except Exception as e: self.log.appendPlainText(tr('Preset nicht geladen:')+f' {f.name}: {e}')
        self.presets.blockSignals(False)

    def load_editor(self):
        while self.editor_layout.count():
            item=self.editor_layout.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().setParent(None)
                item.widget().deleteLater()
        self.editors=[]
        p=self.presets.currentData()
        if p:
            for stage in p['stages']:
                e=StageEditor(stage,self.models); self.editors.append(e); self.editor_layout.addWidget(e)
        self.editor_layout.addStretch()

    def pipeline(self):
        p=copy.deepcopy(self.presets.currentData())
        if not p: raise ValueError(tr('Kein gültiges Preset vorhanden.'))
        p['stages']=[e.value() for e in self.editors]; validate(p,self.root); return p

    def save_preset(self):
        name,ok=QInputDialog.getText(self,tr('Eigenes Preset'),tr('Name:'))
        if not ok or not name.strip(): return
        try:
            p=self.pipeline(); p['name']=name.strip()
            path=self.data/'Pipelines/Custom'/('gui-'+uuid.uuid4().hex[:12]+'.json')
            atomic_json(path,p); self.load_presets(); self.presets.setCurrentIndex(self.presets.findText(tr(p['name']))); self.load_editor()
        except Exception as e: self.error(e)

    def persist(self): atomic_json(self.queue_path,self.items)

    def restore(self):
        if not self.queue_path.exists(): return
        try:
            items=json.loads(self.queue_path.read_text(encoding='utf-8'))
            if not isinstance(items,list): raise ValueError(tr('Ungültiges Warteschlangenformat'))
            for item in items:
                if not isinstance(item,dict) or not all(k in item for k in ('id','source','pipeline','status')): raise ValueError(tr('Ungültiger Eintrag'))
                validate(item['pipeline'],self.root)
                if item['status']=='running': item['status']='interrupted'
            self.items=items
        except Exception as e: self.error(tr('Warteschlange konnte nicht geladen werden:')+f' {e}')

    def add_files(self):
        files,_=QFileDialog.getOpenFileNames(self,tr('Audiodateien auswählen'),str(self.root/'Input'),tr('Audio (*.wav *.flac *.aif *.aiff *.ogg *.mp3);;Alle Dateien (*)'))
        if not files: return
        try:
            p=self.pipeline()
            for f in files:
                self.items.append(dict(id=uuid.uuid4().hex,source=f,pipeline=copy.deepcopy(p),status='pending'))
            self.persist(); self.render_queue()
        except Exception as e: self.error(e)

    def selected(self):
        rows=sorted({i.row() for i in self.table.selectedIndexes()})
        return [self.items[r] for r in rows]

    def remove_selected(self):
        selected=self.selected(); self.items=[i for i in self.items if i not in selected or i is self.active]
        self.persist(); self.render_queue()

    def retry_selected(self):
        for item in self.selected():
            if item['status'] in ('failed','interrupted','completed_with_warnings'): item['status']='pending'
        self.persist(); self.render_queue()

    def import_job(self):
        f,_=QFileDialog.getOpenFileName(self,tr('Job-Zustand auswählen'),str(self.data/'Processing/Jobs'),'Job (state.json)')
        if not f: return
        try:
            path=Path(f).resolve(); jobs=(self.data/'Processing/Jobs').resolve()
            if path.parent.parent!=jobs: raise ValueError(tr('Bitte einen Job aus Processing/Jobs wählen.'))
            state=json.loads(path.read_text(encoding='utf-8')); identity=state['identity']
            validate(identity['pipeline'],self.root)
            if any(i.get('job')==path.parent.name for i in self.items): raise ValueError(tr('Dieser Job steht bereits in der Warteschlange.'))
            self.items.append(dict(id=uuid.uuid4().hex,source=identity['source'],pipeline=identity['pipeline'],job=path.parent.name,status='pending'))
            self.persist(); self.render_queue()
        except Exception as e: self.error(e)

    def render_queue(self):
        selected_ids={self.table.item(i.row(),0).data(Qt.ItemDataRole.UserRole) for i in self.table.selectedIndexes() if self.table.item(i.row(),0)}
        self.table.setRowCount(len(self.items))
        for row,item in enumerate(self.items):
            for col,text in enumerate([Path(item['source']).name,tr(item['pipeline']['name']),tr(STATUS.get(item['status'],item['status']))]):
                cell=QTableWidgetItem(text); cell.setToolTip(item['source'] if col==0 else item.get('error','') if col==2 else json.dumps(item['pipeline'],ensure_ascii=False,indent=2)); cell.setData(Qt.ItemDataRole.UserRole,item['id']); self.table.setItem(row,col,cell)
            if item['id'] in selected_ids:
                for col in range(3): self.table.item(row,col).setSelected(True)
        self.stop_button.setEnabled(self.active is not None)

    def start_queue(self):
        self.auto=True; self.next_job()

    def pause_queue(self):
        self.auto=False; self.status_label.setText(tr('Pausiert nach dem aktuellen Song.') if self.active else tr('Warteschlange pausiert.'))

    def next_job(self):
        if self.active or not self.auto: return
        item=next((i for i in self.items if i['status']=='pending'),None)
        if not item:
            self.auto=False; self.status_label.setText(tr('Warteschlange beendet. Ergebnisse und mögliche Fehler stehen in der Liste.')); return
        self.active=item; self.cancelled=False; self.buffer=''; item['status']='running'; item.pop('error',None); item.pop('result_status',None)
        request=self.data/'Config/GUIRequests'/(item['id']+'.json')
        try:
            atomic_json(request,item); self.persist()
            self.log_file=open(request.with_suffix('.log'),'a',encoding='utf-8')
            process=QProcess(self); self.process=process
            process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
            process.readyReadStandardOutput.connect(self.read_process)
            process.finished.connect(self.finished)
            process.errorOccurred.connect(self.process_error)
            process.setWorkingDirectory(str(self.root/'App'))
            process.start(str(python_executable(self.root)),['-X','utf8','-u',str(self.root/'App/gui_worker.py'),'--root',str(self.root),'--data-root',str(self.data),'--request',str(request)])
            self.log.appendPlainText('\n▶ '+item['source']); self.status_label.setText(tr('Modelle und Eingabe werden geprüft …')); self.progress.setRange(0,0)
            self.render_queue()
        except Exception as e:
            item['error']=str(e); self.finished(1,QProcess.ExitStatus.NormalExit)

    def read_process(self):
        if not self.process: return
        text=bytes(self.process.readAllStandardOutput()).decode('utf-8',errors='replace')
        if self.log_file: self.log_file.write(text); self.log_file.flush()
        self.buffer+=text
        while '\n' in self.buffer:
            line,self.buffer=self.buffer.split('\n',1)
            self.consume(line)

    def consume(self,line):
        if line.startswith('VOCAL_GUI_EVENT '):
            try:
                data=json.loads(line[len('VOCAL_GUI_EVENT '):])
                if self.active:
                    for k in ('job','output','error'): 
                        if k in data: self.active[k]=data[k]
                    if 'status' in data: self.active['result_status']=data['status']
                    self.persist()
            except Exception as e: self.log.appendPlainText(str(e))
        else: self.log.appendPlainText(line.rstrip())

    def process_error(self,error):
        if error==QProcess.ProcessError.FailedToStart and self.active:
            self.active['error']=self.process.errorString(); self.finished(1,QProcess.ExitStatus.NormalExit)

    def finished(self,code,_exit_status):
        if not self.active: return
        self.read_process()
        if self.buffer: self.consume(self.buffer); self.buffer=''
        item=self.active
        item['status']='interrupted' if self.cancelled else item.pop('result_status','failed') if code==0 else 'failed'
        if code!=0 and not self.cancelled and not item.get('error'): item['error']=tr('Verarbeitung beendet mit Exitcode')+f' {code}. '+tr('Siehe Log.')
        if self.log_file: self.log_file.close(); self.log_file=None
        if self.process: self.process.deleteLater(); self.process=None
        self.active=None; self.persist(); self.render_queue(); self.progress.setRange(0,100); self.progress.setFormat('%p%')
        self.progress.setValue(100 if item['status'].startswith('completed') else 0)
        self.status_label.setText(tr(STATUS[item['status']])+': '+Path(item['source']).name)
        QTimer.singleShot(200,self.next_job)

    def stop(self):
        self.auto=False
        if self.process and self.active:
            self.cancelled=True; self.status_label.setText(tr('Verarbeitung wird abgebrochen …')); self.process.kill()

    def poll(self):
        if not self.active or not self.active.get('job'): return
        try:
            state=json.loads((self.data/'Processing/Jobs'/self.active['job']/'state.json').read_text())
            stages=state['stages']; total=len(self.active['pipeline']['stages'])
            done=sum(s['status'] in ('completed','disabled','optional_failed') for s in stages.values())
            running=next((k for k,v in stages.items() if v['status']=='running'),None)
            self.progress.setRange(0,total); self.progress.setValue(done); self.progress.setFormat(tr('%v / %m Stufen'))
            self.status_label.setText(Path(self.active['source']).name+' · '+(tr(NAMES.get(running,running)) if running else tr('Vorbereitung / Abschluss')))
        except (OSError,ValueError,KeyError): pass

    def output_directory(self):
        selected=self.selected()
        item=selected[0] if selected else next((i for i in reversed(self.items) if i.get('output') or i['status'].startswith('completed')),None)
        candidates=[]
        if item:
            if item.get('job'):
                job=(self.data/'Processing/Jobs'/item['job']).resolve()
                if job.parent==(self.data/'Processing/Jobs').resolve():
                    try:
                        state=json.loads((job/'state.json').read_text(encoding='utf-8'))
                        if state.get('output_folder'): candidates.append(Path(state['output_folder']))
                        if state.get('output'): candidates.append(Path(state['output']).parent)
                    except (OSError,ValueError): pass
            if item.get('output'):
                output=Path(item['output']);candidates.append(output if output.is_dir() else output.parent)
        candidates.append(self.data/'Output')
        for path in candidates:
            if path.is_dir(): return path.resolve()
        (self.data/'Output').mkdir(parents=True,exist_ok=True)
        return (self.data/'Output').resolve()

    def open_output(self):
        try:
            target=self.output_directory()
            if os.name=='nt': os.startfile(str(target),'open')
            elif not QDesktopServices.openUrl(QUrl.fromLocalFile(str(target))): raise OSError(str(target))
        except Exception as e: self.error(tr(tr('Ergebnisordner konnte nicht geöffnet werden:'))+' '+str(e))

    def change_language(self):
        gui_i18n.set_language(self.language.currentData())
        self.settings['language']=gui_i18n.LANG;atomic_json(self.settings_path,self.settings)
        self.retranslate()

    def retranslate(self):
        for widget in self.findChildren(QWidget):
            for getter,setter in [('text','setText'),('title','setTitle'),('placeholderText','setPlaceholderText'),('toolTip','setToolTip')]:
                if isinstance(widget,QLineEdit) and getter=='text': continue
                if hasattr(widget,getter) and hasattr(widget,setter):
                    value=getattr(widget,getter)()
                    if isinstance(value,str): getattr(widget,setter)(tr(gui_i18n.original(value)))
        self.table.setHorizontalHeaderLabels([tr('Audiodatei'),'Preset','Status'])
        for index in range(self.presets.count()):self.presets.setItemText(index,tr(self.presets.itemData(index)['name']))
        self.progress.setFormat(tr('%v / %m Stufen') if self.active and self.progress.maximum()!=100 else '%p%')
        for field in self.findChildren(QDoubleSpinBox): field.setLocale(QLocale('en_US' if gui_i18n.LANG=='en' else 'de_DE'))
        self.render_queue()

    def error(self,e): QMessageBox.warning(self,'Vocal X',str(e))

    def closeEvent(self,event):
        if self.active:
            answer=QMessageBox.question(self,tr('Verarbeitung läuft'),tr('Aktuelle Verarbeitung abbrechen und schließen? Fertige Stufen bleiben für Resume erhalten.'))
            if answer!=QMessageBox.StandardButton.Yes: event.ignore(); return
            process=self.process
            self.stop()
            if process is not None: process.waitForFinished(5000)
        self.persist(); event.accept()

def main():
    import ctypes
    try: ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('TRAILBLAZERS.VocalX')
    except OSError: pass
    app=QApplication(sys.argv); app.setStyle('Fusion'); app.setStyleSheet(STYLE)
    QFontDatabase.addApplicationFont(str(Path(os.environ.get('WINDIR',r'C:\Windows'))/'Fonts/segoeui.ttf'))
    user_data=prepare(ROOT)
    lock=QLockFile(str(user_data/'Config/gui.lock'))
    if not lock.tryLock(100):
        if len(sys.argv)>1:
            atomic_json(user_data/'Config/LaunchRequests'/(uuid.uuid4().hex+'.json'),sys.argv[1:]);return 0
        QMessageBox.information(None,'Vocal X',tr('Die Desktop-App ist bereits geöffnet.')); return 0
    try:
        from qol_window import Window as QOLWindow
        window=QOLWindow(); window.apply_theme(); window.show(); return app.exec()
    except Exception as e:
        QMessageBox.critical(None,tr('Vocal X – Startfehler'),str(e)); return 1

if __name__=='__main__': sys.exit(main())
