"""Unit tests to ensure that dotty is working properly."""

import os

import mock

from dotty import dotty


def noop(*args, **kwargs):
    """A function that does nothing that can be used by Mock to prevent certain
    commands from running.
    """


@mock.patch('dotty.ask_user', return_value=True)
def test_link_files(mock_ask, assets, link_mapping):
    """Ensure that files link correctly."""
    payload = {'link': link_mapping}
    dotty(data=payload)

    for src, target in link_mapping.items():
        assert os.path.islink(target)
        assert os.path.realpath(target) == os.path.abspath(src)

    assert mock_ask.call_count is not None


@mock.patch('dotty.ask_user', return_value=True)
def test_copy_files(mock_ask, assets, copy_mapping):
    """Ensure that files are copied correctly."""
    payload = {'copy': copy_mapping}
    dotty(data=payload)

    for target in copy_mapping.keys():
        assert os.path.isfile(target)
        assert not os.path.islink(target)

    assert mock_ask.call_count is not None


@mock.patch('dotty.run_command', side_effect=noop)
def test_run_command(mock_run, command_list):
    """Ensure that commands are run properly."""
    payload = {'commands': command_list}
    dotty(data=payload)

    assert mock_run.call_count == len(command_list)


@mock.patch('dotty.program_exists', return_value=True)
@mock.patch('dotty.run_command', side_effect=noop)
def test_install_packages(mock_run, mock_exists, package_list):
    """Ensure that packages are installed properly."""
    packages, manager = package_list
    payload = {manager: packages}
    dotty(data=payload)

    assert mock_exists.call_count == 3
    assert mock_run.call_count == 1
