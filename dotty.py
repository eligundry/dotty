#!/usr/bin/env python
"""Dotty is a little python script for syncing dotfiles from a Git repo."""

# Copyright (C) 2015 Vibhav Pant <vibhavp@gmail.com>
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from __future__ import print_function

import argparse
import inspect
import json
import os
import platform
import shutil
import subprocess
import sys
from collections import OrderedDict
from copy import deepcopy
from distutils.util import strtobool

PY2 = sys.version_info[0] < 3
PLATFORM = platform.system()
PACKAGE_MANAGERS = (
    'apt-get',
    'brew',
    'pacman',
)

if PY2:
    user_input = raw_input  # noqa: ignore=F821
    signature = inspect.getargspec
else:
    user_input = input
    signature = inspect.signature


def ask_user(prompt):
    """Prompt the user for a yes or no response."""
    prompt = "{0} [Y/n] ".format(prompt)
    entered = user_input(prompt).lower()

    try:
        return entered == '' or bool(strtobool(entered))
    except ValueError:
        print("Enter a correct choice.")
        return ask_user(prompt)


def create_directory(path, replace):
    """Create a directory in the provided path."""
    exp = os.path.expanduser(path)

    if os.path.isdir(path) and replace:
        remove_path(path)

    if not os.path.isdir(exp):
        print("{0} does not exist, creating.".format(exp))
        os.makedirs(exp)


def create_symlink(src, dest, replace):
    """Create a symlink from the source to the destination."""
    dest = os.path.expanduser(dest)
    src = os.path.abspath(src)

    if os.path.exists(dest):
        is_same = (os.path.islink(dest) and os.readlink(dest) == src)

        if is_same and not replace:
            print("Skipping existing {0} -> {1}".format(src, dest))
            return

        if replace or ask_user("{0} exists, delete it?".format(dest)):
            remove_path(dest)
        else:
            return

    print("Linking {0} -> {1}".format(dest, src))

    os.symlink(src, dest)


def copy_path(src, dest, replace):
    """Copy a file or a folder into the provided destination."""
    dest = os.path.expanduser(dest)
    src = os.path.abspath(src)

    if os.path.exists(dest):
        if replace or ask_user("{0} exists, delete it?".format(dest)):
            remove_path(dest)
        else:
            return

    print("Copying {0} -> {1}".format(src, dest))

    if os.path.isfile(src):
        shutil.copy(src, dest)
    else:
        shutil.copytree(src, dest)


def remove_path(path):
    """Remove a target path, regardless if it's a link, folder, or file."""
    if os.path.isfile(path):
        os.unlink(path)
    elif os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
    else:
        raise RuntimeError("Path {0} cannot be removed.".format(path))


def run_command(command):
    """Run a single CLI command."""
    os.system(command)


def clone_repo(repo_url, dest):
    """Clone a Git repo into the provided destination."""
    run_command("git clone {0} {1}".format(repo_url, dest))


def merge_dicts(*args):
    """Merge an arbitrary amount of dictionaries together."""
    res = {}

    for arg in args:
        res.update(arg)

    return res


def program_exists(program):
    """Check if a CLI program exists."""
    try:
        return bool(shutil.which(program))
    except AttributeError:
        pass

    try:
        return bool(
            subprocess.check_output('which {0}'.format(program), shell=True)
        )
    except subprocess.CalledProcessError:
        return False


def cleanup(data):
    """Remove all the files, folders, and links in a provided file."""
    mappings = deepcopy(data)

    if isinstance(mappings, OrderedDict):
        mappings = OrderedDict(reversed(list(mappings.items())))

    for key, value in mappings.items():
        if key == "system":
            cleanup(value[platform])
        elif key in ('link', 'copy', 'git_repos', 'directories'):
            if isinstance(value, OrderedDict):
                paths = OrderedDict(reversed(list(value.items()))).values()
            elif isinstance(value, dict):
                paths = value.values()
            else:
                paths = value

            for path in paths:
                print("Deleting {0}".format(path))
                remove_path(path)


