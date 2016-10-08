"""Distribution script for dotty."""

from distutils.core import setup

tests_require = ['pytest', 'pytest-cov', 'pytest-mock']
test_runner = ['pytest-runner']


setup(
    name='dotty',
    version='0.1.0',
    py_modules=['dotty'],
    packages=[],
    description="Small library for managing configuration files.",
    author="Vibhav Pant",
    author_email="vibhavp@gmail.com",
    url="https://github.com/vibhavp/dotty",
    scripts='dotty',
    setup_requires=test_runner,
    extras_require={
        'tests': tests_require,
    },
    tests_require=tests_require,
)
