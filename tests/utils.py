"""Various utility functions for testing dotty."""

import os
from shutil import rmtree

from tests.constants import ASSETS_DIR


def noop(*args, **kwargs):
    """A function that does nothing that can be used by Mock to prevent certain
    commands from running.
    """


def fake_git_clone(_, dest):
    """A mock for Git clone that will create an empty directory."""
    os.makedirs(dest)


def get_mtimes(path):
    """Gets all the mtimes from all the files and directories for a given path.
    """
    mtimes = {}

    for subdir, dirs, files in os.walk(path):
        for filename in files:
            filepath = os.path.join(subdir, filename)
            mtimes[filepath] = os.path.getmtime(filepath)

        for directory in dirs:
            dirpath = os.path.join(subdir, directory)
            mtimes[dirpath] = os.path.getmtime(dirpath)

    return mtimes


def asset_join(path):
    return os.path.abspath(os.path.join(ASSETS_DIR, path))


def transform_paths(mappings):
    """Transforms the values in a provided mapping to a full path relative to
    the current directory.
    """
    if isinstance(mappings, dict):
        path_itr = mappings.items()
    elif isinstance(mappings, (list, tuple)):
        path_itr = enumerate(mappings)
    else:
        return asset_join(mappings)

    for key, value in path_itr:
        if isinstance(key, int) or 'http' in key:
            mappings[key] = asset_join(value)
        else:
            mappings[asset_join(key)] = asset_join(mappings.pop(key))

    return mappings


def cleanup_assets():
    """Deletes the assets created by the tests."""
    if os.path.exists(ASSETS_DIR):
        rmtree(ASSETS_DIR)
