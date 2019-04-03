# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""Make easyp2p directory available for the tests."""

import os
import sys
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))
