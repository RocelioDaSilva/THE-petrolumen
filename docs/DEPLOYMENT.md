# PetroLumen Desktop Deployment

## System requirements

- Windows 10 or later (64-bit).
- Microsoft Edge WebView2 Evergreen Runtime.
- Microsoft .NET Framework 4.8.
- The app does not require a separate Python or Node.js installation.

If WebView2 is missing, install it from [Microsoft's WebView2 page](https://developer.microsoft.com/microsoft-edge/webview2/).
If the .NET desktop runtime is unavailable, install [.NET Framework 4.8](https://dotnet.microsoft.com/download/dotnet-framework/net48).

## Install and run

Download and extract the complete `PetroLumen` folder from the desktop release. Keep its files and subfolders together, then run `PetroLumen.exe`. Do not run the executable from inside an archive or move it by itself.

## Data and reset

The app stores its SQLite database, authentication secret, WebView profile, and logs in a writable user-data directory. It tries these locations in order:

1. `%LOCALAPPDATA%\PetroLumen`
2. `%APPDATA%\PetroLumen`
3. A `data` folder next to `PetroLumen.exe` (portable fallback)
4. A temporary application data directory if the preceding locations are unavailable

To reset the app, close it and rename or remove the active `PetroLumen` data directory. The app creates a fresh database and secret on its next launch; resetting removes local accounts and saved data. Do not remove the installation folder when resetting user data.

## Logs and troubleshooting

Application logs are written to `logs\petrolumen.log` inside the active data directory. The log rotates at 1 MB and retains up to three older files. If the app cannot initialize its data directory or load a desktop prerequisite, it displays a diagnostic dialog instead.

PyInstaller-packaged executables can occasionally trigger antivirus warnings. Verify that the download came from the official release source and follow your organization's software approval process; do not disable antivirus protection globally.

For development builds, see the repository's `build_exe.ps1` script and `frontend_desktop\requirements_packaging.txt`.
