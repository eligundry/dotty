"""Distribution script for dotty."""

from setuptools import find_packages, setup


TESTS_REQUIRE = (
    'mock',
    'pytest',
    'pytest-cov',
    'pytest-mock',
    'tox',
)
TEST_RUNNER = ('pytest-runner',)


setup(
    name='dotty',
    version='0.2.0',
    packages=find_packages(),
    description="Small library for managing configuration files.",
    author="Vibhav Pant",
    author_email="vibhavp@gmail.com",
    url="https://github.com/vibhavp/dotty",
    install_requires=(),
    extras_require={
        'tests': TESTS_REQUIRE,
    },
    setup_requires=TEST_RUNNER,
    tests_require=TESTS_REQUIRE,
    entry_points={
        'console_scripts': [
            'dotty=dotty:dotty'
        ],
    }
)
