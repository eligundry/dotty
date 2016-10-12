"""Unit tests to ensure that dotty is working properly."""

import json
import os
from collections import OrderedDict

import dotty
import mock
import pytest

from tests.utils import (
    asset_join, fake_git_clone, get_mtimes, noop, transform_paths
)


def test_data_must_be_present():
    """Ensure that data must be provided to dotty."""
    with pytest.raises(RuntimeError):
        dotty.dotty(cli=True)


def test_link_files(mock_ask_user, assets, link_mapping):
    """Ensure that files link correctly."""
    enabled, replace = assets
    payload = {'link': link_mapping}
    dotty.dotty(json_config=payload, link=enabled, replace=replace)

    for src, target in link_mapping.items():
        assert os.path.islink(target) is enabled
        assert (os.path.realpath(target) == os.path.abspath(src)) is enabled

    assert mock_ask_user.call_count >= 0


def test_copy_files(mock_ask_user, assets, copy_file_mapping,
                    copy_folder_mapping):
    """Ensure that files are copied correctly."""
    enabled, replace = assets
    payload = {
        'copy': dotty.merge_dicts(copy_file_mapping, copy_folder_mapping)
    }
    dotty.dotty(json_config=payload, copy=enabled, replace=replace)

    for target in copy_file_mapping.values():
        assert not os.path.islink(target)
        assert os.path.isfile(target) is enabled

    for target in copy_folder_mapping.values():
        assert not os.path.islink(target)
        assert os.path.isdir(target) is enabled

    assert mock_ask_user.call_count >= 0


@pytest.mark.parametrize('enabled', (True, False))
def test_create_directories(directory_list, enabled):
    """Ensure that directories are created properly."""
    payload = {'directories': directory_list}
    dotty.dotty(json_config=payload, directories=enabled)

    for directory in directory_list:
        assert os.path.isdir(directory) is enabled


def test_replace_items(mock_ask_user, assets, copy_link_payload):
    """Ensure assets can be replaced if needed."""
    enabled, replace = assets

    # Create things
    # When getting the modified times, if the files will be replaced, subtract
    # 1 from their time in order to avoid issues with time collisions.
    dotty.dotty(json_config=copy_link_payload, firstrun=True)
    og_times = get_mtimes(transform_paths('target'), sub_one=replace)

    # Replace everything
    dotty.dotty(
        json_config=copy_link_payload,
        firstrun=enabled,
        replace=replace
    )
    new_times = get_mtimes(transform_paths('target'))

    # If they have been replaced the times should be different
    assert ((new_times != og_times) ==
            any([replace, enabled, mock_ask_user.return_value]))
    assert bool(mock_ask_user.call_count) != any([replace, enabled])


@pytest.mark.parametrize('enabled', (True, False))
@mock.patch('dotty.run_command', side_effect=noop)
def test_run_command(mock_run, command_list, enabled):
    """Ensure that commands are run properly."""
    payload = {'commands': command_list}
    dotty.dotty(json_config=payload, commands=enabled)

    assert (mock_run.call_count == len(command_list)) is enabled


@pytest.mark.parametrize('enabled', (True, False))
@mock.patch('dotty.program_exists', return_value=True)
@mock.patch('dotty.run_command', side_effect=noop)
def test_install_packages(mock_run, mock_exists, package_list, enabled):
    """Ensure that packages are installed properly."""
    packages, manager = package_list
    payload = {manager: packages}
    dotty.dotty(json_config=payload, install_packages=enabled)

    assert (mock_exists.call_count == 1) is enabled
    assert (mock_run.call_count == 1) is enabled


@pytest.mark.parametrize('enabled', (True, False))
@pytest.mark.parametrize('create_dirs', (True, False))
def test_clone_git_repos(create_dirs, git_repo_mapping, enabled):
    """Ensure that Git repos are cloned properly with dirs created."""
    if create_dirs:
        patcher = mock.patch('dotty.clone_repo', side_effect=fake_git_clone)
    else:
        patcher = mock.patch('dotty.run_command', side_effect=noop)

    patcher.start()

    payload = {'git_repos': git_repo_mapping}
    dotty.dotty(json_config=payload, git_repos=enabled)

    if create_dirs:
        for directory in git_repo_mapping.values():
            assert os.path.exists(directory) is enabled
            assert os.path.isdir(directory) is enabled

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

    assert dotty.ask_user(test_input) is expected

    patch.stop()


@mock.patch('tests.test_dotty.dotty.user_input', side_effect=('not-valid', '3', 'y'))
def test_ask_user_recursion(mocked_ask_user):
    """Ensure the ask_user asks again when an invalid value is provided."""
    assert dotty.ask_user('You mad?')
    assert mocked_ask_user.call_count == 3


def test_raw_run_command():
    """Ensure that run_command can echo."""
    dotty.run_command('echo "hello"')


@mock.patch('os.chdir', side_effect=noop)
def test_parse_args(mock_chdir, dotty_json_file, full_mapping):
    """Ensure that argument parsing works as expected."""
    args = dotty.parse_args([dotty_json_file, '-r'])

    assert mock_chdir.call_count == 1
    assert isinstance(args.json_config, OrderedDict)
    assert args.json_config == full_mapping
    assert args.replace
    assert args.link
    assert args.copy
    assert args.directories
    assert not args.install_packages
    assert not args.git_repos
    assert not args.commands
    assert not args.firstrun
    assert not args.clean


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
                             create=dotty.PY2)
        patcher.start()

    assert dotty.program_exists(program) is passing

    if not use_shutil:
        patcher.stop()


def test_remove_path_error():
    """Ensure that remove_path will raise an error when path doesn't exist."""
    with pytest.raises(RuntimeError):
        dotty.remove_path('doesnt-exist')


@pytest.mark.parametrize('dict_type', (dict, OrderedDict, 'file'))
@mock.patch('dotty.run_command', side_effect=noop)
@mock.patch('dotty.clone_repo', side_effect=fake_git_clone)
def test_clean(mock_clone, mock_run, assets, full_mapping, dict_type,
               dotty_json_file):
    """Ensure that cleanup works as expected."""
    if dict_type == 'file':
        with open(asset_join(dotty_json_file)) as json_fp:
            full_mapping = json.load(json_fp, object_pairs_hook=OrderedDict)
    else:
        full_mapping = dict_type(full_mapping)

    dotty.dotty(json_config=full_mapping, firstrun=True)
    dotty.dotty(json_config=full_mapping, clean=True)

    assert os.listdir(transform_paths('target')) == []

    def mapping_test(mapping):
        """Ensure that none of the source files were touched."""
        for key, value in mapping.items():
            if key in ('link', 'copy'):
                for path in value:
                    assert any([
                        os.path.isfile(path),
                        os.path.isdir(path),
                    ])
            elif key == 'system':
                mapping_test(value[dotty.PLATFORM])

        return True

    assert mapping_test(full_mapping)
