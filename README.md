# Scratch-Wound-Visualizer
A Python Programm to quickly analyze the growth of cells 

Der Segmentierungsansatz folgt Suarez-Arnedo A, Torres Figueroa F, Clavijo C, Arbeláez P, Cruz JC, Muñoz-Camargo C (2020): 

An image J plugin for the high throughput image analysis of in vitro scratch wound healing assays. PLoS ONE 15(7): e0232565. doi:10.1371/journal.pone.0232565. Unabhängige Neuimplementierung und Verbesserung in Python, kein Code des Originals übernommen.

Das Installerskript legt eine eigene virtuelle Umgebung an, installiert alle Pakete aus `requirements.txt` und richtet ein Icon im Anwendungsmenü und auf dem Desktop ein. Danach einfach das Icon **"Scratch Wound Visualizer"** anklicken.




## Installation für Linux (Fedora bzw. Red Hat / Ubuntu bzw. Debian)

Voraussetzung: Python 3.14, im Terminal eingeben:

```bash
git clone https://github.com/SimonBic/Scratch-Wound-Visualizer.git
cd Scratch-Wound-Visualizer/src/installer
./install.sh
```

Läuft ab Ubuntu 22.04, Debian 12, Fedora 35 bzw. RHEL 9. Auf älteren Versionen gibts PySide6 (die Bibliothek für die Oberfläche) nicht mehr, da bricht der Installer ab.

Falls die App unter X11 (also nicht Wayland) nicht startet und irgendwas mit "xcb" meldet, fehlt eine Systembibliothek: `sudo apt install libxcb-cursor0` (Ubuntu/Debian) bzw. `sudo dnf install xcb-util-cursor` (Fedora).


## Installation für Windows und macOS

Die Pakete in der `requirements.txt` gibt es alle für Windows (normale 64-Bit PCs und ARM Laptops) und für macOS, sowohl für Intel Macs als auch für Apple Silicon (M1, M2, ...). Ich hab die Versionen extra festgelegt, auch die Pakete, die automatisch mitinstalliert werden, damit überall genau das gleiche läuft wie bei mir.

**Wichtig für Mac:** Die App braucht mindestens **macOS 13 (Ventura)**. Das liegt an PySide6 (das ist die Bibliothek für die Oberfläche), die Versionen, die mit Python 3.14 laufen, gibts erst ab macOS 13. Auf älteren Macs bricht der Installer beim Pakete installieren mit einer Fehlermeldung ab. Welche macOS Version man hat, sieht man oben links unter Apple → "Über diesen Mac".

Falls jemand die Installation auf Windows oder MacOS testen kann, dann wäre ich dankbar für eine kurze Rückmeldung in Form eines pull requests oder Issue über etwaige Fehlercodes oder über eine erfolgreiche Installation.

### Schritt 1: Programm herunterladen

Auf GitHub oben rechts auf den grünen Button **"Code"** klicken, dann **"Download ZIP"**. Die Datei irgendwo, in einen leeren Ordner entpacken (Rechtsklick → "Alle extrahieren" unter Windows, Doppelklick unter macOS).

### Schritt 2: Python installieren (falls noch nicht vorhanden)

Das Programm braucht **Python 3.14**. Falls unsicher: einfach Schritt 3 versuchen, falls Python fehlt, meldet sich der Installer mit einer Fehlermeldung.

Python-Download unter [python.org/downloads](https://www.python.org/downloads/). **Wichtig unter Windows:** beim Installieren unten den Haken bei **"Add python.exe to PATH"** setzen.

### Schritt 3: Installation starten

#### Unter Windows

1. Im entpackten Ordner in eine leere Fläche **Umschalt-Taste gedrückt halten und gleichzeitig rechtsklicken**
2. **"PowerShell-Fenster hier öffnen"** auswählen
3. Eintippen und Enter drücken: `python src\installer\install.py`
4. Kurz warten, am Ende steht "Installation abgeschlossen"

Danach liegt ein **Symbol "Scratch Wound Visualizer"** auf dem Desktop und im Startmenü, doppelklicken zum Starten.

#### Unter macOS

1. **Terminal** öffnen: `Cmd + Leertaste`, "Terminal" eintippen, Enter
2. `cd ` eintippen (mit Leerzeichen, ohne Enter), dann den entpackten Ordner per Maus ins Terminal ziehen, Enter drücken
3. Eintippen und Enter drücken: `python3 src/installer/install.py`
4. Kurz warten, am Ende steht "Installation abgeschlossen"

Danach liegt ein Symbol "Scratch Wound Visualizer" auf dem Schreibtisch. Beim ersten Doppelklick meldet macOS eventuell "kann nicht geöffnet werden", dann stattdessen Rechtsklick → Öffnen (nur beim ersten Mal nötig, MacOS vertraut externen Codern, wie mir, erstmal grundsätzlich nicht).


## Ergebnisse der App

**Einzelner Versuch:** Neben dem Ordner mit den Bildern wird ein Ordner `<ordner>_marked` angelegt, da drin:

- `<bild>_duenn.tif` und `<bild>_dick.tif`: jedes Bild mit eingezeichneter Wundgrenze, einmal dünn, einmal dick. Die breiteste und schmalste Stelle des Spalts sind als weiße Linie eingezeichnet und mit "Max. distance" bzw. "Min. distance" beschriftet.
- `_alle_zeitpunkte_duenn.tif` / `_dick.tif`: alle Wundgrenzen übereinander auf dem letzten Bild.
- `_heatmap.tif`: Zellrasen zum ersten Zeitpunkt rot, was danach zuwächst gelb, grün, blau usw., mit 40 % Deckkraft über dem letzten Bild.
- `<versuch>_auswertung.xlsx`: Abstand der Wundränder (Mittelwert, Max), Fläche und Fläche in % vom ersten Zeitpunkt, plus Graph.

**Ordner mit mehreren Versuchen:** Pro Versuch das gleiche `_marked`-Ordner-Zeug wie oben, aber nur **eine** Excel für alle Versuche direkt im gewählten Ordner: jeder Versuch untereinander mit Graph, ganz unten der Durchschnitt mit Standardabweichung. Dazu `<ordner>_gesamt_heatmap.png`: alle Heatmaps an der Spaltmitte ausgerichtet übereinandergelegt und gemittelt.

Alle Werte sind in Pixeln. Gemessen wird nur da, wo im ersten Bild eine Wunde erkannt wurde, dunkle Ränder vom Mikroskop oder Linien quer durch den Spalt fliegen dadurch raus.

Wenn man einen Ordner nochmal auswertet, werden die alten Ergebnisse überschrieben. Die Excel vorher schließen, sonst kann sie (vor allem unter Windows) nicht überschrieben werden.
