"""Various utility functions for testing dotty."""

import os


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
