# easyp2p

[German README](README_de.md)

## Overview

easyp2p is a Python tool for downloading and aggregating account statements 
from several people-to-people (P2P) investment platforms. The tool has a simple
graphical user interface in which the platforms and the date range of interest
can be selected. The investment results (interest payments, redemptions, ...)
will be written to an Excel file on a daily, monthly and total basis.
Currently the following P2P platforms are supported:

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
* Viainvest
* Viventor

## Why easyp2p?

Investing money in P2P platforms involves significant risks. Thus the saying
"Don't put all your eggs in one basket" is even more true than for other asset
classes and investments should be split across more than just one platform.
However, that makes it more difficult to track the actual investment
performance since you need to log into all the platforms, download account
statements and afterwards manually aggregate them. easyp2p provides a fully
automated solution to this problem.

## Prerequisites

To use easyp2p you need to be registered with at least one of the supported
P2P platforms.

## Installation

### Linux

easyp2p relies on Python 3 and the Qt5 toolkit. On Debian-based systems such
as Ubuntu the required packages can be installed by:

    sudo apt install python3 python3-pip git libqt5gui5

Next clone the repository from GitHub:
 
    git clone https://github.com/Ceystyle/easyp2p.git

easyp2p can then simply be installed by:

    cd easyp2p
    sudo python3 setup.py install

After successful installation easyp2p can be started from any folder in
the terminal:

    easyp2p

Please note that several P2P platforms (Grupeer, Mintos, Iuvo, Swaper) 
can only be evaluated if either the Chrome or Chromium browser is 
installed on the system.

### Windows & Mac

Unfortunately not officially supported yet.

## User manual

The user manual can be found [here](docs/user_manual_en.md).