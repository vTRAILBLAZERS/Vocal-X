"""Developer-only Windows DPAPI wrapper. Never ship this admin module."""
import ctypes
from ctypes import wintypes
class Blob(ctypes.Structure):_fields_=[('length',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]
def transform(data,protect):
 buffer=ctypes.create_string_buffer(data);source=Blob(len(data),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte)));out=Blob()
 dll=ctypes.WinDLL('crypt32',use_last_error=True);kernel=ctypes.WinDLL('kernel32',use_last_error=True)
 kernel.LocalFree.argtypes=[ctypes.c_void_p];kernel.LocalFree.restype=ctypes.c_void_p
 if protect:
  fn=dll.CryptProtectData;fn.argtypes=[ctypes.POINTER(Blob),wintypes.LPCWSTR,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
  ok=fn(ctypes.byref(source),'Vocal X signing key',None,None,None,1,ctypes.byref(out))
 else:
  fn=dll.CryptUnprotectData;fn.argtypes=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
  ok=fn(ctypes.byref(source),None,None,None,None,1,ctypes.byref(out))
 if not ok:raise ctypes.WinError(ctypes.get_last_error())
 try:return ctypes.string_at(out.data,out.length)
 finally:kernel.LocalFree(out.data)
