
# Plattformuebergreifender Installer (Windows/macOS/Linux), erstellt eine
# .venv, installiert die Pakete aus requirements.txt und richtet ein
# Programm-Icon zum Anklicken ein:
#   Windows: Verknuepfung auf dem Desktop und im Startmenue
#   macOS:   .app-Bundle auf dem Schreibtisch
#   Linux:   .desktop-Eintrag im Anwendungsmenue und auf dem Desktop 


# Aufruf:
#     Windows: python src\installer\install.py
#     macOS:   python3 src/installer/install.py
#     Linux:   bash src/installer/install.sh 

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

APP_NAME = "Scratch Wound Visualizer"
APP_ID = "scratch-wound-visualizer"
PYTHON_VERSION = "3.14"

INSTALLER_ORDNER = Path(__file__).resolve().parent
REPO_ORDNER = INSTALLER_ORDNER.parent.parent
APP_ORDNER = REPO_ORDNER / "src"
MAIN_PY_PFAD = APP_ORDNER / "main.py"
LOGO_SVG_PFAD = REPO_ORDNER / "assets" / "logo.svg"
VENV_PFAD = REPO_ORDNER / ".venv"
REQUIREMENTS_PFAD = REPO_ORDNER / "requirements.txt"

SYSTEM = platform.system()

if SYSTEM == "Windows":
    VENV_PYTHON = VENV_PFAD / "Scripts" / "python.exe"
    # pythonw startet ohne schwarzes Konsolenfenster im Hintergrund
    VENV_PYTHON_GUI = VENV_PFAD / "Scripts" / "pythonw.exe"
else:
    VENV_PYTHON = VENV_PFAD / "bin" / "python"
    VENV_PYTHON_GUI = VENV_PYTHON


def fehler(text: str) -> None:
    print(f"FEHLER: {text}")
    sys.exit(1)


def python_befehl() -> list:
    # Laeuft install.py schon mit der richtigen Version, direkt diese nehmen
    if f"{sys.version_info.major}.{sys.version_info.minor}" == PYTHON_VERSION:
        return [sys.executable]

    if SYSTEM == "Windows":
        try:
            ergebnis = subprocess.run(["py", f"-{PYTHON_VERSION}", "--version"], capture_output=True, text=True)
            if ergebnis.returncode == 0 and PYTHON_VERSION in ergebnis.stdout:
                return ["py", f"-{PYTHON_VERSION}"]
        except FileNotFoundError:
            pass
        fehler(
            f"Python {PYTHON_VERSION} wurde nicht gefunden. Bitte von https://www.python.org/downloads/ "
            "installieren (Haken bei 'Add python.exe to PATH' nicht vergessen)."
        )

    kandidat = shutil.which(f"python{PYTHON_VERSION}")
    if kandidat:
        return [kandidat]

    hinweise = {
        "Darwin": f"Auf macOS z.B. mit: brew install python@{PYTHON_VERSION}",
        "Linux": f"Auf Fedora z.B. mit: sudo dnf install python{PYTHON_VERSION}",
    }
    fehler(f"Python {PYTHON_VERSION} wurde nicht gefunden. " + hinweise.get(SYSTEM, ""))


def venv_sicherstellen() -> None:
    befehl = python_befehl()

    if VENV_PFAD.exists():
        try:
            ergebnis = subprocess.run([str(VENV_PYTHON), "--version"], capture_output=True, text=True)
            if f"Python {PYTHON_VERSION}." in ergebnis.stdout:
                print(f"Bestehende virtuelle Umgebung passt bereits ({ergebnis.stdout.strip()}).")
                return
        except FileNotFoundError:
            pass
        print("Bestehende virtuelle Umgebung passt nicht, wird neu angelegt...")
        shutil.rmtree(VENV_PFAD)

    print(f"Erstelle virtuelle Umgebung unter {VENV_PFAD} ...")
    subprocess.run([*befehl, "-m", "venv", str(VENV_PFAD)], check=True)


def abhaengigkeiten_installieren() -> None:
    print("Installiere/prüfe Abhängigkeiten aus requirements.txt...")
    subprocess.run([str(VENV_PYTHON), "-m", "pip", "install", "--upgrade", "pip", "--quiet"], check=True)
    subprocess.run([str(VENV_PYTHON), "-m", "pip", "install", "-r", str(REQUIREMENTS_PFAD)], check=True)
    print("Abhängigkeiten erfolgreich installiert.")


def icon_erzeugen(modus: str, ziel: Path) -> None:
    # Laeuft ueber die VENV-Python (dort ist PySide6 installiert),
    # NICHT ueber die System-Python, die install.py selbst ausfuehrt
    subprocess.run(
        [str(VENV_PYTHON), str(INSTALLER_ORDNER / "icon_erzeugen.py"), modus, str(LOGO_SVG_PFAD), str(ziel)],
        check=True,
    )
    print(f"Icon erzeugt: {ziel}")


