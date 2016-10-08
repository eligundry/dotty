"""Unit tests to ensure that dotty is working properly."""

import os
from collections import OrderedDict

import mock
import pytest

from dotty import ask_user, dotty, parse_args, program_exists, run_command, PY2
from tests.conftest import ASSETS_DIR
from tests.utils import noop, fake_git_clone, get_mtimes


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
def test_copy_files(mock_ask, assets, copy_file_mapping):
    """Ensure that files are copied correctly."""
    payload = {'copy': copy_file_mapping}
    dotty(data=payload)

    for target in copy_file_mapping.keys():
        assert not os.path.islink(target)
        assert os.path.isfile(target)

    assert assets
    assert mock_ask.call_count is not None


def test_create_directories(directory_list):
    """Ensure that directories are created properly."""
    payload = {'directories': directory_list}
    dotty(data=payload)

    for directory in directory_list:
        assert os.path.isdir(directory)


@pytest.mark.xfail(reason="Symlinking is acting weird")
@pytest.mark.parametrize('replace', (True, False))
def test_replace_items(replace, assets, copy_link_payload):
    """Ensure items can be replaced if needed."""
    patcher = mock.patch('dotty.ask_user', return_value=replace)
    patcher.start()

    # Create things
    dotty(data=copy_link_payload)
    og_times = get_mtimes(os.path.join(ASSETS_DIR, 'target'))

    # Replace everything
    dotty(data=copy_link_payload, replace=replace)
    new_times = get_mtimes(os.path.join(ASSETS_DIR, 'target'))

    try:
        for path in new_times.keys():
            assert (new_times[path] != og_times[path]) == replace
    finally:
        # Always clean up your patches
        patcher.stop()

    assert assets


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


@pytest.mark.parametrize('create_dirs', (True, False))
def test_clone_git_repos(create_dirs, git_repo_mapping):
    """Ensure that Git repos are cloned properly with dirs created."""
    if create_dirs:
        patcher = mock.patch('dotty.clone_repo', side_effect=fake_git_clone)
    else:
        patcher = mock.patch('dotty.run_command', side_effect=noop)

    patcher.start()

    payload = {'git_repos': git_repo_mapping}
    dotty(data=payload)

    if create_dirs:
        for directory in git_repo_mapping.values():
            assert os.path.exists(directory)
            assert os.path.isdir(directory)

    patcher.stop()


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


@mock.patch('os.chdir', side_effect=noop)
def test_parse_args(mock_chdir, dotty_json_file, full_mapping):
    """Ensure that argument parsing works as expected."""
    args = parse_args([dotty_json_file, '-r'])

    assert mock_chdir.call_count == 1
    assert args.replace is True
    assert isinstance(args.config, OrderedDict)
    assert args.config == full_mapping


@pytest.mark.parametrize('use_shutil,program,passing', (
    (True, 'python', True),
    (True, 'really-shouldnt-exist', False),
    (False, 'python', True),
    (False, 'really-shouldnt-exist', False),
))
def test_program_exists(use_shutil, program, passing):
    """Ensure that program_exists works as expected."""
    if not use_shutil:
        patcher = mock.patch('dotty.shutil.which', side_effect=AttributeError,
                             create=PY2)
        patcher.start()

    assert program_exists(program) is passing

    if not use_shutil:
        patcher.stop()
