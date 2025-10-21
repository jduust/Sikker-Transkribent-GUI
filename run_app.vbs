' Get the folder where this script lives
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Create WshShell object
Set WshShell = CreateObject("WScript.Shell")

' Build full command to run pythonw.exe from the virtual environment
cmd = """" & scriptDir & "\.venv\Scripts\pythonw.exe"" """ & scriptDir & "\app.py"""

' Run the command hidden (0 = hidden window), do not wait (False)
WshShell.Run cmd, 0, False
