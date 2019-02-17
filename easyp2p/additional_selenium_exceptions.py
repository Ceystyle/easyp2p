# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
Definition of additional Selenium expected conditions which are not part of
upstream (yet).

.. moduleauthor:: Niko Sandschneider <nsandschn@gmx.de>

"""

from typing import Callable, List
from selenium import webdriver

class one_of_many_expected_conditions_true():
    """
    An expectation for checking if (at least) one of several provided expected
    conditions for the Selenium webdriver is true.
    """
    def __init__(self, conditions: List[Callable[[webdriver.Chrome], bool]]) \
            -> None:
        self.conditions = conditions

    def __call__(self, driver: webdriver.Chrome) -> bool:
        for condition in self.conditions:
            try:
                if condition(driver):
                    return True
            except:
                pass
        return False
