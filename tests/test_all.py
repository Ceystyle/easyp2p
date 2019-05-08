# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Helper module for running all easyp2p tests."""

import unittest

if __name__ == '__main__':
    # initialize the test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # add tests to the test suite
    suite.addTests(loader.discover('tests', 'test_*'))

    # initialize a runner, pass it the suite and run it
    runner = unittest.TextTestRunner(verbosity=3)
    result = runner.run(suite)
