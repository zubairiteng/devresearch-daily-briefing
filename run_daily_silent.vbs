Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "c:\Users\DELL\Desktop\automation\daily news"
WshShell.Run "python run_pipeline.py", 0, False
