Set objShell = CreateObject("Wscript.Shell")
objShell.Run "powershell.exe -WindowStyle Hidden -NonInteractive -ExecutionPolicy Bypass -File ""C:\Users\favio\Desktop\TRADING\watchdog_monitor.ps1""", 0, False
