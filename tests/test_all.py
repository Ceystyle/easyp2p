# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider
# pylint: disable=invalid-name

"""Helper module for running all easyp2p tests."""

import unittest

import tests.test_credentials
import tests.test_credentials_window
import tests.test_main_window
import tests.test_progress_window
import tests.parser_tests
import tests.platform_tests

# initialize the test suite
loader = unittest.TestLoader()
suite = unittest.TestSuite()

# add tests to the test suite
suite.addTests(loader.loadTestsFromModule(tests.test_credentials))
suite.addTests(loader.loadTestsFromModule(tests.test_credentials_window))
suite.addTests(loader.loadTestsFromModule(tests.test_main_window))
suite.addTests(loader.loadTestsFromModule(tests.test_progress_window))
suite.addTests(loader.loadTestsFromModule(tests.test_settings_window))
suite.addTests(loader.loadTestsFromModule(tests.parser_tests))
suite.addTests(loader.loadTestsFromModule(tests.platform_tests))

# initialize a runner, pass it the suite and run it
runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)
