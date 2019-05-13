import os
import pytest
import configobj
import validate

from tempfile import mkstemp

from burpui.config import BUIConfig

TEST_CONFIG = b"""
[Global]
# backend comment
backend = something
timeout = 12
duplicate = nyan

#[Test]

[Production]
duplicate = cat
run = true
sql = none
array = some, VALUES
"""

TEST_CONFIG_FAILURE = b"""
[I is a wrong file
hi ha ho
"""


def test_config_init():
    casters = ['string_lower_list', 'force_string', 'boolean_or_string']
    fd, tmpfile = mkstemp()
    os.write(fd, TEST_CONFIG)
    os.close(fd)

    fd, wrong = mkstemp()
    os.write(fd, TEST_CONFIG_FAILURE)
    os.close(fd)

    config = BUIConfig(tmpfile)
    with pytest.raises(configobj.ConfigObjError):
        fail = BUIConfig(wrong, defaults={})

    assert config.safe_get('backend', section='Global') == 'something'
    assert config.safe_get('timeout', 'integer', 'Global') == 12

    config.default_section('Production')

    assert config.safe_get('duplicate') == 'cat'
    assert config.safe_get('duplicate', section='Global') == 'nyan'
    assert config.safe_get('run', 'boolean_or_string') is True
    assert config.safe_get('sql', 'boolean_or_string') == 'none'

    array = config.safe_get('array', 'string_lower_list')
    assert array[1] == 'values'
    assert array[0] == 'some'
    assert isinstance(config.safe_get('array'), list)

    assert config.safe_get('array', 'force_string') == 'some,VALUES'

    for cast in casters:
        # safe_get is safe and shouldn't raise any exception
        assert config.safe_get('i iz not in ze config!', cast) is None

    os.unlink(tmpfile)
    os.unlink(wrong)


def test_config_reload():
    fd, tmpfile = mkstemp()
    os.write(fd, TEST_CONFIG)
    os.close(fd)
    config = BUIConfig(tmpfile)

    assert 'last' not in config.options.get('Production', {})

    with open(tmpfile, 'a') as cfg:
        print("last = ohai", file=cfg)

    config.mtime = -1
    assert 'last' in config.options.get('Production', {})
    assert config.options.get('Production', {}).get('last') == 'ohai'

    os.unlink(tmpfile)


def test_config_sections():
    fd, tmpfile = mkstemp()
    os.write(fd, TEST_CONFIG)
    os.close(fd)
    config = BUIConfig(tmpfile)

    with open(tmpfile) as cfg:
        lines = [x.rstrip() for x in cfg.readlines()]
        assert '[Unknown]' not in lines
        assert '[Test]' not in lines

    assert not config.lookup_section('Unknown')
    with open(tmpfile) as cfg:
        lines = [x.rstrip() for x in cfg.readlines()]
        assert '[Unknown]' in lines
        assert lines[-1] == '[Unknown]'

    assert not config.lookup_section('Test')
    with open(tmpfile) as cfg:
        lines = [x.rstrip() for x in cfg.readlines()]
        assert '[Test]' in lines
        assert lines[-1] != '[Test]'

    assert config.lookup_section('Production')

    os.unlink(tmpfile)


def test_config_rename_section():
    fd, tmpfile = mkstemp()
    os.write(fd, TEST_CONFIG)
    os.close(fd)
    config = BUIConfig(tmpfile)

    with open(tmpfile) as cfg:
        lines = [x.rstrip() for x in cfg.readlines()]
        assert '[Production2]' not in lines

    assert not config.rename_section('Unknown', 'Test')
    assert config.rename_section('Production', 'Production2')
    with open(tmpfile) as cfg:
        lines = [x.rstrip() for x in cfg.readlines()]
        assert '[Production2]' in lines

    os.unlink(tmpfile)


def test_config_rename_option():
    fd, tmpfile = mkstemp()
    os.write(fd, TEST_CONFIG)
    os.close(fd)
    config = BUIConfig(tmpfile)

    config.default_section('Global')
    with pytest.raises(KeyError):
        config.rename_option('unknown', 'yeah', 'Global')

    with pytest.raises(ValueError):
        config.rename_option('test', 'truc', 'Unknown')

    assert 'back' not in config.options.get('Global', {})
    assert not config.rename_option('backend', 'backend', 'Global')
    assert config.rename_option('backend', 'back', 'Global')
    assert config.safe_get('back') == 'something'

    os.unlink(tmpfile)


def test_config_move_option():
    fd, tmpfile = mkstemp()
    os.write(fd, TEST_CONFIG)
    os.close(fd)
    config = BUIConfig(tmpfile)

    assert 'New' not in config.options
    assert 'backend' not in config.options.get('New', {})
    assert not config.move_option('backend', 'Global', 'Global')
    assert config.move_option('backend', 'Global', 'New')
    assert config.safe_get('backend', section='New') == 'something'

    os.unlink(tmpfile)


def test_config_safe_get():
    fd, tmpfile = mkstemp()
    os.write(fd, TEST_CONFIG)
    os.close(fd)
    config = BUIConfig(tmpfile)

    assert config.safe_get('timeout', 'idontknow', 'Global') == '12'
    assert config.safe_get('test', section='hahaha') is None

    os.unlink(tmpfile)
