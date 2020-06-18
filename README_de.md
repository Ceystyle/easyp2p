# easyp2p

[English README](README.md)

## Überblick

easyp2p ist ein Python-Tool um automatisiert Daten von verschiedenen
People-to-People (P2P) Investitionsplattformen herunterzuladen und zu
einem einheitlichen Format zu aggregieren.
Das Tool besitzt eine einfache Benutzeroberfläche, in der die gewünschten
Plattformen und der Berichtszeitraum festgelegt werden können. Die
Ergebnisse (Zinszahlungen, Tilungszahlungen usw.) werden in Form einer
Excel-Tabelle auf Tages-, Monats- und Gesamtbasis ausgegeben, so dass man
unter anderem einen schnellen Überblick über die monatlichen Einnahmen aus
P2P-Investitionen erhält.  
Momentan werden folgende P2P-Plattformen unterstützt:

* Bondora
* DoFinance
* Estateguru
* Grupeer
* Iuvo
* Mintos
* PeerBerry
* Robocash
* Swaper
* Twino
* Viventor

## Warum easyp2p?

Bei der Investition in P2P-Plattformen handelt es sich um eine riskante
Geldanlage. Daher sollte keinesfalls ein zu großer Betrag in eine einzelne
Plattform investiert werden. Wie bei jeder Geldanlage gilt: nicht alle Eier
in einen Korb, Diversifikation ist wichtig! Allerdings wird es mit einer
zunehmenden Anzahl von Plattformen auch gleichzeitig schwieriger einen
Überblick über den tatsächlichen Verdienst zu behalten. Man muss sich auf
allen aktiven Plattformen einloggen, sich zum jeweiligen Kontoauszug
durchklicken, diesen herunterladen und anschließend manuell die Ergebnisse
zusammen kopieren, da natürlich alle Plattformen ihr ganz eigenes
Kontoauszugsformat haben. An dieser Stelle kommt easyp2p ins Spiel, da es
diesen Prozess komplett automatisiert und man mit wenigen Klicks einen
Überblick über alle Zahlungen für beliebige Zeiträume erhält.

## Voraussetzungen

Um easyp2p verwenden zu können sind Zugangsdaten zu mindestens einer der
unterstützten P2P-Plattformen erforderlich.

## Installation

### Linux

easyp2p basiert auf Python 3 und dem Qt5-Toolkit. Auf Debian-basierten
Systemen, z.B. Ubuntu, können die benötigten Pakete folgendermaßen
installiert werden:

    sudo apt install python3 python3-pip git libqt5gui5

Anschließen muss das Repository von GitHub geklont werden:
 
    git clone https://github.com/Ceystyle/easyp2p.git

Dann kann easyp2p einfach durch folgenden Befehl installiert werden:

    cd easyp2p
    sudo python3 setup.py install

Nach erfolgreicher Installation kann easyp2p von einem beliebigen Ordner
im Terminal gestartet werden:

    easyp2p

Zu beachten ist, dass einige P2P-Plattformen (Grupeer, Mintos, Iuvo, Swaper) 
nur ausgewertet werden können, wenn entweder der Chrome- oder Chromium-Browser
installiert sind.

### Windows & Mac

Momentan leider noch nicht offiziell unterstützt.

## Bedienungsanleitung

Die Bedienungsanleitung findet man [hier](docs/user_manual_de.md).