def windows_verknuepfung_einrichten() -> None:
    ico_pfad = INSTALLER_ORDNER / "logo.ico"
    icon_erzeugen("ico", ico_pfad)

    # GetFolderPath statt %USERPROFILE%\Desktop, weil OneDrive den
    # Desktop oft woanders hin umleitet
    ps_skript = f'''
        $WshShell = New-Object -comObject WScript.Shell

        $ZielPfade = @(
            (Join-Path ([Environment]::GetFolderPath("Desktop")) "{APP_NAME}.lnk"),
            (Join-Path ([Environment]::GetFolderPath("Programs")) "{APP_NAME}.lnk")
        )

        foreach ($Pfad in $ZielPfade) {{
            $Shortcut = $WshShell.CreateShortcut($Pfad)
            $Shortcut.TargetPath = "{VENV_PYTHON_GUI}"
            $Shortcut.Arguments = '"{MAIN_PY_PFAD}"'
            $Shortcut.WorkingDirectory = "{APP_ORDNER}"
            $Shortcut.IconLocation = "{ico_pfad}"
            $Shortcut.Save()
            Write-Host "Verknuepfung angelegt: $Pfad"
        }}
        '''

    ps_datei = INSTALLER_ORDNER / "_verknuepfung_erstellen.ps1"
    # Mit BOM, sonst liest PowerShell 5 Umlaute im Pfad (z.B. Benutzername) falsch
    ps_datei.write_text(ps_skript, encoding="utf-8-sig")

    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps_datei)],
            check=True,
        )
    finally:
        ps_datei.unlink()


def macos_app_bundle_einrichten() -> None:
    iconset_ordner = INSTALLER_ORDNER / "logo.iconset"
    icns_pfad = INSTALLER_ORDNER / "logo.icns"
    icon_erzeugen("iconset", iconset_ordner)
    subprocess.run(["iconutil", "-c", "icns", str(iconset_ordner), "-o", str(icns_pfad)], check=True)
    shutil.rmtree(iconset_ordner)

    app_pfad = Path.home() / "Desktop" / f"{APP_NAME}.app"
    (app_pfad / "Contents" / "MacOS").mkdir(parents=True, exist_ok=True)
    (app_pfad / "Contents" / "Resources").mkdir(parents=True, exist_ok=True)

    info_plist = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIconFile</key>
    <string>logo.icns</string>
    <key>CFBundleIdentifier</key>
    <string>de.ukr.scratchwoundvisualizer</string>
    <key>CFBundleName</key>
    <string>{APP_NAME}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
'''
    (app_pfad / "Contents" / "Info.plist").write_text(info_plist)
    shutil.copy(icns_pfad, app_pfad / "Contents" / "Resources" / "logo.icns")

    launcher_pfad = app_pfad / "Contents" / "MacOS" / "launcher"
    launcher_pfad.write_text(f'#!/bin/bash\ncd "{APP_ORDNER}"\nexec "{VENV_PYTHON}" "{MAIN_PY_PFAD}"\n')
    launcher_pfad.chmod(0o755)

    # Finder cached Icons - Bundle "anfassen", damit das neue Icon sofort erscheint
    os.utime(app_pfad)

    print(f"App-Bundle angelegt: {app_pfad}")
    print("Beim allerersten Start: Rechtsklick -> 'Öffnen', sonst blockiert Gatekeeper unsignierte Apps.")


def linux_desktop_datei_einrichten() -> None:
    # .desktop kann das SVG direkt als Icon verwenden
    desktop_inhalt = f"""[Desktop Entry]
Type=Application
Name={APP_NAME}
Comment=Analyse von Scratch-Wound-Assays
Exec="{VENV_PYTHON}" "{MAIN_PY_PFAD}"
Path={APP_ORDNER}
Icon={LOGO_SVG_PFAD}
Terminal=false
Categories=Science;Biology;
StartupWMClass={APP_ID}
"""

    applikationen_ordner = Path.home() / ".local" / "share" / "applications"
    applikationen_ordner.mkdir(parents=True, exist_ok=True)
    menue_datei = applikationen_ordner / f"{APP_ID}.desktop"
    menue_datei.write_text(desktop_inhalt)
    menue_datei.chmod(0o755)
    print(f"Im Anwendungsmenue installiert: {menue_datei}")

    # Desktop-Ordner heisst je nach Sprache anders (z.B. ~/Schreibtisch)
    desktop_ordner = Path.home() / "Desktop"
    if shutil.which("xdg-user-dir"):
        ergebnis = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True)
        if ergebnis.returncode == 0 and ergebnis.stdout.strip():
            desktop_ordner = Path(ergebnis.stdout.strip())

    if desktop_ordner.is_dir() and desktop_ordner != Path.home():
        desktop_datei = desktop_ordner / f"{APP_ID}.desktop"
        desktop_datei.write_text(desktop_inhalt)
        desktop_datei.chmod(0o755)

        
        if shutil.which("gio"):
            subprocess.run(
                ["gio", "set", str(desktop_datei), "metadata::trusted", "true"],
                capture_output=True,
            )
        print(f"Auf dem Desktop installiert: {desktop_datei}")

    if shutil.which("update-desktop-database"):
        subprocess.run(["update-desktop-database", str(applikationen_ordner)], capture_output=True)


if __name__ == "__main__":
    if not MAIN_PY_PFAD.exists():
        fehler(f"main.py wurde nicht gefunden unter {APP_ORDNER}")

    if not LOGO_SVG_PFAD.exists():
        fehler(f"logo.svg wurde nicht gefunden unter {LOGO_SVG_PFAD}")

    venv_sicherstellen()
    abhaengigkeiten_installieren()

    if SYSTEM == "Windows":
        windows_verknuepfung_einrichten()
    elif SYSTEM == "Darwin":
        macos_app_bundle_einrichten()
    else:
        linux_desktop_datei_einrichten()

    print(f"\nInstallation abgeschlossen. '{APP_NAME}' kann jetzt per Icon gestartet werden.")
