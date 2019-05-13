# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module containing all configurable settings for easyp2p."""

from datetime import date
from typing import Tuple


class Settings:

    """A class to store all settings of easyp2p."""

    def __init__(self, date_range: Tuple[date, date], output_file: str) -> None:
        """
        Initialize all easyp2p settings.

        date_range: Date range for which to evaluate investment results.
        output_file: File name including path where the final results should
            be saved.

        """
        self.platforms = set()
        self.date_range = date_range
        self.output_file = output_file
        self.headless = True
