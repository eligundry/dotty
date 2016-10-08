"""Set of fixtures to be used by the tests."""
# pylint: disable=redefined-outer-name
import os
import platform
from shutil import rmtree

import mock
import pytest


@pytest.fixture
def link_mapping():
    """Returns the mappings needed for to create a link with dotty."""
    mappings = {
        'tests/assets/src/bashrc': 'tests/assets/target/.bashrc',
        'tests/assets/src/vimrc': 'tests/assets/target/.vimrc',
        'tests/assets/src/zshrc': 'tests/assets/target/.zshrc',
    }

    return _transform_paths(mappings)


@pytest.fixture
def copy_mapping():
    """Returns the mappings needed to copy files with dotty."""
    mappings = {
        'tests/assets/src/init.vim': 'tests/assets/target/init.vim',
        'tests/assets/src/bin': 'tests/assets/target/bin',
    }

    return _transform_paths(mappings)


@pytest.fixture
def command_list():
    """Returns a list of commands to be run."""
    return [
        "echo 'hello'",
        "ls",
        "sudo apt-get update",
        "sudo apt-get upgrade",
    ]


@pytest.fixture(params=(
    {
        'package_manager': 'pacman',
        'platform': 'Linux',
    },
    {
        'package_manager': 'apt',
        'platform': 'Linux',
    },
    {
        'package_manager': 'brew',
        'platform': 'Darwin',
    },
))
def package_list(request):
    """Returns a list of packages to install."""
    packages = [
        "vim",
        "zsh",
        "git",
        "python",
        "java",
    ]

    os_platform = request.param['platform']
    package_manager = request.param['package_manager']

    patch = mock.object.patch(platform, 'system', os_platform)
    patch.start()

    yield (packages, package_manager)

    patch.stop()


def _transform_paths(mappings):
    """Transforms the values in a provided mapping to a full path relative to
    the current directory.
    """
    if isinstance(mappings, dict):
        for key, value in mappings.items():
            mappings[key] = os.path.abspath(value)
    else:
        for idx, value in enumerate(mappings):
            mappings[idx] = os.path.abspath(value)

    return mappings


@pytest.fixture
def assets(link_mapping, copy_mapping):
    """Fixture that will create the tests assets and delete them when finished.
    """
    assets_dir = 'tests/assets'

    for folder in ('src', 'target'):
        folder = os.path.join(assets_dir, folder)
        if not os.path.exists(folder):
            os.makedirs(folder)

    for mapping in (link_mapping, copy_mapping):
        for test_file in mapping.keys():
            with open(test_file, 'w') as filehandler:
                filehandler.write('a')

    yield {'pytest': 'is silly about yield'}

    rmtree(assets_dir)
