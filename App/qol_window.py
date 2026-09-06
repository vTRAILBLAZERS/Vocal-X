import license_service
from vocal_license import APP_VERSION, message as license_message
"""Vocal X desktop workflow extensions; inference stays in the existing worker."""
import copy,json,os,sys,time,uuid,shutil,subprocess
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,QThread,Signal,QMimeData,QByteArray,QRect,QSize,QProcess
from PySide6.QtGui import QAction,QKeySequence,QShortcut,QDrag,QIcon,QColor
from PySide6.QtWidgets import (QApplication,QWidget,QLabel,QPushButton,QLineEdit,QMenu,QDialog,QVBoxLayout,QHBoxLayout,QFormLayout,QFileDialog,QMessageBox,QCheckBox,QComboBox,QInputDialog,QAbstractItemView,QSystemTrayIcon,QDialogButtonBox,QSpacerItem,QSizePolicy,QStyledItemDelegate,QStyleOptionViewItem,QStyle)
import vocal_gui as base
import gui_i18n
from qol_audio import Audition,txt
from vocal_pipeline.policy import settings,wav_info,hardware,output_root,DEFAULTS
from vocal_pipeline.output_layout import track_directory
from vocal_pipeline.schema import validate
from vocal_pipeline import __version__
from preset_info import describe

def valid_wavs(paths):
 accepted=[];rejected=[]
 for path in paths:
  try:wav_info(path);accepted.append(str(Path(path).resolve()))
  except (OSError,ValueError,TypeError):rejected.append(str(path))
 return accepted,rejected
class PresetDelegate(QStyledItemDelegate):
 def sizeHint(self,option,index):return QSize(360,54)
 def paint(self,painter,option,index):
  opt=QStyleOptionViewItem(option);self.initStyleOption(opt,index);opt.text='';option.widget.style().drawControl(QStyle.ControlElement.CE_ItemViewItem,opt,painter,option.widget)
  painter.save();light=getattr(self.parent().window(),'settings',{}).get('theme')=='light';painter.setPen(QColor('#15251d' if light and not option.state & QStyle.StateFlag.State_Selected else '#e5eaf4'));rect=option.rect.adjusted(8,4,-8,-4);font=painter.font();font.setBold(True);painter.setFont(font);painter.drawText(rect.adjusted(0,0,0,-22),Qt.AlignmentFlag.AlignVCenter,str(index.data()))
  font.setBold(False);font.setPointSize(max(8,font.pointSize()-1));painter.setFont(font);painter.setPen(QColor('#87ba9e'));short=str(index.data(Qt.ItemDataRole.ToolTipRole) or '');short=painter.fontMetrics().elidedText(short,Qt.TextElideMode.ElideRight,rect.width());painter.drawText(rect.adjusted(0,22,0,0),Qt.AlignmentFlag.AlignVCenter,short);painter.restore()
class InfoLabel(QLabel):
 def fit(self):
  height=self.fontMetrics().boundingRect(QRect(0,0,max(100,self.width()-24),10000),Qt.TextFlag.TextWordWrap,self.text()).height()+28
  self.setFixedHeight(height)
 def setText(self,text):super().setText(text);self.fit()
 def resizeEvent(self,event):super().resizeEvent(event);self.fit()
class Probe(QThread):
 done=Signal(dict)
 def run(self):self.done.emit(hardware())

