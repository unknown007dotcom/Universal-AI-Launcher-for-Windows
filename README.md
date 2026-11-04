# AI HUB

A lightweight Windows-first desktop launcher for AI websites and locally installed AI clients. Uses Python's standard-library Tkinter UI (no embedded browser, runtime download, or API key). Configuration is stored outside the executable in `%APPDATA%\AIHub\config.json` on Windows.

## Build Windows executable

On Windows 10/11 x64 install Python 3.11 (enable the Python launcher), then run `build_windows.bat`. Output: `dist\AIHub.exe`. It is a one-file, windowed PyInstaller build. Alternatively, push to GitHub or run **Actions → Build AI HUB for Windows → Run workflow**; download artifact `AIHub-Windows-x64` from a successful run. The workflow also saves a build-warning log artifact. This checkout environment is Linux, so a genuine Windows binary cannot be built locally here.

## Run from source

Python 3.10+ with Tk/Tcl installed: `python main.py`. Runtime has no third-party package requirements.

## How launch works

APP FIRST (default): opens a verified detected app, otherwise official website. WEB FIRST always opens the site. ASK EVERY TIME prompts when an app is verified. A user-specified executable is validated for existence; on Windows automatic detection requires an exact product display-name match in installed-product registry metadata or an exact product-named Start Menu shortcut; publisher metadata is only a consistency check, never the identity by itself. This prevents Google Drive from being mistaken for Gemini. Unknown/unverified clients are not guessed: the platform remains WEB ONLY. If a configured path is invalid it reports DETECTION REQUIRED. If app launch fails, the user can choose website fallback. Websites are opened via the default browser, and only one target is launched.

Use each card's ⋯ menu to edit, reorder, or delete. Add AI accepts a display name, http(s) URL, optional icon/category, executable path and publisher. Favorites and recent/history records persist. Search filters names and categories. Settings includes launch behavior and JSON import/export/default restore. Synaptics instructions are in Settings.

## Touchpad and single instance

Configure Synaptics Control Panel → Advanced → Tap Zones → Top Right → Run… and choose `AIHub.exe`. Repeated launches are guarded by a named Windows mutex; the existing process is retained. The existing window can be brought forward when its own instance is activated; Windows' mutex does not provide cross-process window activation by itself, so a second process exits rather than stealing focus. Configure Synaptics to launch the existing executable.

## Tests and limitations

Run `python -m unittest discover -s tests -v` for portable unit tests. Linux sandbox can exercise config, validation, launch fallback (mocked browser), and UI module import. Registry, Windows shell launching, mutex behavior, GUI interaction on a real desktop, and packaged executable runtime must be verified on Windows. Automatic desktop detection deliberately errs toward website fallback; Store packaging/protocols and app-specific undocumented locations are not guessed. Windows build is automated in GitHub Actions; no Windows executable is attached to this Linux checkout until that workflow is run.
