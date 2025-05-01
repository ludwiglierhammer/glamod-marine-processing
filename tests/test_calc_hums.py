import pytest

import glamod_marine_processing.qc_suite.modules.CalcHums as ch


def test_vap_from_example():
    """
    This is from Kate's example in the file
    """
    assert ch.vap(10., 15., 1013) == 12.3
    assert ch.vap(-15., -10., 1013) == 1.7
    assert ch.vap(None, 15., 1013) is None


def test_vap_from_sh():
    """
    This is from Kate's example in the file
    """
    assert ch.vap_from_sh(7.6, 1013.) == 12.3

def test_sh():
    """
    This is from Kate's example in the file
    """
    assert ch.sh(10., 15., 1013.) == 7.6
    assert ch.sh(None, 15., 1013.) is None
    assert ch.sh(-15., -10., 1013.) == 1.0

def test_sh_from_vap():
    """
    This is from Kate's example in the file
    """
    assert ch.sh_from_vap(12.3,1013.,1013.) == 7.6

def test_rh():
    """
    This is from Kate's example in the file
    """
    assert ch.rh(10., 15., 1013.) == 72.0
    assert ch.rh(-15., -10., 1013.) == 63.6
    assert ch.rh(None, 15., 1013.) is None

def test_wb():
    """
    This is from Kate's example in the file
    """
    assert ch.wb(10., 15., 1013) == 12.2
    assert ch.wb(-15., -10., 1013) == -10.9
    assert ch.wb(None, 15., 1013) is None

def test_dpd():
    """
    This is from Kate's example in the file
    """
    assert ch.dpd(10., 15.) == 5.0
    assert ch.dpd(None, 15.) is None

def test_td_from_vap():
    """
    They're all from Kate's examples in the file
    """
    assert ch.td_from_vap(12.3, 1013., 15.) == 10.0
    assert ch.td_from_vap(12.3, 1013., -15.) == 8.7


