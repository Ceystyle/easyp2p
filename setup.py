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

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="easyp2p",
    version=find_version("easyp2p", "__init__.py"),
    author="Niko Sandschneider",
    author_email="nsandschn@gmx.de",
    description="Package for downloading and presenting investment results for several P2P lending platforms",
    long_description=long_description,
    #url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    python_requires=">=3.5",
    install_requires=['lxml', 'pandas', 'PyQt5', 'selenium', 'xlrd', 'xlsxwriter'],
    entry_points = {'gui_scripts': ['easyp2p=easyp2p.__main__:main'],},
)
