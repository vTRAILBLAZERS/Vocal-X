Set shell = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
root = fs.GetParentFolderName(fs.GetParentFolderName(WScript.ScriptFullName))
args = ""
For Each arg In WScript.Arguments
 args = args & " " & Chr(34) & arg & Chr(34)
Next
shell.Run Chr(34) & root & "\Vocal X.exe" & Chr(34) & args, 0, False
