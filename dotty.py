#!/usr/bin/env python3
"""Dotty is a little python script for syncing dotfiles stored on your git
repo.
"""

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
import json
import os
import platform
import shutil
import subprocess
import sys
from collections import OrderedDict
from distutils.util import strtobool

PY2 = sys.version_info[0] < 3

if PY2:
    user_input = raw_input
else:
    user_input = input


def ask_user(prompt):
    """Prompts the user for a yes or no response."""
    prompt = "{0} [Y/n] ".format(prompt)
    entered = user_input(prompt).lower()

    try:
        return entered == '' or bool(strtobool(entered))
    except ValueError:
        print("Enter a correct choice.")
        return ask_user(prompt)


def create_directory(path):
    """Creates a directory in the provided path."""
    exp = os.path.expanduser(path)

    if not os.path.isdir(exp):
        print(exp + " does not exist, creating.")
        os.makedirs(exp)


def create_symlink(src, dest, replace):
    """Creates a symlink from the source to the destination."""
    dest = os.path.expanduser(dest)
    src = os.path.abspath(src)

    if os.path.exists(dest):
        if os.path.islink(dest) and os.readlink(dest) == src:
            print("Skipping existing {0} -> {1}".format(dest, src))
            return
        elif replace or ask_user(dest + " exists, delete it?"):
            if os.path.isfile(dest):
                os.remove(dest)
            else:
                shutil.rmtree(dest)
        else:
            return

    print("Linking {0} -> {1}".format(dest, src))

    os.symlink(src, dest)


def copy_path(src, dest):
    """Copies a file or a folder into the provided destination."""
    dest = os.path.expanduser(dest)
    src = os.path.abspath(src)

    if os.path.exists(dest):
        if ask_user(dest + " exists, delete it?"):
            if os.path.isfile(dest):
                os.remove(dest)
            else:
                shutil.rmtree(dest)
        else:
            return

    print("Copying {0} -> {1}".format(src, dest))

    if os.path.isfile(src):
        shutil.copy(src, dest)
    else:
        shutil.copytree(src, dest)


def run_command(command):
    """Runs a single CLI command."""
    os.system(command)


def clone_repo(repo_url, dest):
    """Clones a git repo in to the provided destination."""
    run_command("git clone {0} {1}".format(repo_url, dest))


def _merge_dicts(*args):
    res = {}

    for arg in args:
        res.update(arg)

    return res


def program_exists(program):
    if hasattr(shutil, 'which'):
        return bool(shutil.which(program))

    try:
        return bool(
            subprocess.check_output(['which', program], shell=True)
        )
    except subprocess.CalledProcessError:
        return False


def parse_args(args):
    """Parses the incoming CLI args for dotty."""
    parser = argparse.ArgumentParser()
    parser.add_argument("config",
                        help="the JSON file you want to use",
                        type=open)
    parser.add_argument("-r",
                        "--replace",
                        action="store_true",
                        help="replace files/folders if they already exist")
    args = parser.parse_args(args)

    # Switch to the directory of the target file so all links created will be
    # relative to it.
    os.chdir(
        os.path.expanduser(os.path.abspath(os.path.dirname(args.config.name)))
    )

    # Make sure the dict is ordered so the directives execute in the order they
    # are written.
    args.config = json.load(args.config, object_pairs_hook=OrderedDict)

    return args


def dotty(data={}, replace=False):
    """Runs the dotty linker. An example of the JSON that needs to be something
    like this:

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
            "apt": ["vim-nox"],
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
        data (dict): The JSON mappings to link.
        replace (bool): Should existing symlinks and directories be replaced?
    """
    if not data:
        args = parse_args(sys.argv[1:])
        js = args.config
        replace = args.replace
    else:
        js = data

    # Check the OS
    os_type = platform.system()
    platform_js = js.get(os_type, {})

    directories = (js.get("directories", []) +
                   platform_js.get("directories", []))
    links = _merge_dicts(js.get("link", {}), platform_js.get("link", {}))
    copy = _merge_dicts(js.get("copy", {}), platform_js.get("copy", {}))
    commands = js.get("commands", []) + platform_js.get("commands", [])
    git_repos = _merge_dicts(js.get('git_repos', {}),
                             platform_js.get('git_repos', {}))
    pacman = js.get("pacman", [])
    apt = js.get("apt", [])
    brew = js.get("brew", [])

    for path in directories:
        create_directory(path)

    for repo, path in git_repos.items():
        clone_repo(repo, path)

    for src, dest in links.items():
        create_symlink(src, dest, replace)

    for src, dest in copy.items():
        copy_path(src, dest)

    for command in commands:
        run_command(command)

    if all((pacman, os_type == "Linux", program_exists("pacman"))):
        run_command("sudo pacman -S {0}".format(" ".join(pacman)))

    if all((apt, os_type == "Linux", program_exists("apt-get"))):
        run_command("sudo apt-get update && "
                    "sudo apt-get install {0}".format(" ".join(apt)))

    if all((brew, os_type == "Darwin", program_exists("brew"))):
        run_command("brew update && brew install {0}".format(" ".join(brew)))

    print("Done!")


if __name__ == "__main__":
    dotty()
