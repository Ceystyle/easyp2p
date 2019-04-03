# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Helper module for running all easyp2p tests."""

import unittest

import tests.gui_tests
import tests.parser_tests
import tests.platform_tests

# initialize the test suite
loader = unittest.TestLoader()
suite = unittest.TestSuite()

# add tests to the test suite
suite.addTests(loader.loadTestsFromModule(tests.gui_tests))
suite.addTests(loader.loadTestsFromModule(tests.parser_tests))
suite.addTests(loader.loadTestsFromModule(tests.platform_tests))

# initialize a runner, pass it the suite and run it
runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)