def parse_args(args):
    """Parse the incoming CLI args for dotty."""
    argspec = signature(dotty)

    def format_val(key):
        """Return the `action` value for the argument based on argspec."""
        if PY2:
            val = argspec.defaults[argspec[0].index(key)]
        else:
            val = argspec.parameters[key].default

        return str(val).lower()

    parser = argparse.ArgumentParser(
        usage=inspect.cleandoc(dotty.__doc__),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("json_config",
                        help="the JSON file you want to use",
                        type=open)
    # The action key is getting formatted like that in order to use dotty's
    # argspec as the only source of truth for the default values of the CLI
    # params.
    parser.add_argument("-f",
                        "--firstrun",
                        action="store_{0}".format(format_val('firstrun')),
                        help="runs all the directives available in the config")
    parser.add_argument("-r",
                        "--replace",
                        action="store_{0}".format(format_val('replace')),
                        help="replace files/folders if they already exist")
    parser.add_argument("-l",
                        "--link",
                        action="store_{0}".format(format_val('link')),
                        help="symlink links")
    parser.add_argument("-c",
                        "--copy",
                        action="store_{0}".format(format_val('copy')),
                        help="copy paths")
    parser.add_argument("-d",
                        "--directories",
                        action="store_{0}".format(format_val('directories')),
                        help="create directories")
    parser.add_argument("--commands",
                        action="store_{0}".format(format_val('commands')),
                        help="run commands")
    parser.add_argument("--install-packages",
                        action="store_{0}".format(
                            format_val('install_packages')
                        ),
                        help="install packages with system package manager")
    parser.add_argument("--git-repos",
                        action="store_{0}".format(format_val('git_repos')),
                        help="clone Git repos")
    parser.add_argument("--clean",
                        action="store_{0}".format(format_val('clean')),
                        help="clean up the files in the provided JSON")
    args = parser.parse_args(args)

    # Switch to the directory of the target file so all links created will be
    # relative to it.
    os.chdir(os.path.expanduser(os.path.abspath(os.path.dirname(
        args.json_config.name
    ))))

    # Make sure the dict is ordered so the directives execute in the order they
    # are written.
    args.json_config = json.load(args.json_config,
                                 object_pairs_hook=OrderedDict)

    return args


def get_platform_data(data, key, default=None):
    """Return config keys relevant to the current operating system."""
    if not default:
        default = []

    return data.get(PLATFORM, {}).get(key, default)


def linker(data, replace):
    """Create symlinks from the provided mappings."""
    links = merge_dicts(
        data.get("link", {}),
        get_platform_data(data, "link", default={})
    )

    for src, dest in links.items():
        create_symlink(src, dest, replace)


def copy_paths(data, replace):
    """Copy paths from the provided mappings."""
    paths = merge_dicts(
        data.get("copy", {}),
        get_platform_data(data, "copy", default={})
    )

    for src, dest in paths.items():
        copy_path(src, dest, replace)


def run_commands(data):
    """Run commands from the provided mappings."""
    commands = (data.get("commands", []) +
                get_platform_data(data, "commands"))

    for command in commands:
        run_command(command)


def clone_repos(data):
    """Clone Git repos from the provided mappings."""
    repos = merge_dicts(
        data.get('git_repos', {}),
        get_platform_data(data, 'git_repos', default={})
    )

    for repo, dest in repos.items():
        clone_repo(repo, dest)


def create_directories(data, replace):
    """Create directories from the provided config data."""
    directories = (data.get("directories", []) +
                   get_platform_data(data, "directories"))

    for path in directories:
        create_directory(path, replace)


def install_system_packages(data, manager):
    """Install system packages from the provided config data."""
    packages = " ".join(data.get(manager, []))

    if not packages or not program_exists(manager):
        return

    if manager == "pacman" and PLATFORM == "Linux":
        run_command("sudo pacman -S {0}".format(packages))

    elif manager == "apt-get" and PLATFORM == "Linux":
        run_command("sudo apt-get update && "
                    "sudo apt-get install {0}".format(packages))

    elif manager and PLATFORM == "Darwin":
        run_command("brew update && "
                    "brew install {0}".format(packages))


def dotty(json_config=None, replace=True, link=True, copy=True,
          directories=True, install_packages=False, git_repos=False,
          commands=False, firstrun=False, cli=False, clean=False):
    """Run the dotty linker.

    An example of the JSON needs to look for this to function properly is like
    so:

    .. code-block:: json
        {
            // Create Directories
            "directories": ["~/emacs.d"],
            // Link Files
            "link": {
                "source": "dest",
                "zshrc": "~/.zshrc"
                // Directories can be linked too
                "emacs/lisp/": "~/.emacs.d/lisp"
            },
            // Copy Files & Directories
            "copy": {
                "offlineimaprc": "~/.offlineimaprc"
            },
            // Run Commands
            "commands": [
                "emacs -batch -Q -l ~/.emacs.d/firstrun.el"
            ],
            // Git Repos to clone
            "git_repos": {
                "https://github.com/robbyrussell/oh-my-zsh.git": "~/.oh-my-zsh"
            },
            // Install Packages with package manager if on correct system.
            "brew": ["macvim"],
            "apt-get": ["vim-nox"],
            "pacman": ["vim"],
            // Conditional links depending on the output of `platform.system()`
            "system": {
                "Darwin": {
                    "link": {
                        "iterm-2.0-profiles.json": "~/.iterm-2.0-profiles.json"
                    }
                },
                "Linux": {
                    "link": {
                        "config/terminator.conf": "~/.config/terminator.conf"
                    }
                }
            }
        }

    Args:
        config (dict|collections.OrderedDict): The JSON mappings to link. If
            run from the CLI, the mappings are loaded into an `OrderedDict` so
            that the commands run in the exact order provided.
        replace (bool): Should existing symlinks, files, and directories be
            replaced?
    """
    if not json_config:
        if not cli:
            return dotty(cli=True, **vars(parse_args(sys.argv[1:])))

        raise RuntimeError("Data must be provided in the form of a CLI arg or "
                           "dict.")

    if clean:
        cleanup(json_config)
        print("Removed all files!")
        return

    if firstrun:
        replace = True

    for key in json_config:
        if key == "directories" and (firstrun or directories):
            create_directories(json_config, replace)

        elif key == "copy" and (firstrun or copy):
            copy_paths(json_config, replace)

        elif key == "git_repos" and (firstrun or git_repos):
            clone_repos(json_config)

        elif key == "link" and (firstrun or link):
            linker(json_config, replace)

        elif key in PACKAGE_MANAGERS and (firstrun or install_packages):
            install_system_packages(json_config, key)

        elif key == "commands" and (firstrun or commands):
            run_commands(json_config)

    print("Done!")


if __name__ == "__main__":
    dotty()
