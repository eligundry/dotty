#!/usr/bin/env python3

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

import argparse
import itertools
import json
import os
import platform
import shutil
from distutils.util import strtobool
from sys import stderr


def ask_user(prompt):
    user_input = input(prompt + " [Y/n] ").lower()

    try:
        return user_input == '' or bool(strtobool(user_input))
    except ValueError:
        print("Enter a correct choice.", file=stderr)
        return ask_user(prompt)


def create_directory(path):
    exp = os.path.expanduser(path)
    if (not os.path.isdir(exp)):
        print(exp + " doesnt exist, creating.")
        os.makedirs(exp)


def create_symlink(src, dest, replace):
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
    os.system(command)


def _merge_dicts(*args):
    return dict(itertools.chain(arg.iteritems() for arg in args))


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
            // Install Packages with package manager if on correct system.
            "brew": [
                "macvim",
            ],
            "apt": [
                "vim-nox",
            ],
            "pacman": [
                "vim",
            ],
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
        parser = argparse.ArgumentParser()
        parser.add_argument("config", help="the JSON file you want to use",
                            default=data)
        parser.add_argument("-r", "--replace", action="store_true",
                            help="replace files/folders if they already exist",
                            default=replace)
        args = parser.parse_args()
        js = json.load(open(args.config))
        replace = args.replace
        os.chdir(
            os.path.expanduser(os.path.abspath(os.path.dirname(args.config)))
        )
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
    pacman = js.get("pacman", [])
    apt = js.get("apt", [])
    brew = js.get("brew", [])

    for path in directories:
        create_directory(path)

    for src in links:
        create_symlink(src, links[src], replace)

    for src in copy:
        copy_path(src, copy[src])

    for command in commands:
        run_command(command)

    if all((pacman, os_type == 'Linux', shutil.which('pacman'))):
        run_command("sudo pacman -S {0}".format(" ".join(pacman)))

    if all((apt, os_type == 'Linux', shutil.which('apt-get'))):
        run_command("sudo apt-get update && "
                    "sudo apt-get install {0}".format(" " .join(apt)))

    if all((brew, os_type == 'Darwin', shutil.which('brew'))):
        run_command("brew update && brew install {0}".format(" ".join(brew)))

    print("Done!")


if __name__ == "__main__":
    dotty()
