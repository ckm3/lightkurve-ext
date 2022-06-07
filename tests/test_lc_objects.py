import pytest
import numpy as np
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

    # test lightcurve object and split_by_gap, fill_gaps, and fast_bin methods
    lc_dir = lkx.LightCurveDirectory('./tests/data/', scan_dir=True)
    lcc = lc_dir.search_lightcurve(73228647, author='SPOC').load().select_lc_with_author_priority()
    lc = lcc.stitch().remove_nans()
    lc_length = len(lc)
    l = 0
    for lc in lc.split_by_gap():
        print(np.diff(lc.time.value).max())
        l += len(lc)
        # print(len(lc.fill_gaps(method='gaussian_noise')))
        print(len(lc.fill_gaps(method='NaN')))
        print(len(lc.fill_gaps(method='zero')))
    assert l == lc_length
    assert len(lc.fast_bin(10)) == 10

    # test bin LC with number of bins larger than the length of LC
    assert len(lc.fast_bin(lc_length + 10)) == lc_length + 10