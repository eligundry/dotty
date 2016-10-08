"""Set of fixtures to be used by the tests."""
# pylint: disable=redefined-outer-name
import json
import os
import random
import sys
from collections import OrderedDict
from shutil import rmtree

import mock
import pytest

from dotty import _merge_dicts
from tests.constants import ASSETS_DIR
from tests.utils import transform_paths, cleanup_assets


@pytest.fixture
def link_mapping():
    """Returns the mappings needed for to create a link with dotty."""
    mappings = {
        'src/bashrc': 'target/.bashrc',
        'src/vimrc': 'target/.vimrc',
        'src/zshrc': 'target/.zshrc',
    }

    yield transform_paths(mappings)

    cleanup_assets()


@pytest.fixture
def copy_file_mapping():
    """Returns the mappings needed to copy files with dotty."""
    mappings = {
        'src/init.vim': 'target/.init.vim',
        'src/offlineimaprc': 'target/.offlineimaprc',
    }

    yield transform_paths(mappings)

    cleanup_assets()


@pytest.fixture
def copy_folder_mapping():
    """Returns the mappings needed to copy folders with dotty."""
    mappings = {
        'src/bin': 'target/.bin',
        'src/copy_dir': 'target/.copy_dir',
    }

    yield transform_paths(mappings)

    cleanup_assets()

@pytest.fixture
def directory_list():
    """Returns a list of directories to create."""
    yield transform_paths([
        'target/.dir1',
        'target/.dir2',
        'target/.dir3',
    ])

    cleanup_assets()


@pytest.fixture
def copy_link_payload(link_mapping, copy_file_mapping, copy_folder_mapping,
                      directory_list):
    yield {
        'directories': directory_list,
        'link': link_mapping,
        # 'copy': _merge_dicts(copy_file_mapping, copy_folder_mapping),
        'copy': copy_file_mapping,
    }

    cleanup_assets()


@pytest.fixture
def git_repo_mapping():
    """Returns a mapping of Git repos to clone."""
    yield transform_paths({
        'https://github.com/vibhavp/dotty.git': 'target/dotty',
        'https://github.com/robbyrussell/oh-my-zsh.git': 'target/omz',
    })

    cleanup_assets()


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

    cleanup_assets()


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
    folder_path = transform_paths(os.path.join(ASSETS_DIR, 'src'))
    os.makedirs(folder_path)

    # Write the JSON file
    path = os.path.join(folder_path, 'dotty.json')

    with open(path, 'w') as json_fp:
        json.dump(full_mapping, json_fp)

    yield path

    cleanup_assets()
