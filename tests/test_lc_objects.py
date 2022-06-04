import pytest
import lightkurve_ext as lkx

def test_lc_collection():
    lc_dir = lkx.LightCurveDirectory(
        './tests/data')
    lcc_list = lc_dir.search_lightcurve(188589164, author=['SPOC', 'TESS-SPOC'])
    assert isinstance(lcc_list, lkx.SearchResults)
    lcc = lcc_list.load()
    assert len(lcc) == 4

    # test select lc with author priority
    lcc = lcc.select_lc_with_author_priority(author_priority_list=['TESS-SPOC', 'SPOC'])
    assert len(lcc) == 2


def test_lc_object():
    lc_dir = lkx.LightCurveDirectory(
        './tests/data')
    lc_list = lc_dir.search_lightcurve(188589164, author=['SPOC', 'TESS-SPOC'])
    lc = lc_list.load()[0]
    assert isinstance(lc, lkx.LightCurve)