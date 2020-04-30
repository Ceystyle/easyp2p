# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""Module containing all configurable settings for easyp2p."""

from dataclasses import dataclass
from datetime import date
import os
from pathlib import Path
from typing import Optional, Set, Tuple


@dataclass
class Settings:
    """A class to store all settings of easyp2p."""
    date_range: Tuple[date, date]
    output_file: str
    directory: str = os.path.join(str(Path.home()), '.easyp2p')
    headless: bool = True
    platforms: Optional[Set[str]] = None
