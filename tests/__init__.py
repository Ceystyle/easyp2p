# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""Package containing all tests for easyp2p."""

import os

PLATFORMS = {
    'Bondora',
    'DoFinance',
    'Estateguru',
    'Grupeer',
    'Iuvo',
    'Mintos',
    'PeerBerry',
    'Robocash',
    'Swaper',
    'Twino'}
INPUT_PREFIX = os.path.join('tests', 'input', 'input_test_')
RESULT_PREFIX = os.path.join('tests', 'expected_results', 'result_test_')
TEST_PREFIX = os.path.join('tests', 'test_results', 'test_')