class Window(base.Window):
 def __init__(self,root=base.ROOT,startup=True):
  self.ready_qol=False;self.session_dirty=False;self.undo_items=[];self.started=0;self.track_started=0;self.model_started=0;self.current_stage=None;self.block_progress=None;self.batch_ids=set();self.hw={'cuda':False,'gpu':'…','vram':0};self.preview_job=False;self.last_selected=None
  super().__init__(root)
  self.settings=settings(self.root);self.session_dirty=self.session_dirty or self.settings.get('session_open',False);self.settings['session_open']=True;self.setWindowTitle('Vocal X');self.setAcceptDrops(True)
  self.setWindowIcon(QIcon(str(self.root/'App/assets/taskbar-x.ico')))
  menu=self.menuBar().addMenu('Vocal X');self.settings_action=menu.addAction('');self.settings_action.triggered.connect(self.show_settings)
  self.license_action=menu.addAction('');self.license_action.triggered.connect(self.show_license)
  self.save_queue_action=menu.addAction('');self.save_queue_action.triggered.connect(self.save_queue_file)
  self.load_queue_action=menu.addAction('');self.load_queue_action.triggered.connect(self.load_queue_file)
  self.recent_menu=menu.addMenu('');self.favorite_menu=menu.addMenu('')
  self.import_preset_action=menu.addAction('');self.import_preset_action.triggered.connect(self.import_preset)
  self.export_preset_action=menu.addAction('');self.export_preset_action.triggered.connect(self.export_preset)
  self.presets.view().setItemDelegate(PresetDelegate(self.presets))
  ll=self.presets.parentWidget().layout()
  self.preset_info=InfoLabel();self.preset_info.setSizePolicy(QSizePolicy.Policy.Preferred,QSizePolicy.Policy.Maximum);self.preset_info.setWordWrap(True);self.preset_info.setStyleSheet('color:#e5eaf4;background:#1c2b24;border:1px solid #315540;border-radius:7px;padding:10px;');ll.insertWidget(2,self.preset_info)
  row=QHBoxLayout();self.favorite=QPushButton('☆');self.favorite.setMaximumWidth(48);self.favorite.clicked.connect(self.toggle_favorite);row.addWidget(self.favorite)
  self.mode=QCheckBox('Advanced');self.mode.setChecked(self.settings['advanced']);self.mode.toggled.connect(self.set_mode);row.addWidget(self.mode)
  self.duplicate=QPushButton();self.duplicate.clicked.connect(self.save_preset);row.addWidget(self.duplicate);ll.insertLayout(3,row)
  self.simple_spacer=QSpacerItem(0,0,QSizePolicy.Policy.Minimum,QSizePolicy.Policy.Expanding);ll.insertSpacerItem(ll.count()-1,self.simple_spacer)
  self.search=QLineEdit();self.search.textChanged.connect(self.filter_queue)
  rl=self.table.parentWidget().layout();rl.insertWidget(2,self.search)
  self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
  self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu);self.table.customContextMenuRequested.connect(self.context_menu)
  self.table.setDragEnabled(True);self.table.setAcceptDrops(True);self.table.viewport().setAcceptDrops(True);self.table.installEventFilter(self);self.table.viewport().installEventFilter(self)
  self.table.itemSelectionChanged.connect(self.track_selected)
  table_space=QShortcut(QKeySequence('Space'),self.table);table_space.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut);table_space.activated.connect(lambda:self.audition.toggle())
  self.total_label=QLabel();self.time_label=QLabel();rl.addWidget(self.total_label);rl.addWidget(self.time_label)
  self.audition=Audition(self.root);self.audition.preview.connect(self.render_preview);rl.addWidget(self.audition)
  self.rerun_button=QPushButton();self.rerun_button.clicked.connect(self.rerun);rl.addWidget(self.rerun_button)
  self.undo_button=QPushButton();self.undo_button.clicked.connect(self.undo_remove);self.undo_button.hide();rl.addWidget(self.undo_button)
  footer=QHBoxLayout();self.gpu_label=QLabel();footer.addWidget(self.gpu_label);footer.addStretch();version=QLabel('Vocal X BETA v'+APP_VERSION);version.setStyleSheet('color:#81948b;font-size:11px');footer.addWidget(version);self.centralWidget().layout().addLayout(footer)
  from qol_windows import Taskbar
  self.taskbar=Taskbar(self)
  self.gpu_query=QProcess(self);self.gpu_query.readyReadStandardOutput.connect(self.gpu_usage);self.last_gpu_query=0
  self.tray=QSystemTrayIcon(self.windowIcon(),self);self.tray.setToolTip('Vocal X');self.tray.show()
  for key,slot in [('Ctrl+O',self.add_files),('Ctrl+Return',self.start_queue)]:
   shortcut=QShortcut(QKeySequence(key),self);shortcut.activated.connect(slot)
  space=QShortcut(QKeySequence('Space'),self.audition);space.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut);space.activated.connect(self.audition.toggle)
  self.ready_qol=True;self.refresh_preset_order();self.retranslate();self.set_mode(self.mode.isChecked());self.render_queue()
  if self.settings.get('geometry'):self.restoreGeometry(QByteArray.fromBase64(self.settings['geometry'].encode()))
  self.session_timer=QTimer(self);self.session_timer.timeout.connect(self.save_session);self.session_timer.start(10000)
  if startup:
   self.probe=Probe(self);self.probe.done.connect(self.hardware_ready);self.probe.start()
  self.start_button.setEnabled(False)
  self.poll()
 def restore(self):
  try:
   data=json.loads(self.queue_path.read_text(encoding='utf-8'));data=data if isinstance(data,list) else [];self.session_dirty=any(isinstance(i,dict) and i.get('status')=='running' for i in data);self.items=[]
   for item in data:
    try:
     if not isinstance(item,dict) or any(k not in item for k in ('id','source','pipeline','status')) or item['status'] not in base.STATUS:continue
     wav_info(item['source']);validate(item['pipeline'],self.root)
     if item['status']=='running':item['status']='interrupted'
     if item.get('job'):
      job=(self.data/'Processing/Jobs'/item['job']).resolve()
      if job.parent==(self.data/'Processing/Jobs').resolve() and (job/'state.json').is_file():
       record=json.loads((job/'state.json').read_text(encoding='utf-8'))
       if record.get('output'):item['output']=record['output']
     self.items.append(item)
    except (KeyError,OSError,ValueError,TypeError):pass
  except (OSError,ValueError,TypeError):self.items=[]
 def update_license_controls(self):
  value,error=license_service.status(self.root)
  allowed=bool(value and self.hw.get('cuda') and self.settings['setup_complete'])
  self.start_button.setEnabled(allowed);self.audition.render.setEnabled(allowed)
  return value,error
 def show_license(self):
  from license_dialog import LicenseDialog
  dialog=LicenseDialog(self.root,self);dialog.exec()
  value,error=self.update_license_controls()
  if value and self.hw.get('cuda') and not self.settings['setup_complete']:self.choose_initial_output()
 def choose_initial_output(self):
  folder=QFileDialog.getExistingDirectory(self,txt('Wo sollen deine fertigen Vocal-X-Ergebnisse gespeichert werden?','Where should Vocal X save your finished results?'),str(output_root(self.root)))
  if folder:self.settings.update(output_dir=folder,setup_complete=True);self.save_settings()
  self.update_license_controls()
 def license_allows_processing(self):
  value,error=self.update_license_controls()
  if error:self.status_label.setText(license_message(error,gui_i18n.LANG));return False
  return True
 def hardware_ready(self,data):
  self.hw=data;self.gpu_label.setText(f"{data['gpu']} · CUDA {data.get('runtime') or '—'} · {data['vram']} GB VRAM")
  if not self.settings['setup_complete']:
   QMessageBox.information(self,'Vocal X',txt('Vocal X benötigt eine NVIDIA-Grafikkarte mit CUDA-Unterstützung. Eine kompatible NVIDIA-GPU ist Voraussetzung für die AI-Verarbeitung.','Vocal X requires an NVIDIA graphics card with CUDA support for AI processing.')+'\n\n'+self.gpu_label.text())
  value,error=self.update_license_controls()
  if data['cuda']:
   if error:self.show_license()
   elif not self.settings['setup_complete']:self.choose_initial_output()
  else:self.status_label.setText(txt('Keine kompatible CUDA-GPU. AI-Verarbeitung ist deaktiviert.','No compatible CUDA GPU. AI processing is disabled.'))
  if self.session_dirty:
   if QMessageBox.question(self,'Vocal X',txt('Letzte Vocal-X-Sitzung wiederherstellen?','Restore the previous Vocal X session?'))!=QMessageBox.StandardButton.Yes:self.items=[];self.persist();self.render_queue()
  if len(sys.argv)>1:self.add_paths(sys.argv[1:])
 def save_settings(self):base.atomic_json(self.settings_path,self.settings)
 def save_session(self):
  self.settings['selected_preset']=self.presets.currentData()['name'] if self.presets.currentData() else ''
  self.settings['geometry']=bytes(self.saveGeometry().toBase64()).decode();self.save_settings();self.persist()
 def change_language(self):
  super().change_language()
  if self.ready_qol:self.audition.retranslate()
 def retranslate(self):
  super().retranslate()
  if not self.ready_qol:return
  self.license_action.setText(txt('Lizenz / Aktivierung …','License / Activation …'))
  self.rerun_button.setText(txt('Ausgewählte erneut rendern','Render selected again'));self.rerun_button.setToolTip(txt('Mit den bisherigen Track-Einstellungen erneut einreihen. Danach Start / Fortsetzen drücken.','Queue again with the existing track settings. Then press Start / Resume.'))
  self.settings_action.setText(txt('Einstellungen','Settings'));self.save_queue_action.setText(txt('Queue speichern …','Save queue …'));self.load_queue_action.setText(txt('Queue laden …','Load queue …'));self.import_preset_action.setText(txt('Preset importieren …','Import preset …'));self.export_preset_action.setText(txt('Preset exportieren …','Export preset …'))
  self.mode.setText(txt('Erweitert','Advanced'));self.recent_menu.setTitle(txt('Zuletzt verwendet','Recently used'));self.favorite_menu.setTitle(txt('Favoriten','Favorites'));self.search.setPlaceholderText(txt('Tracks suchen …','Search tracks …'));self.duplicate.setText(txt('Preset duplizieren','Duplicate preset'));self.undo_button.setText(txt('Entfernen rückgängig','Undo removal'));self.pause_button.setText(txt('Nach Schritt pausieren','Pause after stage'));self.start_button.setText(txt('Start / Fortsetzen','Start / Resume'));self.refresh_info();self.audition.retranslate()
  for index in range(self.presets.count()):
   p=self.presets.itemData(index);self.presets.setItemData(index,p.get('info',describe(p))[gui_i18n.LANG]['short'],Qt.ItemDataRole.ToolTipRole)
 def load_editor(self):
  super().load_editor()
  if self.ready_qol:
   self.refresh_info();self.set_mode(self.mode.isChecked())
   for e in self.editors:
    if hasattr(e,'prompt'):e.prompt.setToolTip(txt('Nur WAV: saubere Referenz derselben Stimme','WAV only: clean reference of the same voice'))
    for f in e.fields.values():f.valueChanged.connect(self.refresh_info)
    e.enabled.toggled.connect(self.refresh_info)
 def refresh_info(self):
  if not self.ready_qol or not self.presets.currentData():return
  p=self.pipeline();data=describe(p)[gui_i18n.LANG];custom=p.get('info',{}).get(gui_i18n.LANG,{})
  text=data['description']+'\n'+txt('Geeignet für: ','Use case: ')+custom.get('use_case',data['use_case'])+' · '+txt('Eingriff: ','Intensity: ')+data['intensity']+' · '+txt('AI-Modelle: ','AI models: ')+str(data['models'])
  if custom.get('custom'):text=custom['description']+'\n'+text
  self.preset_info.setText(text);self.presets.setToolTip(custom.get('short',data['short']));self.favorite.setText('★' if p['name'] in self.settings['favorites'] else '☆')
 def refresh_preset_order(self):
  name=self.settings.get('selected_preset') or (self.presets.currentData() or {}).get('name');self.presets.blockSignals(True)
  data=[self.presets.itemData(i) for i in range(self.presets.count())]
  favorites=self.settings['favorites'];recent=self.settings['recent']
  data.sort(key=lambda p:(0 if p['name'] in favorites else 1 if p['name'] in recent else 2,p['name']))
  self.presets.clear()
  for p in data:
   self.presets.addItem(base.tr(p['name']),p);self.presets.setItemData(self.presets.count()-1,p.get('info',describe(p))[gui_i18n.LANG]['short'],Qt.ItemDataRole.ToolTipRole)
  for i,p in enumerate(data):
   if p['name']==name:self.presets.setCurrentIndex(i)
  self.presets.blockSignals(False);self.load_editor()
  self.refresh_preset_menus()
 def refresh_preset_menus(self):
  if self.ready_qol:
   for menu,names in [(self.recent_menu,self.settings['recent']),(self.favorite_menu,self.settings['favorites'])]:
    menu.clear();menu.setEnabled(bool(names))
    for preset_name in names:
     menu.addAction(base.tr(preset_name),lambda checked=False,n=preset_name:self.presets.setCurrentIndex(next((i for i in range(self.presets.count()) if self.presets.itemData(i)['name']==n),0)))
 def toggle_favorite(self):
  name=self.presets.currentData()['name'];fav=self.settings['favorites']
  if name in fav:fav.remove(name)
  else:fav.append(name)
  self.save_settings();self.refresh_preset_order()
 def set_mode(self,advanced):
  if not self.ready_qol:return
  self.settings['advanced']=advanced;self.save_settings();self.editor.parentWidget().parentWidget().setVisible(advanced);self.log.setVisible(advanced)
  self.simple_spacer.changeSize(0,0,QSizePolicy.Policy.Minimum,QSizePolicy.Policy.Fixed if advanced else QSizePolicy.Policy.Expanding);self.presets.parentWidget().layout().invalidate()
  for label in self.findChildren(QLabel):
   if label.text() in ('VERARBEITUNGSLOG','PROCESSING LOG'):label.setVisible(advanced)
 def add_files(self):
  paths,_=QFileDialog.getOpenFileNames(self,txt('WAV-Dateien hinzufügen','Add WAV files'),str(self.root/'Input'),'WAV Audio (*.wav)');self.add_paths(paths)
 def add_paths(self,paths):
  accepted,rejected=valid_wavs(paths);duplicates=0;p=self.pipeline();self.apply_performance(p);known={str(Path(i['source']).resolve()).casefold() for i in self.items}
  for path in accepted:
   if path.casefold() in known:duplicates+=1;continue
   dest=track_directory(self.root,path)/'Finale Vocal'
   if dest.exists() and list(dest.glob('*.wav')):
    box=QMessageBox(self);box.setWindowTitle('Vocal X');box.setText(Path(path).name+'\n'+txt('Ein fertiges Ergebnis existiert bereits.','A finished result already exists.'));again=box.addButton(txt('Erneut verarbeiten','Process again'),QMessageBox.ButtonRole.AcceptRole);show=box.addButton(txt('Ergebnis anzeigen','Show result'),QMessageBox.ButtonRole.ActionRole);box.addButton(txt('Überspringen','Skip'),QMessageBox.ButtonRole.RejectRole);box.exec()
    if box.clickedButton()==show:os.startfile(str(dest));continue
    if box.clickedButton()!=again:continue
   self.items.append(dict(id=uuid.uuid4().hex,source=path,pipeline=copy.deepcopy(p),status='pending'));known.add(path.casefold())
  self.settings['recent']=[p['name']]+[n for n in self.settings['recent'] if n!=p['name']][:5];self.save_settings();self.refresh_preset_menus();self.persist();self.render_queue()
  if rejected or duplicates:self.status_label.setText(txt(f'{len(rejected)} Dateien nicht hinzugefügt (nur lesbare WAV). {duplicates} Duplikate übersprungen.',f'{len(rejected)} files rejected (readable WAV only). {duplicates} duplicates skipped.'))
 def selected(self):
  ids={self.table.item(i.row(),0).data(Qt.ItemDataRole.UserRole) for i in self.table.selectedIndexes() if self.table.item(i.row(),0)}
  return [i for i in self.items if i['id'] in ids]
 def filter_queue(self):
  if not self.ready_qol:return
  query=self.search.text().casefold()
  for row,item in enumerate(self.items):self.table.setRowHidden(row,query not in Path(item['source']).name.casefold())
 def render_queue(self):
  super().render_queue()
  if self.ready_qol:
   self.filter_queue();batch=[i for i in self.items if not self.batch_ids or i['id'] in self.batch_ids];done=sum(i['status'] in ('completed','completed_with_warnings','failed') for i in batch);self.total_label.setText(txt('Gesamt','Total')+f': {done}/{len(batch)} Tracks')
 def remove_selected(self):
  self.undo_items=[(n,copy.deepcopy(i)) for n,i in enumerate(self.items) if i in self.selected() and i is not self.active];super().remove_selected()
  if self.ready_qol:self.undo_button.setVisible(bool(self.undo_items))
 def undo_remove(self):
  for n,item in self.undo_items:
   if all(i['id']!=item['id'] for i in self.items):self.items.insert(min(n,len(self.items)),item)
  self.undo_items=[];self.undo_button.hide();self.persist();self.render_queue()
 def move_next(self):
  chosen=[i for i in self.selected() if i is not self.active];remaining=[i for i in self.items if i not in chosen];index=remaining.index(self.active)+1 if self.active in remaining else 0
  self.items=remaining[:index]+chosen+remaining[index:];self.persist();self.render_queue()
 def eventFilter(self,obj,event):
  from PySide6.QtCore import QEvent
  if event.type()==QEvent.Type.DragEnter or event.type()==QEvent.Type.DragMove:
   if event.mimeData().hasUrls() or event.source() is self.table:event.acceptProposedAction();return True
  if event.type()==QEvent.Type.Drop:
   if event.mimeData().hasUrls():self.add_paths([u.toLocalFile() for u in event.mimeData().urls()]);event.acceptProposedAction();return True
   if event.source() is self.table:
    chosen=[i for i in self.selected() if i is not self.active];row=self.table.indexAt(event.position().toPoint()).row();target=self.items[row] if row>=0 else None;remaining=[i for i in self.items if i not in chosen];index=remaining.index(target) if target in remaining else len(remaining);self.items=remaining[:index]+chosen+remaining[index:];self.persist();self.render_queue();event.acceptProposedAction();return True
  return super().eventFilter(obj,event)
 def dragEnterEvent(self,e):
  if e.mimeData().hasUrls():e.acceptProposedAction()
 def dropEvent(self,e):self.add_paths([u.toLocalFile() for u in e.mimeData().urls()]);e.acceptProposedAction()
 def context_menu(self,pos):
  if not self.selected():return
  menu=QMenu(self)
  actions=[(txt('Abspielen','Play'),lambda:self.track_selected(force=True,autoplay=True)),(txt('Im Explorer anzeigen','Show in Explorer'),lambda:subprocess.Popen(['explorer.exe','/select,',self.selected()[0]['source']])),(txt('Ergebnisordner öffnen','Open output folder'),self.open_output),(txt('Entfernen','Remove'),self.remove_selected),(txt('Erneut verarbeiten','Process again'),self.rerun),(txt('Ab Fehler fortsetzen','Resume from failure'),self.retry_selected),(txt('Als Nächstes verarbeiten','Process next'),self.move_next),(txt('Aktuelles Preset anwenden','Apply current preset'),self.apply_preset),(txt('Dateiinformationen','File information'),self.file_info),(txt('Fehlerdetails','Error details'),lambda:QMessageBox.information(self,'Vocal X','\n'.join(i.get('error','—') for i in self.selected())))]
  for label,slot in actions:menu.addAction(label,slot)
  menu.exec(self.table.viewport().mapToGlobal(pos))
 def rerun(self):
  selected=[i for i in self.selected() if i is not self.active]
  if not selected:
   self.status_label.setText(txt('Bitte einen Track auswählen, der gerade nicht verarbeitet wird.','Select a track that is not currently processing.'));return
  for i in selected:
   i['status']='pending'
   for key in ('job','output','error','result_status','control'):i.pop(key,None)
  self.persist();self.render_queue()
  self.status_label.setText(txt(f'{len(selected)} Track(s) erneut eingereiht. Start / Fortsetzen drücken.',f'{len(selected)} track(s) queued again. Press Start / Resume.'))
 def apply_preset(self):
  p=self.pipeline()
  for i in self.selected():
   if i is not self.active:i['pipeline']=copy.deepcopy(p);i['status']='pending';i.pop('job',None)
  self.persist();self.render_queue()
 def file_info(self):
  lines=[]
  for i in self.selected():
   try:d=wav_info(i['source'])
   except (ValueError,OSError) as e:self.error(txt('Diese WAV-Datei konnte nicht gelesen werden.','This WAV file could not be read.')+' '+str(e));return
   lines.append(f"{Path(i['source']).name}\nWAV · {d['rate']/1000:g} kHz · {d['subtype']} · {d['channels']} ch · {d['duration']:.1f} s · {d['size']/1024**2:.1f} MB"+('\n'+txt('Hinweis: niedrige Samplerate oder sehr kurze Datei.','Note: low sample rate or very short file.') if d['warning'] else ''))
  QMessageBox.information(self,'Vocal X','\n\n'.join(lines))
 def track_selected(self,force=False,autoplay=False):
  if not self.ready_qol:return
  items=self.selected()
  if not items:return
  i=items[0]
  if i['id']==self.last_selected and not force:return
  self.last_selected=i['id'];self.audition.load(i['source'],i.get('output'),autoplay=autoplay)
 def output_directory(self):
  selected=self.selected()
  if selected and selected[0].get('preview'):return Path(selected[0].get('output',selected[0]['source'])).parent
  if selected and selected[0].get('output') or not selected and any(i.get('output') for i in self.items):return super().output_directory()
  if selected:
   path=track_directory(self.root,selected[0]['source'])
   if path.exists():return path
  path=output_root(self.root);path.mkdir(parents=True,exist_ok=True);return path
 def start_queue(self):
  if not self.license_allows_processing():return
  if not self.hw.get('cuda') or not self.settings['setup_complete']:self.error(txt('CUDA-GPU und abgeschlossene Ersteinrichtung erforderlich.','CUDA GPU and completed setup required.'));return
  if not self.active:
   self.batch_ids={i['id'] for i in self.items if i['status'] in ('pending','interrupted')};self.started=time.monotonic()
   for i in self.items:
    if i['status']=='interrupted':i['status']='pending'
  super().start_queue()
 def next_job(self):
  if not self.active and self.auto and not self.license_allows_processing():self.auto=False;return
  before=self.active;had_auto=self.auto
  if not before and had_auto:
   self.track_started=time.monotonic();self.model_started=self.track_started;self.current_stage=None;self.block_progress=None
   for item in self.items:
    if item['status']=='pending':
     try:
      wav_info(item['source'])
      for s in item['pipeline']['stages']:
       if s['enabled'] and s['parameters'].get('prompt_path'):wav_info(s['parameters']['prompt_path'])
      item['control']=str(self.data/'Config/GUIRequests'/(item['id']+'.pause'));Path(item['control']).unlink(missing_ok=True)
     except Exception as e:item.update(status='failed',error=str(e))
  super().next_job()
  if had_auto and not self.auto and not self.active and self.ready_qol:self.queue_completed()
 def pause_queue(self):
  self.auto=False
  if self.active:
   p=Path(self.active['control']);p.parent.mkdir(parents=True,exist_ok=True);p.touch();self.status_label.setText(txt('Pause nach dem aktuellen Schritt angefordert.','Pause requested after the current stage.'))
 def stop(self):
  menu=QMessageBox(self);menu.setWindowTitle('Vocal X');menu.setText(txt('Wie soll die Verarbeitung gestoppt werden?','How should processing stop?'))
  now=menu.addButton(txt('Schritt abbrechen','Cancel stage'),QMessageBox.ButtonRole.DestructiveRole);after=menu.addButton(txt('Track fertigstellen, dann stoppen','Finish track, then stop'),QMessageBox.ButtonRole.AcceptRole);menu.addButton(txt('Zurück','Back'),QMessageBox.ButtonRole.RejectRole);menu.exec()
  if menu.clickedButton()==now:super().stop()
  elif menu.clickedButton()==after:self.auto=False
 def read_process(self):
  if not self.process:return
  text=bytes(self.process.readAllStandardOutput()).decode('utf-8',errors='replace')
  if self.log_file:self.log_file.write(text);self.log_file.flush()
  self.buffer+=text.replace('\r','\n')
  while '\n' in self.buffer:
   line,self.buffer=self.buffer.split('\n',1);self.consume(line)
 def consume(self,line):
  import re
  total=re.search(r'Estimated total processing time for this track: ([0-9.]+)',line)
  remaining=re.search(r'Estimated time remaining: ([0-9.]+)',line)
  if total:self.estimate_total=float(total[1])
  if remaining and getattr(self,'estimate_total',0)>0:self.block_progress=(max(0,self.estimate_total-float(remaining[1])),self.estimate_total)
  match=re.search(r'AnyEnhance block (\d+)/(\d+)',line)
  if match:self.block_progress=(int(match[1]),int(match[2]))
  else:
   match=re.search(r'(\d+)%',line)
   if match:self.block_progress=(min(100,int(match[1])),100)
  super().consume(line)
 def gpu_usage(self):
  try:
   text=bytes(self.gpu_query.readAllStandardOutput()).decode().strip().splitlines()[0];usage,used,total=[float(x.strip()) for x in text.split(',')];self.gpu_label.setText(f"{self.hw['gpu']} · CUDA · {used/1024:.1f}/{total/1024:.1f} GB · {usage:.0f}%")
  except (ValueError,IndexError):pass
 def poll(self):
  super().poll()
  if not self.ready_qol:return
  if self.hw.get('cuda') and time.monotonic()-self.last_gpu_query>5 and self.gpu_query.state()==QProcess.ProcessState.NotRunning:
   self.last_gpu_query=time.monotonic();self.gpu_query.start('nvidia-smi',['--query-gpu=utilization.gpu,memory.used,memory.total','--format=csv,noheader,nounits','--id=0'])
  for request in (self.data/'Config/LaunchRequests').glob('*.json'):
   try:
    paths=json.loads(request.read_text(encoding='utf-8'));request.unlink();self.add_paths(paths if isinstance(paths,list) else [])
   except (OSError,ValueError):pass
  batch=[i for i in self.items if not self.batch_ids or i['id'] in self.batch_ids];done=sum(i['status'] in ('completed','completed_with_warnings','failed') for i in batch)
  self.total_label.setText(txt('Gesamt','Total')+f': {done}/{len(batch)} '+txt('Tracks','tracks'))
  elapsed=time.monotonic()-self.started if self.started else 0;eta=(elapsed/done*(len(batch)-done)) if done else None
  model='';fraction=''
  if self.active and self.active.get('job'):
   try:
    state=json.loads((self.data/'Processing/Jobs'/self.active['job']/'state.json').read_text());running=next((k for k,v in state['stages'].items() if v['status']=='running'),None)
    if running!=self.current_stage:self.current_stage=running;self.model_started=time.monotonic();self.block_progress=None;self.estimate_total=None
    stages=[s for s in self.active['pipeline']['stages'] if s['enabled']];stage=next((s for s in stages if s['id']==running),None)
    if stage:
     models=[s for s in stages if s['engine']!='DSP'];model=f"{stage['model'] or stage['type']}"+(f" · {models.index(stage)+1}/{len(models)}" if stage in models else '')
     if self.block_progress:
      a,b=self.block_progress;fraction=f' · {a/b:.0%}'
      if a:eta=(time.monotonic()-self.model_started)/a*(b-a)
     self.status_label.setText(model+fraction)
     for row,i in enumerate(self.items):
      if i is self.active:self.table.item(row,2).setText(txt('Modell','Model')+' '+model+fraction)
   except (OSError,ValueError,KeyError):pass
  self.taskbar.update(done,len(batch),self.active is not None)
  self.time_label.setText(txt('Laufzeit','Elapsed')+f' {elapsed:.0f}s · Track {max(0,time.monotonic()-self.track_started) if self.active else 0:.0f}s · '+txt('Modell','Model')+f' {max(0,time.monotonic()-self.model_started) if self.active else 0:.0f}s · ETA '+(f'~{eta:.0f}s' if eta is not None else '—'))
 def finished(self,code,status):
  item=self.active;super().finished(code,status)
  if item and item.get('preview') and item.get('output') and item['status'].startswith('completed'):self.audition.load(item['source'],item['output'])
 def queue_completed(self):
  items=[i for i in self.items if i['id'] in self.batch_ids];ok=sum(i['status'].startswith('completed') for i in items);bad=sum(i['status']=='failed' for i in items)
  if not items:return
  text=txt(f'{ok} Tracks fertig · {bad} Fehler',f'{ok} tracks completed · {bad} errors')
  if self.settings['notify']:self.tray.showMessage('Vocal X',text,QSystemTrayIcon.MessageIcon.Information,6000)
  if self.settings['sound']:QApplication.beep()
  if self.settings['open_after']:self.open_output()
  action=self.settings['after']
  if action=='close':self.close()
  elif action in ('sleep','shutdown'):
   box=QMessageBox(self);box.setWindowTitle('Vocal X');box.setText(txt('Geplante PC-Aktion jetzt ausführen?','Execute the selected PC action now?'));box.setStandardButtons(QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No);box.setDefaultButton(QMessageBox.StandardButton.No)
   if box.exec()==QMessageBox.StandardButton.Yes:
    if action=='shutdown':subprocess.Popen(['shutdown.exe','/s','/t','30'])
    else:
     import ctypes;ctypes.windll.powrprof.SetSuspendState(False,False,False)
 def render_preview(self,start,length):
  if not self.license_allows_processing():return
  if not self.hw.get('cuda') or not self.settings['setup_complete']:self.error(txt('CUDA und Ersteinrichtung erforderlich.','CUDA and initial setup required.'));return
  if self.active:self.error(txt('Vorschau nach dem laufenden Job starten.','Start preview after the current job.'));return
  selected=self.selected()
  if not selected:return
  import soundfile as sf
  source=selected[0]['source'];info=wav_info(source);folder=self.data/'Preview'/uuid.uuid4().hex;folder.mkdir(parents=True)
  x,sr=sf.read(source,start=int(start*info['rate']),frames=int(min(60,length)*info['rate']),dtype='float32',always_2d=True)
  if not len(x):self.error(txt('Leerer Vorschaubereich.','Empty preview region.'));return
  path=folder/'Original.wav';sf.write(path,x,sr,subtype='FLOAT')
  preview_preset=self.pipeline();self.apply_performance(preview_preset)
  item=dict(id=uuid.uuid4().hex,source=str(path),pipeline=preview_preset,status='pending',preview=True);self.items.insert(0,item);self.persist();self.render_queue()
  if not self.hw.get('cuda'):self.error(txt('CUDA nicht verfügbar.','CUDA unavailable.'));return
  self.batch_ids={item['id']};self.started=time.monotonic();self.auto=True;self.next_job();self.auto=False
 def save_queue_file(self):
  path,_=QFileDialog.getSaveFileName(self,'Vocal X','','Vocal X Queue (*.vxqueue)')
  if path:base.atomic_json(Path(path),{'version':1,'items':self.items})
 def load_queue_file(self):
  path,_=QFileDialog.getOpenFileName(self,'Vocal X','','Vocal X Queue (*.vxqueue)')
  if not path:return
  try:
   data=json.loads(Path(path).read_text(encoding='utf-8'));rejected=0
   for item in data['items']:
    try:
     wav_info(item['source']);validate(item['pipeline'],self.root)
     if any(Path(i['source']).resolve()==Path(item['source']).resolve() for i in self.items):continue
     item=dict(id=uuid.uuid4().hex,source=str(Path(item['source']).resolve()),pipeline=item['pipeline'],status='pending');self.items.append(item)
    except (KeyError,ValueError,OSError,TypeError):rejected+=1
   self.persist();self.render_queue();self.status_label.setText(txt(f'{rejected} ungültige Einträge übersprungen.',f'{rejected} invalid entries skipped.'))
  except Exception as e:self.error(e)
 def import_job(self):
  old=list(self.items);super().import_job();self.items=[i for i in self.items if i in old or not valid_wavs([i['source']])[1]];self.persist();self.render_queue()
 def save_preset(self):
  name,ok=QInputDialog.getText(self,txt('Eigenes Preset','Custom preset'),'Name:')
  if not ok or not name.strip():return
  p=self.pipeline();p['name']=name.strip();p['info']=describe(p)
  for lang in ('de','en'):
   for key,label in [('short','Kurzbeschreibung / Short description'),('description','Beschreibung / Description'),('use_case','Anwendungsfall / Use case')]:
    text,ok=QInputDialog.getText(self,f'{lang.upper()} · {label}',label,text=p['info'][lang][key])
    if not ok:return
    p['info'][lang][key]=text
   p['info'][lang]['custom']=True
  base.atomic_json(self.data/'Pipelines/Custom'/('gui-'+uuid.uuid4().hex+'.json'),p);self.load_presets();self.settings['selected_preset']=p['name'];self.refresh_preset_order()
 def export_preset(self):
  path,_=QFileDialog.getSaveFileName(self,'Vocal X','','Vocal X Preset (*.vxpreset)')
  if path:base.atomic_json(Path(path),self.pipeline())
 def import_preset(self):
  path,_=QFileDialog.getOpenFileName(self,'Vocal X','','Vocal X Preset (*.vxpreset)')
  if not path:return
  try:
   p=json.loads(Path(path).read_text(encoding='utf-8'));validate(p,self.root);p.setdefault('info',describe(p));base.atomic_json(self.data/'Pipelines/Custom'/('import-'+uuid.uuid4().hex+'.json'),p);self.load_presets();self.refresh_preset_order()
  except Exception as e:self.error(e)
 def apply_performance(self,p):
  steps={'Eco':8,'Maximum':32}.get(self.settings['performance'])
  if steps:
   for s in p['stages']:
    if s['type']=='restoration':s['parameters']['timesteps']=steps
 def show_settings(self):
  dialog=QDialog(self);dialog.setWindowTitle(txt('Vocal X Einstellungen','Vocal X Settings'));form=QFormLayout(dialog)
  license_button=QPushButton(txt('Lizenz / Aktivierung','License / Activation'));license_button.clicked.connect(self.show_license);form.addRow(license_button)
  output=QLineEdit(str(output_root(self.root)));browse=QPushButton('…');row=QHBoxLayout();row.addWidget(output);row.addWidget(browse);form.addRow(txt('Output-Ordner','Output folder'),row)
  def change_output():
   path=QFileDialog.getExistingDirectory(dialog,'Output',output.text())
   if path:output.setText(path);self.settings['output_dir']=path;self.settings['setup_complete']=True;self.save_settings();self.update_license_controls()
  browse.clicked.connect(change_output);output.setReadOnly(True)
  name=QLineEdit(self.settings['filename']);form.addRow(txt('Dateiname','Filename'),name)
  def set_name():
   value=name.text()
   if '{OriginalName}' not in value or Path(value).name!=value or not value.lower().endswith('.wav'):name.setText(self.settings['filename']);self.error(txt('Schema benötigt {OriginalName} und .wav, ohne Unterordner.','Pattern requires {OriginalName} and .wav, without subfolders.'));return
   self.settings['filename']=value;self.save_settings()
  name.editingFinished.connect(set_name)
  reset_name=QPushButton(txt('Dateinamen-Standard wiederherstellen','Restore default filename'));reset_name.clicked.connect(lambda:(name.setText(DEFAULTS['filename']),set_name()));form.addRow(reset_name)
  for key,de,en in [('notify','Windows-Benachrichtigung','Windows notification'),('sound','Fertig-Sound','Completion sound'),('open_after','Ergebnisordner automatisch öffnen','Open output folder automatically')]:
   box=QCheckBox(txt(de,en));box.setChecked(self.settings[key]);box.toggled.connect(lambda value,k=key:(self.settings.update({k:value}),self.save_settings()));form.addRow(box)
  after=QComboBox()
  for label,value in [(txt('Nichts tun','Do nothing'),'nothing'),(txt('Vocal X schließen','Close Vocal X'),'close'),(txt('Standby (Bestätigung erforderlich)','Sleep (confirmation required)'),'sleep'),(txt('Herunterfahren (Bestätigung erforderlich)','Shutdown (confirmation required)'),'shutdown')]:after.addItem(label,value)
  after.setCurrentIndex(after.findData(self.settings['after']));after.currentIndexChanged.connect(lambda:(self.settings.update(after=after.currentData()),self.save_settings()));form.addRow(txt('Nach Abschluss','On completion'),after)
  performance=QComboBox();performance.addItems(['Eco','Balanced','Maximum']);performance.setCurrentText(self.settings['performance']);performance.currentTextChanged.connect(lambda value:(self.settings.update(performance=value),self.save_settings()));form.addRow(txt('KI-Rekonstruktion','AI reconstruction'),performance)
  form.addRow(QLabel(txt('Eco: 8 Schritte · Balanced: Preset-Wert · Maximum: 32 Schritte. Mehr Schritte brauchen mehr Zeit; Qualität ist nicht garantiert.','Eco: 8 steps · Balanced: preset value · Maximum: 32 steps. More steps take longer; quality is not guaranteed.')))
  theme=QComboBox();theme.addItems(['Vocal X Dark','Light']);theme.setCurrentIndex(self.settings['theme']=='light')
  def set_theme():
   self.settings['theme']='light' if theme.currentIndex() else 'dark';self.save_settings();self.apply_theme()
  theme.currentIndexChanged.connect(set_theme);form.addRow(txt('Design','Theme'),theme)
  row=QHBoxLayout();export=QPushButton(txt('Exportieren','Export'));imp=QPushButton(txt('Importieren','Import'));reset=QPushButton(txt('Benachrichtigungen zurücksetzen','Reset notifications'));row.addWidget(export);row.addWidget(imp);row.addWidget(reset);form.addRow(row)
  def export_settings():
   path,_=QFileDialog.getSaveFileName(dialog,'Vocal X','','Vocal X Settings (*.vxsettings)')
   if path:base.atomic_json(Path(path),self.settings)
  def import_settings():
   path,_=QFileDialog.getOpenFileName(dialog,'Vocal X','','Vocal X Settings (*.vxsettings)')
   if not path:return
   try:
    values=json.loads(Path(path).read_text());self.settings.update({k:v for k,v in values.items() if k in DEFAULTS and type(v)==type(DEFAULTS[k]) and k not in ('setup_complete','after')});self.settings['after']='nothing'
    if self.settings['performance'] not in ('Eco','Balanced','Maximum'):self.settings['performance']='Balanced'
    if self.settings['theme'] not in ('dark','light'):self.settings['theme']='dark'
    self.save_settings();self.apply_theme();dialog.accept();self.show_settings()
   except Exception as e:self.error(e)
  export.clicked.connect(export_settings);imp.clicked.connect(import_settings);reset.clicked.connect(lambda:(self.settings.update(notify=True,sound=False,open_after=False),self.save_settings(),dialog.accept()))
  form.addRow(QLabel(self.gpu_label.text()));close=QDialogButtonBox(QDialogButtonBox.StandardButton.Close);close.rejected.connect(dialog.reject);form.addRow(close);dialog.exec()
 def apply_theme(self):
  QApplication.instance().setStyleSheet(base.STYLE if self.settings['theme']=='dark' else base.STYLE.replace('#11151e','#f2f5f3').replace('#e5eaf4','#15251d').replace('#171e2b','#ffffff').replace('#202a3b','#e1e9e4').replace('#263248','#dce7e0').replace('#202b3c','#d8e5dd'))
  QApplication.instance().setStyleSheet(QApplication.instance().styleSheet()+' QWidget#branding {background:#11151e;} QWidget#branding QLabel {background:transparent;color:#e5eaf4;}')
 def closeEvent(self,event):
  if self.active:
   if QMessageBox.question(self,'Vocal X',txt('Laufenden Schritt abbrechen und schließen?','Cancel the current stage and close?'))!=QMessageBox.StandardButton.Yes:event.ignore();return
   self.auto=False;self.cancelled=True
   if self.process:self.process.kill();self.process.waitForFinished(5000)
  self.settings['session_open']=False;self.save_session();self.audition.shutdown();self.tray.hide();self.taskbar.close();self.gpu_query.kill();self.gpu_query.waitForFinished(1000);event.accept()
