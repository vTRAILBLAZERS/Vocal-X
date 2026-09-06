"""Optional Windows shell integration. Failure never blocks audio work."""
import ctypes,uuid
class GUID(ctypes.Structure):
 _fields_=[('data',ctypes.c_ubyte*16)]
 def __init__(self,text):super().__init__((ctypes.c_ubyte*16).from_buffer_copy(uuid.UUID(text).bytes_le))
class Taskbar:
 def __init__(self,window):
  self.window=window;self.ptr=ctypes.c_void_p();self.available=False;self.com_init=False
  try:
   ole=ctypes.windll.ole32;self.com_init=ole.CoInitialize(None) in (0,1)
   cls=GUID('56FDF344-FD6D-11d0-958A-006097C9A090');iid=GUID('EA1AFB91-9E28-4B86-90E9-9E9F8A5EEFAF')
   hr=ole.CoCreateInstance(ctypes.byref(cls),None,1,ctypes.byref(iid),ctypes.byref(self.ptr))
   if hr==0:self.call(3,[],[]);self.available=True
  except Exception:pass
 def call(self,index,args,values):
  table=ctypes.cast(self.ptr,ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
  fn=ctypes.WINFUNCTYPE(ctypes.c_long,ctypes.c_void_p,*args)(table[index]);return fn(self.ptr,*values)
 def update(self,done,total,active=False):
  if not self.available:return
  try:
   hwnd=ctypes.c_void_p(int(self.window.winId()));self.call(10,[ctypes.c_void_p,ctypes.c_int],[hwnd,2 if active and total else 0])
   if total:self.call(9,[ctypes.c_void_p,ctypes.c_ulonglong,ctypes.c_ulonglong],[hwnd,int(done),int(total)])
  except Exception:self.available=False
 def close(self):
  if self.available:self.update(0,0);self.call(2,[],[]);self.available=False
  if self.com_init:ctypes.windll.ole32.CoUninitialize();self.com_init=False
