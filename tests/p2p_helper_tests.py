# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
This module contains functions for preparing test files with expected results.

The files will be used by parser_tests to compare the actual to the expected
results.

"""
from datetime import date
import os
import sys
from typing import Tuple

import tests.test_parser as parser_tests
import easyp2p.platforms as p2p_platforms
import easyp2p.p2p_helper as p2p_helper


def _generate_parser_results(
        platform: str, date_range: Tuple[date, date], input_file: str,
        output_file: str) -> None:
    """
    Helper function for generating, comparing and writing parser results.

    Args:
        platform: Name of the P2P platform
        date_range: Date range of the account statement
        input_file: File name including path with parser input data
        output_file: File name including path where results should be saved

    """
    if os.path.isfile(output_file):
        df_old = p2p_helper.get_df_from_file(output_file)
    platform_class = getattr(
        getattr(p2p_platforms, platform.lower()), platform)
    platform_instance = platform_class(date_range)
    (df, _) = platform_instance.parse_statement(input_file)
    if os.path.isfile(output_file):
        print('New df:\n', df)
        print('Old df:\n', df_old)
        choice = input('Do you want to replace old with new df (y/n/q)? ')
        if choice.lower() == 'q':
            sys.exit()
        elif choice.lower() != 'y':
            return
    else:
        print('Df:\n', df)
        choice = input('Do you want to save the df (y/n/q)? ')
        if choice.lower() == 'q':
            sys.exit()
        elif choice.lower() != 'y':
            return
    df.to_csv(output_file)


def _get_choice_from_user(message: str) -> bool:
    """
    Helper function to get confirmation from the user.

    Args:
        message: Message for the user

    Returns:
        True if user chooses y, False otherwise

    """
    choice = input(message + ' (y(es)/n(o)/q(uit)? ')
    if choice.lower() == 'q':
        sys.exit()
    elif choice.lower() == 'y':
        return True
    else:
        return False


def main():
    """
    Generate the expected result files for the unit tests.

    This function generates the expected results files for the parser unit
    tests. It can generate the default, unknown cashflow type, no cashflows
    and unknown currency result files. Since it uses the code which these
    expected results should test, the result files need to be checked manually
    before using them!

    """
    print('WARNING: this will overwrite expected test results!\n')

    platform_list = [
        'Bondora', 'DoFinance', 'Estateguru', 'Grupeer', 'Iuvo', 'Mintos',
        'PeerBerry', 'Robocash', 'Swaper', 'Twino']

    if _get_choice_from_user('Generate default parser results'):
        for platform in platform_list:
            # DoFinance has its own date range
            if platform == 'DoFinance':
                date_range = (date(2018, 5, 1), date(2018, 9, 30))
            else:
                date_range = (date(2018, 9, 1), date(2018, 12, 31))
            input_file = parser_tests.INPUT_PREFIX + '{0}_parser.{1}'.format(
                platform.lower(), parser_tests.PLATFORMS[platform])
            output_file = parser_tests.RESULT_PREFIX + '{0}_parser.csv'.format(
                platform.lower())
            _generate_parser_results(
                platform, date_range, input_file, output_file)

    if _get_choice_from_user('Generate unknown cashflow parser results'):
        for platform in platform_list:
            if platform in [
                    'DoFinance', 'Estateguru', 'Grupeer', 'Iuvo',
                    'Mintos', 'Robocash', 'Twino']:
                #TODO: generate the unknown cf input files
                if platform == 'DoFinance':
                    date_range = (date(2018, 5, 1), date(2018, 9, 30))
                else:
                    date_range = (date(2018, 9, 1), date(2018, 12, 31))
                input_file = parser_tests.INPUT_PREFIX \
                    + '{0}_parser_unknown_cf.{1}'.format(
                        platform.lower(), parser_tests.PLATFORMS[platform])
                output_file = parser_tests.RESULT_PREFIX \
                    + '{0}_parser_unknown_cf.csv'.format(platform.lower())
                _generate_parser_results(
                    platform, date_range, input_file, output_file)

    if _get_choice_from_user('Generate no cashflows parser results'):
        for platform in platform_list:
            date_range = (date(2016, 9, 1), date(2016, 12, 31))
            input_file = parser_tests.INPUT_PREFIX \
                + '{0}_parser_no_cfs.{1}'.format(
                    platform.lower(), parser_tests.PLATFORMS[platform])
            output_file = parser_tests.RESULT_PREFIX \
                + '{0}_parser_no_cfs.csv'.format(platform.lower())
            _generate_parser_results(
                platform, date_range, input_file, output_file)


if __name__ == '__main__':
    main()
