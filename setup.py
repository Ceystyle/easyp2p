import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="easyp2p",
    version="0.0.1",
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
    ],
    python_requires='>=3.5',
    install_requires=['pandas', 'PyQt5', 'selenium', 'xlrd', 'xlsxwriter'],
    entry_points = {'gui_scripts': ['easyp2p=easyp2p.easyp2p:main'],},
)
