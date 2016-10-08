"""Unit tests to ensure that dotty is working properly."""

import os

import mock
import pytest

from dotty import ask_user, dotty, run_command


def noop(*args, **kwargs):
    """A function that does nothing that can be used by Mock to prevent certain
    commands from running.
    """


def fake_git_clone(_, dest):
    """A mock for Git clone that will create an empty directory."""
    os.makedirs(dest)


@mock.patch('dotty.ask_user', return_value=True)
def test_link_files(mock_ask, assets, link_mapping):
    """Ensure that files link correctly."""
    payload = {'link': link_mapping}
    dotty(data=payload)

    for src, target in link_mapping.items():
        assert os.path.islink(target)
        assert os.path.realpath(target) == os.path.abspath(src)

    assert assets
    assert mock_ask.call_count is not None


@mock.patch('dotty.ask_user', return_value=True)
def test_copy_files(mock_ask, assets, copy_mapping):
    """Ensure that files are copied correctly."""
    payload = {'copy': copy_mapping}
    dotty(data=payload)

    for target in copy_mapping.keys():
        assert os.path.isfile(target)
        assert not os.path.islink(target)

    assert assets
    assert mock_ask.call_count is not None


def test_create_directories(directory_list):
    """Ensure that directories are created properly."""
    payload = {'directories': directory_list}
    dotty(data=payload)

    for directory in directory_list:
        assert os.path.isdir(directory)


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


@mock.patch('dotty.run_command', side_effect=noop)
def test_clone_git_repos_mock(mock_run, git_repo_mapping):
    """Ensure that Git repos are cloned properly with no dirs created."""
    payload = {'git_repos': git_repo_mapping}
    dotty(data=payload)

    assert mock_run.call_count == len(git_repo_mapping)


@mock.patch('dotty.clone_repo', side_effect=fake_git_clone)
def test_clone_git_repos(mock_run, git_repo_mapping):
    """Ensure that Git repos are cloned properly with dirs created."""
    payload = {'git_repos': git_repo_mapping}
    dotty(data=payload)

    assert mock_run.call_count == len(git_repo_mapping)

    for directory in git_repo_mapping.values():
        assert os.path.exists(directory)
        assert os.path.isdir(directory)


@pytest.mark.parametrize('test_input,expected', (
    ('', True),
    ('y', True),
    ('Y', True),
    ('t', True),
    ('T', True),
    ('True', True),
    ('true', True),
    ('1', True),
    ('on', True),
    ('n', False),
    ('N', False),
    ('f', False),
    ('F', False),
    ('false', False),
    ('False', False),
    ('off', False),
    ('0', False),
))
def test_ask_user(test_input, expected):
    """Ensure that ask_user works correctly with strtobool."""
    patch = mock.patch('dotty.user_input', return_value=test_input)
    patch.start()

    assert ask_user(test_input) is expected

    patch.stop()


def test_raw_run_command():
    """Ensure that run_command can echo."""
    run_command('echo "hello"')
