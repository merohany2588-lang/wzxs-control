Ultimate C Drive Strike - ASCII Safe Version

Why this exists:
- Your previous PowerShell package broke because Chinese text inside the script was corrupted.
- This version uses ASCII-only strings in the .ps1 file to avoid parser failures caused by broken encoding.

Files:
1. ultimate_c_drive_strike_ascii_safe.ps1
2. run_ultimate_c_drive_strike_ascii_safe.cmd
3. README.txt

How to use:
1. Extract the zip.
2. Right click run_ultimate_c_drive_strike_ascii_safe.cmd
3. Choose "Run as administrator"
4. Use menu option 8 for the full sequence

Notes:
- This version does not rely on Python.
- It does not directly delete WinSxS, System32, or pagefile.sys.
- It opens Windows system dialogs for virtual memory and uninstall center when needed.
