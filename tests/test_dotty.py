"""Unit tests to ensure that dotty is working properly."""

import os

import mock

from dotty import dotty


@mock.patch('dotty.ask_user', return_value=True)
def test_link_files(assets, link_mapping):
    """Ensure that files link correctly."""
    payload = {'link': link_mapping}
    dotty(data=payload)

    for src, target in link_mapping.items():
        assert os.path.islink(target)
        assert os.path.realpath(target) == os.path.abspath(src)


@mock.patch('dotty.ask_user', return_value=True)
def test_copy_files(assets, copy_mapping):
    """Ensure that files are copied correctly."""
    payload = {'copy': copy_mapping}
    dotty(data=payload)

    for target in copy_mapping.keys():
        assert os.path.isfile(target)
        assert not os.path.islink(target)
