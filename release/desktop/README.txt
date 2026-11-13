PETROLUMEN DESKTOP
==================

SYSTEM REQUIREMENTS
- Windows 10 or later (64-bit)
- Microsoft Edge WebView2 Evergreen Runtime
- Microsoft .NET Framework 4.8
- No separate Python or Node.js installation is required

If WebView2 is missing, install it from:
https://developer.microsoft.com/microsoft-edge/webview2/

If .NET Framework is unavailable, install .NET Framework 4.8 from:
https://dotnet.microsoft.com/download/dotnet-framework/net48

RUNNING THE APP
1. Extract the complete PetroLumen folder from the release.
2. Keep all files and subfolders together.
3. Run PetroLumen.exe. Do not run it from inside an archive or move the
   executable by itself.

DATA STORAGE AND RESET
The database, authentication secret, WebView profile, and logs are stored in a
writable user-data directory. PetroLumen tries these locations in order:
1. %LOCALAPPDATA%\PetroLumen
2. %APPDATA%\PetroLumen
3. A data folder next to PetroLumen.exe
4. A temporary application data directory

To reset, close PetroLumen and rename or remove the active PetroLumen data
directory. A fresh database and secret are created on the next launch. This
removes local accounts and saved data. Do not remove the installation folder
when resetting user data.

LOGS AND TROUBLESHOOTING
Logs are in logs\petrolumen.log inside the active data directory. The log
rotates at 1 MB and retains up to three older files. If a data directory or
desktop prerequisite cannot be initialized, PetroLumen displays a diagnostic
dialog.

ANTIVIRUS
PyInstaller executables can occasionally trigger antivirus warnings. Verify
that the download came from the official release source and follow your
organization's software approval process. Do not disable antivirus protection
globally.
