#!/bin/bash
#Installer für Linux, Terminal, cd bis zum installer, dann ausführen:
#bash ./install.sh


set -e  # Skript abbrechen, falls n Befehl fehlschlaegt

INSTALLER_ORDNER="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_BEFEHL="python3.14"

if ! command -v "$PYTHON_BEFEHL" &> /dev/null; then
    echo "FEHLER: Python 3.14 wurde nicht gefunden (Befehl '$PYTHON_BEFEHL' existiert nicht)."
    echo "Bitte zuerst installieren, z.B. mit: sudo dnf install python3.14"
    exit 1
fi

echo "Gefundene Python-Version: $("$PYTHON_BEFEHL" --version)"

"$PYTHON_BEFEHL" "$INSTALLER_ORDNER/install.py"
