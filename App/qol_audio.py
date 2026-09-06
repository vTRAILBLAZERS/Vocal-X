from vocal_pipeline.paths import data_root
"""Local audition, waveform selection and bounded RMS level matching."""
import hashlib
from pathlib import Path
import numpy as np,soundfile as sf
from PySide6.QtCore import Qt,QUrl,Signal,QThread
from PySide6.QtGui import QPainter,QColor,QPen
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QCheckBox,QSlider,QDoubleSpinBox,QLabel
from PySide6.QtMultimedia import QMediaPlayer,QAudioOutput
import gui_i18n

def txt(de,en):return en if gui_i18n.LANG=='en' else de
class Waveform(QWidget):
 region=Signal(float,float);seek=Signal(float)
 def __init__(self):
  super().__init__();self.setMinimumHeight(62);self.points=[];self.duration=0;self.start=0;self.end=20;self.press=None;self.cursor=0
 def paintEvent(self,e):
  p=QPainter(self);p.fillRect(self.rect(),QColor('#171e2b'));w=self.width();h=self.height()
  if self.duration:
   p.fillRect(int(self.start/self.duration*w),0,max(1,int((self.end-self.start)/self.duration*w)),h,QColor('#24513d'))
  p.setPen(QPen(QColor('#46db87'),1))
  for i,v in enumerate(self.points):
   x=i*w/max(1,len(self.points));p.drawLine(int(x),int(h/2-v*h*.45),int(x),int(h/2+v*h*.45))
  if self.duration:p.setPen(QColor('white'));p.drawLine(int(self.cursor/self.duration*w),0,int(self.cursor/self.duration*w),h)
 def mousePressEvent(self,e):self.press=e.position().x()
 def mouseReleaseEvent(self,e):
  if not self.duration or self.press is None:return
  a=self.press/self.width()*self.duration;b=e.position().x()/self.width()*self.duration
  if abs(e.position().x()-self.press)<5:self.seek.emit(max(0,min(self.duration,b)))
  else:self.start=max(0,min(a,b));self.end=min(self.duration,max(a,b));self.region.emit(self.start,self.end);self.update()

