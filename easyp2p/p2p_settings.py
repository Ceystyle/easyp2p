# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module containing all configurable settings for easyp2p."""

from dataclasses import dataclass
from datetime import date
from typing import Optional, Set, Tuple


@dataclass
class Settings:
    """A class to store all settings of easyp2p."""
    date_range: Tuple[date, date]
    output_file: str
    headless: bool = True
    platforms: Optional[Set[str]] = None
