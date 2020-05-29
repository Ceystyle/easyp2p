#  Copyright (c) 2018-2020 Niko Sandschneider

import codecs
import os
import re
import setuptools

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="easyp2p",
    version=find_version("easyp2p", "__init__.py"),
    author="Niko Sandschneider",
    author_email="info@ceystyle.de",
    description="Application for downloading and presenting investment results \
        for people-to-people (P2P) lending platforms.",
    long_description=long_description,
    url="https://github.com/ceystyle/easyp2p",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    python_requires=">=3.5",
    install_requires=[
        'arrow', 'bs4', 'keyring', 'lxml', 'pandas', 'PyQt5', 'requests',
        'selenium', 'xlrd', 'xlsxwriter'],
    entry_points={'gui_scripts': ['easyp2p=easyp2p.ui.main_window:main']},
)
