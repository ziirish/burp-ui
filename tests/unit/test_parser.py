import os
import tempfile

from burpui.misc.parser.utils import OptionInt, OptionMulti


def test_confsrv(parser):
    confsrv = parser.server_conf
    stdout = confsrv.get("stdout")
    keep = confsrv.get("keep")
    keep_raw = confsrv.get_raw("keep")
    port = confsrv.get("port")
    port_raw = confsrv.get_raw("port")
    assert stdout == 0
    assert keep == [3, 2]
    assert isinstance(keep_raw, OptionMulti)
    assert keep_raw.dump() == "keep := 3\nkeep = 2"
    assert port == 4971
    assert isinstance(port_raw, OptionInt)
    # assert port_raw.dump() == 'port = 4971\nmax_children = 5'


def test_save_conf(parser):
    (tmp, tmp_dest) = tempfile.mkstemp()
    os.close(tmp)
    confsrv = parser.server_conf
    confsrv["stdout"] = 1
    confsrv.store(confsrv.default, tmp_dest, True)
    with open(tmp_dest) as conf:
        assert "stdout = 1\n" in conf.readlines()
    os.unlink(tmp_dest)
