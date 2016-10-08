"""Distribution script for dotty."""

from distutils.core import setup


setup(
    name='Dotty',
    version='0.1.0',
    description="Small library for managing configuration files.",
    author="Vibhav Pant",
    author_email="vibhavp@gmail.com",
    url="https://github.com/vibhavp/dotty",
    packages=[],
    scripts='dotty',
    setup_requires=['pytest-runner'],
    extras_require={
        'tests': ['pytest', 'pytest-cov', 'pytest-mock'],
    },
)
