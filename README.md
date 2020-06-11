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

On most Linux based systems Python 3 is usually already included. The only
other external dependency of easyp2p is ChromeDriver which can be installed
by:

    sudo apt-get install chromium-driver

After downloading all files from GitHub easyp2p can simply be installed by:

    sudo python3 setup.py install

### Windows & Mac

Unfortunately not officially supported yet.

## User manual

The user manual can be found [here](docs/user_manual_en.md).