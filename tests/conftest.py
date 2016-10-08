"""Set of fixtures to be used by the tests."""
# pylint: disable=redefined-outer-name
import json
import os
import random
from collections import OrderedDict
from shutil import rmtree

import mock
import pytest

from dotty import _merge_dicts


ASSETS_DIR = 'tests/assets'


@pytest.fixture
def link_mapping():
    """Returns the mappings needed for to create a link with dotty."""
    mappings = {
        'tests/assets/src/bashrc': 'tests/assets/target/.bashrc',
        'tests/assets/src/vimrc': 'tests/assets/target/.vimrc',
        'tests/assets/src/zshrc': 'tests/assets/target/.zshrc',
    }

    yield _transform_paths(mappings)

    _cleanup_assets()


@pytest.fixture
def copy_file_mapping():
    """Returns the mappings needed to copy files with dotty."""
    mappings = {
        'tests/assets/src/init.vim': 'tests/assets/target/.init.vim',
        'tests/assets/src/offlineimaprc': 'tests/assets/target/.offlineimaprc',
    }

    yield _transform_paths(mappings)

    _cleanup_assets()


@pytest.fixture
def copy_folder_mapping():
    """Returns the mappings needed to copy folders with dotty."""
    mappings = {
        'tests/assets/src/bin': 'tests/assets/target/.bin',
        'tests/assets/src/copy_dir': 'tests/assets/target/.copy_dir',
    }

    yield _transform_paths(mappings)

    _cleanup_assets()

@pytest.fixture
def directory_list():
    """Returns a list of directories to create."""
    yield _transform_paths([
        'tests/assets/target/.dir1',
        'tests/assets/target/.dir2',
        'tests/assets/target/.dir3',
    ])

    _cleanup_assets()


@pytest.fixture
def copy_link_payload(link_mapping, copy_file_mapping, copy_folder_mapping,
                      directory_list):
    yield {
        'directories': directory_list,
        'link': link_mapping,
        # 'copy': _merge_dicts(copy_file_mapping, copy_folder_mapping),
        'copy': copy_file_mapping,
    }

    _cleanup_assets()


@pytest.fixture
def git_repo_mapping():
    """Returns a mapping of Git repos to clone."""
    yield _transform_paths({
        'https://github.com/vibhavp/dotty.git': 'tests/assets/target/dotty',
        'https://github.com/robbyrussell/oh-my-zsh.git': (
            'tests/assets/target/omz'
        ),
    })

    _cleanup_assets()


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

    patch = mock.patch('platform.system', return_value=os_platform)
    patch.start()

    yield (packages, package_manager)

    patch.stop()


@pytest.fixture
def assets(link_mapping, copy_file_mapping, copy_folder_mapping):
    """Fixture that will create the tests assets and delete them when finished.
    """
    for folder in ('src', 'target'):
        folder = os.path.join(ASSETS_DIR, folder)
        if not os.path.exists(folder):
            os.makedirs(folder)

    # for folder in copy_folder_mapping.keys():
    #     folder = os.path.join(ASSETS_DIR, folder)
    #     if not os.path.exists(folder):
    #         os.makedirs(folder)

    for mapping in (link_mapping, copy_file_mapping):
        for test_file in mapping.keys():
            with open(test_file, 'w') as filehandler:
                filehandler.write('a')

    yield {'pytest': 'is silly about yield'}

    _cleanup_assets()


@pytest.fixture
def full_mapping(link_mapping, copy_file_mapping, directory_list,
                 git_repo_mapping, command_list, package_list,
                 copy_folder_mapping):
    """Creates full dotty mapping in an OrderedDict."""
    return OrderedDict((
        ('directories', directory_list),
        ('link', link_mapping),
        ('copy', _merge_dicts(copy_file_mapping, copy_folder_mapping)),
        ('commands', command_list),
        ('git_repos', git_repo_mapping),
        (package_list[1], package_list[0])
    ))


@pytest.fixture
def dotty_json_file(full_mapping):
    """Creates a dotty test JSON file in the asserts dir."""
    # Create the folder
    folder_path = _transform_paths(os.path.join(ASSETS_DIR, 'src'))
    os.makedirs(folder_path)

    # Write the JSON file
    path = os.path.join(folder_path, 'dotty.json')

    with open(path, 'w') as json_fp:
        json.dump(full_mapping, json_fp)

    yield path

    _cleanup_assets()


def _transform_paths(mappings):
    """Transforms the values in a provided mapping to a full path relative to
    the current directory.
    """
    if isinstance(mappings, dict):
        for key, value in mappings.items():
            mappings[key] = os.path.abspath(value)
    elif isinstance(mappings, (list, tuple)):
        for idx, value in enumerate(mappings):
            mappings[idx] = os.path.abspath(value)
    else:
        return os.path.abspath(mappings)

    return mappings


def _cleanup_assets():
    """Deletes the assets created by the tests."""
    if os.path.exists(ASSETS_DIR):
        rmtree(ASSETS_DIR)
