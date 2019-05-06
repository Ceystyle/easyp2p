# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module containing all configurable settings for easyp2p."""

class Settings:

    """A class to store all settings of easyp2p."""

    def __init__(self):
        """Initialize all settings."""
        self.platforms = set()
        self.date_range = None
        self.output_file = None
        self.headless = True
