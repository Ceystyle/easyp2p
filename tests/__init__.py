# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""Package containing all tests for easyp2p."""

import os

PLATFORMS = {
    'Bondora': 'xlsx',
    'DoFinance': 'xlsx',
    'Estateguru': 'csv',
    'Grupeer': 'xlsx',
    'Iuvo': 'xlsx',
    'Mintos': 'xlsx',
    'PeerBerry': 'csv',
    'Robocash': 'xls',
    'Swaper': 'xlsx',
    'Twino': 'xlsx'}
INPUT_PREFIX = os.path.join('tests', 'input', 'input_test_')
RESULT_PREFIX = os.path.join('tests', 'expected_results', 'result_test_')
TEST_PREFIX = os.path.join('tests', 'test_results', 'test_')