class AudioPrepare(QThread):
 done=Signal(object);failed=Signal(str)
 def __init__(self,source,result,cache,token):super().__init__();self.source=source;self.result=result;self.cache=cache;self.token=token
 def run(self):
  try:
   paths=[self.source,self.result if self.result and Path(self.result).is_file() else self.source];stats=[];points=[];duration=0
   for index,path in enumerate(paths):
    total=0.;count=0;peak=0.;wave=[]
    with sf.SoundFile(path) as f:
     if index==0:duration=len(f)/f.samplerate
     for block in f.blocks(blocksize=max(4096,len(f)//1500),dtype='float32',always_2d=True):
      total+=float(np.sum(block.astype('float64')**2));count+=block.size;peak=max(peak,float(np.abs(block).max()));wave.append(float(np.abs(block).max()))
    stats.append((max(1e-12,(total/max(1,count))**.5),max(1e-12,peak)))
    if index==0:points=np.asarray(wave);points=(points/max(1e-8,points.max())).tolist()
   target=min(s[0]/max(1,s[1]/.95) for s in stats);matched=[]
   for index,path in enumerate(paths):
    key=hashlib.sha256((str(path)+str(Path(path).stat().st_mtime_ns)+str(target)).encode()).hexdigest()[:20];out=self.cache/(key+'.wav');self.cache.mkdir(parents=True,exist_ok=True)
    if not out.exists():
     with sf.SoundFile(path) as inp,sf.SoundFile(out,'w',samplerate=inp.samplerate,channels=inp.channels,subtype='PCM_16') as dest:
      for block in inp.blocks(blocksize=65536,dtype='float32',always_2d=True):dest.write(block*(target/stats[index][0]))
    matched.append(str(out))
   self.done.emit({'token':self.token,'raw':list(map(str,paths)),'matched':matched,'points':points,'duration':duration,'has_result':paths[0]!=paths[1]})
  except Exception as e:self.failed.emit(str(e))

class Audition(QWidget):
 preview=Signal(float,float)
 def __init__(self,root):
  super().__init__();self.root=Path(root);self.data=None;self.workers=[];self.token=0;self.side=0
  self.audio=QAudioOutput(self);self.player=QMediaPlayer(self);self.player.setAudioOutput(self.audio);self.audio.setVolume(.7)
  layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0)
  self.wave=Waveform();layout.addWidget(self.wave)
  row=QHBoxLayout();self.original=QPushButton('Original');self.result=QPushButton('Vocal X');self.play=QPushButton('▶ / Ⅱ');self.swap=QPushButton('A/B');self.loop=QCheckBox('Loop');self.match=QCheckBox('RMS');self.match.setChecked(True)
  self.volume=QSlider(Qt.Orientation.Horizontal);self.volume.setRange(0,100);self.volume.setValue(70);self.volume.setMaximumWidth(100)
  for widget in [self.original,self.result,self.play,self.swap,self.loop,self.match,self.volume]:row.addWidget(widget)
  layout.addLayout(row);range_row=QHBoxLayout();self.start=QDoubleSpinBox();self.start.setSuffix(' s');self.start.setMaximum(999999);self.length=QDoubleSpinBox();self.length.setRange(1,60);self.length.setValue(20);self.length.setSuffix(' s')
  self.render=QPushButton();self.auto=QPushButton();range_row.addWidget(self.start);range_row.addWidget(self.length);range_row.addWidget(self.auto);range_row.addWidget(self.render);layout.addLayout(range_row)
  self.note=QLabel();self.note.setWordWrap(True);layout.addWidget(self.note)
  self.original.clicked.connect(lambda:self.choose(0));self.result.clicked.connect(lambda:self.choose(1));self.swap.clicked.connect(lambda:self.choose(1-self.side));self.play.clicked.connect(self.toggle)
  self.volume.valueChanged.connect(lambda n:self.audio.setVolume(n/100));self.match.toggled.connect(lambda:self.choose(self.side));self.render.clicked.connect(lambda:self.preview.emit(self.start.value(),self.length.value()));self.auto.clicked.connect(self.auto_region)
  self.wave.seek.connect(lambda sec:self.player.setPosition(int(sec*1000)));self.wave.region.connect(self.region);self.start.valueChanged.connect(self.update_region);self.length.valueChanged.connect(self.update_region)
  self.player.positionChanged.connect(self.position);self.player.mediaStatusChanged.connect(self.media_status);self.player.errorOccurred.connect(lambda *args:self.note.setText(self.player.errorString()));self.retranslate()
 def retranslate(self):
  self.render.setText(txt('Vorschau rendern','Render preview'));self.auto.setText(txt('Aktive Stelle','Active section'));self.match.setToolTip(txt('RMS-Lautstärkeabgleich nur für die Wiedergabe','RMS level matching for playback only'));self.start.setToolTip(txt('Start der Vorschau in Sekunden','Preview start in seconds'));self.length.setToolTip(txt('Vorschaulänge, maximal 60 Sekunden','Preview length, maximum 60 seconds'));self.note.setText(txt('WAV auswählen. Ziehen markiert einen Bereich; Klicken spult.','Select WAV. Drag to select a region; click to seek.'))
 def load(self,source,result=None,autoplay=False):
  self.autoplay=autoplay
  self.player.stop();self.token+=1;self.data=None;self.result.setEnabled(False);self.note.setText(txt('Audio wird vorbereitet …','Preparing audio …'))
  worker=AudioPrepare(source,result,data_root(self.root)/'Cache/Audition',self.token);self.workers.append(worker)
  worker.done.connect(self.ready);worker.failed.connect(self.note.setText);worker.finished.connect(lambda:self.workers.remove(worker) if worker in self.workers else None);worker.start()
 def ready(self,data):
  if data['token']!=self.token:return
  self.data=data;self.wave.points=data['points'];self.wave.duration=data['duration'];self.start.setMaximum(max(0,data['duration']-1));self.result.setEnabled(data['has_result']);self.side=0;self.choose(0);self.update_region();self.note.setText(txt('Abgleich nur für Wiedergabe. Originaldateien bleiben unverändert.','Matching affects playback only. Original files are unchanged.'))
 def choose(self,side):
  if not self.data:return
  if side and not self.data['has_result']:return
  pos=self.player.position();playing=self.player.playbackState()==QMediaPlayer.PlaybackState.PlayingState;self.side=side
  self.pending_position=pos;self.pending_play=playing or getattr(self,"autoplay",False);self.autoplay=False
  self.player.setSource(QUrl.fromLocalFile(self.data['matched' if self.match.isChecked() else 'raw'][side]))
  self.original.setStyleSheet('color:#46db87' if side==0 else '');self.result.setStyleSheet('color:#46db87' if side else '')
 def media_status(self,status):
  if status==QMediaPlayer.MediaStatus.LoadedMedia:
   self.player.setPosition(getattr(self,'pending_position',0))
   if getattr(self,'pending_play',False):self.player.play()
  if status==QMediaPlayer.MediaStatus.EndOfMedia and self.loop.isChecked():self.player.setPosition(int(self.start.value()*1000));self.player.play()
 def toggle(self):
  if self.player.playbackState()==QMediaPlayer.PlaybackState.PlayingState:self.player.pause()
  else:self.player.play()
 def position(self,pos):
  self.wave.cursor=pos/1000;self.wave.update()
  if self.loop.isChecked() and pos/1000>=self.wave.end and self.wave.end>self.wave.start:self.player.setPosition(int(self.wave.start*1000))
 def region(self,a,b):self.start.setValue(a);self.length.setValue(min(60,b-a))
 def update_region(self):self.wave.start=self.start.value();self.wave.end=min(self.wave.duration,self.start.value()+self.length.value());self.wave.update()
 def auto_region(self):
  if self.data:
   values=np.asarray(self.data['points']);width=max(1,int(self.length.value()/max(1,self.data['duration'])*len(values)));energy=np.convolve(values**2,np.ones(min(width,len(values))),mode='valid');self.start.setValue(float(np.argmax(energy))/len(values)*self.data['duration']);self.note.setText(txt('Energiereichster Bereich; keine automatische Gesangserkennung.','Highest-energy section; not automatic vocal detection.'))
 def shutdown(self):
  self.token+=1;self.data=None;self.player.stop();self.player.setSource(QUrl())
  for worker in list(self.workers):worker.wait()
