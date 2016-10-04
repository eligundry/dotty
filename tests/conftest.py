"""Set of fixtures to be used by the tests."""
# pylint: disable=redefined-outer-name
import os
from shutil import rmtree

import pytest


def noop(*args, **kwargs):
    """A simple mock side effect that will do nothing."""


@pytest.fixture
def link_mapping():
    """Returns the mappings needed for to create a link with dotty."""
    mappings = {
        'tests/assets/src/bashrc': 'tests/assets/target/.bashrc',
        'tests/assets/src/vimrc': 'tests/assets/target/.vimrc',
        'tests/assets/src/zshrc': 'tests/assets/target/.zshrc',
    }

    return mappings


@pytest.fixture
def copy_mapping():
    """Returns the mappings needed to copy files with dotty."""
    mappings = {
        'tests/assets/src/init.vim': 'tests/assets/target/init.vim',
        'tests/assets/src/bin': 'tests/assets/target/bin',
    }

    return mappings

@pytest.fixture
def assets(mock_ask_user, link_mapping, copy_mapping):
    """Fixture that will create the tests assets and delete them when finished.
    """
    assert mock.ask_user
    assets_dir = 'tests/assets'

    for folder in ('src', 'target'):
        folder = os.path.join(assets_dir, folder)
        if not os.path.exists(folder):
            os.makedirs(folder)

    for mapping in (link_mapping, copy_mapping):
        for test_file in mapping.keys():
            with open(test_file, 'w') as filehandler:
                filehandler.write('a')

    yield True

    rmtree(assets_dir)
