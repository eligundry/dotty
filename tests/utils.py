"""Various utility functions for testing dotty."""

import os
from shutil import rmtree

from tests.constants import ASSETS_DIR


def noop(*args, **kwargs):
    """Function that does nothing that can be used by Mock."""


def fake_git_clone(_, dest):
    """A mock for Git clone that will create an empty directory."""
    os.makedirs(dest)


def get_mtimes(path):
    """Get all the mtimes from all the files in a given path."""
    mtimes = {}

    for subdir, dirs, files in os.walk(path):
        for filename in files:
            filepath = os.path.join(subdir, filename)
            mtimes[filepath] = os.path.getmtime(filepath)

        for directory in dirs:
            dirpath = os.path.join(subdir, directory)
            mtimes[dirpath] = os.path.getmtime(dirpath)

    return mtimes


def asset_join(*paths):
    """Return a path that is suitable for the tests to use."""
    return os.path.abspath(os.path.join(ASSETS_DIR, *paths))


def transform_paths(mappings):
    """Transform short test paths to full paths usable in the tests."""
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
    """Delete the assets created by the tests."""
    if os.path.exists(ASSETS_DIR):
        rmtree(ASSETS_DIR)
