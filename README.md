# easyp2p

## Überblick

easyp2p ist ein Python-Tool um automatisiert Daten von verschiedenen P2P-Investitionsplattformen herunterzuladen und diese in einem einheitlichen Format darzustellen.
Das Tool besitzt eine einfache Benutzeroberfläche, in der die gewünschten Plattformen und der Berichtszeitraum festgelegt werden können. Die Ergebnisse (Zinszahlungen,
Tilungszahlungen usw.) werden in Form einer Excel-Tabelle für den gesamten Zeitraum und pro Monat ausgegeben, so dass man unter anderem einen schnellen Überblick über
die monatlichen Einnahmen aus P2P-Investitionen erhält.  
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

## Warum easyp2p?

Bei der Investition in P2P-Plattformen handelt es sich um eine riskante Geldanlage. Daher sollte keinesfalls ein zu großer Betrag in eine einzelne Plattform investiert
werden. Wie bei jeder Geldanlage gilt: nicht alle Eier in einen Korb, Diversifikation ist wichtig! Allerdings wird es mit einer zunehmenden Anzahl von Plattformen auch
gleichzeitig schwieriger einen Überblick über den tatsächlichen Verdienst zu behalten. Ist man beispielsweise auf zehn verschiedenen Plattformen aktiv und möchte einen
monatlichen Überblick über erhaltene Zinszahlungen muss man sich auf allen zehn Plattformen einloggen, sich zum jeweiligen Kontoauszug durchklicken, diesen herunterladen
und anschließend händisch die Ergebnisse zusammen kopieren, da natürlich alle Plattformen ihr ganz eigenes Kontoauszugsformat haben. An dieser Stelle kommt easyp2p ins
Spiel, da es diesen Prozess komplett automatisiert und man mit wenigen Klicks einen Überblick über alle Zahlungen für beliebige Zeiträume erhält.

## Voraussetzungen

Um easyp2p verwenden zu können sind Zugangsdaten zu mindestens einer der unterstützten P2P-Plattformen erforderlich.

## Installation

### Linux

Auf Linux-basierten Systemen ist Python 3.x in der Regel schon vorinstalliert. Daher muss als externe Abhängigkeit lediglich ChromeDriver installiert werden, das von easyp2p benutzt wird, um auf die Webseiten der P2P-Plattformen zuzugreifen:

    sudo apt-get install chromium-driver

Anschließend kann easyp2p durch den folgenden Befehl installiert werden:

    python3 setup.py install

### Windows & Mac

Momentan leider noch nicht unterstützt.

## Bedienungsanleitung

Die Benutzeroberfläche von easyp2p ist (hoffentlich) weitgehend selbsterklärend:

![Hauptfenster von easyp2p](docs/main_window_screenshot.png)

Im oberen Teil können die P2P-Plattformen ausgewählt werden, für die Ergebnisse erzeugt werden sollen. Im Feld darunter wird der Berichtszeitraum eingestellt. easyp2p unterstützt nur volle Monate. Die Ergebnisse werden in Form einer Excel-Datei ausgegeben, die im nächsten Feld ausgewählt werden kann. Mit dem Button "Starte Auswertung" kann die Auswertung gestartet werden.

Zunächst öffnet sich ein Fenster, um die Zugangsdaten zu den ausgewählten P2P-Plattformen abzufragen. Diese können entweder jedes Mal aufs Neue eingegeben werden oder (sofern vom Betriebssystem unterstützt) im Keyring gespeichert werden. Ist letzteres gewünscht, so muss der Haken in der Checkbox gesetzt werden. Für Plattformen, die bereits im Keyring gespeichert sind, werden die Zugangsdaten nicht erneut abgefragt. Sollen die im Keyring gespeicherten Zugangsdaten gelöscht oder geändert werden, z.B. nach einer Aktualisierung des Passworts, so kann dies im Einstellungsfenster, das man über den Button mit den drei Punkten erreicht, geschehen.
Nachdem alle Zugangsdaten abgefragt wurdem, öffnet sich ein neues Fenster, in dem der Fortschritt zu sehen ist. Neben allgemeinen Informationen zum Status werden hier auch evtl. Fehlermeldungen angezeigt.
