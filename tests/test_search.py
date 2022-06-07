import pytest
import hashlib
from pathlib import Path
import lightkurve_ext as lkx


def test_LightCruveDirectory():
    # test a single directory
    lc_dir = lkx.LightCurveDirectory("./tests/data/TESS", use_cache=True)
    assert lc_dir.directories == [Path("./tests/data/TESS")]

    # test a list of directories
    lc_dir = lkx.LightCurveDirectory(
        ["./tests/data/TESS", "./tests/data/HLSP"], use_cache=True
    )
    assert lc_dir.directories == set(
        [Path("./tests/data/TESS"), Path("./tests/data/HLSP")]
    )

    # test scan a directory
    lc_dir = lkx.LightCurveDirectory("./tests/data/TESS", scan_dir=True)
    assert len(lc_dir.obsid_path_dicts) > 0

    # test save cache
    lc_dir = lkx.LightCurveDirectory(
        "./tests/data/TESS", use_cache=False, scan_dir=True, dump_scan_results=True
    )
    cache_path = (
        Path.home()
        / ".lightkurve_ext-cache"
        / hashlib.md5(
            (Path("./tests/data/TESS").as_posix()).encode("utf-8")
        ).hexdigest()
    )
    assert cache_path.exists()


def test_search_local_lightcurves():
    # test search directories
    lc_dir = lkx.LightCurveDirectory(
        ["./tests/data/HLSP", "./tests/data/TESS"],
        use_cache=False,
        scan_dir=True,
        dump_scan_results=True,
    )
    search_results = lc_dir.search_lightcurve(
        441801208, exptime=120, author="SPOC", mission="TESS"
    )
    assert isinstance(search_results, lkx.SearchResults)
    lcc = search_results.load()
    assert len(lcc) == 1

    # test search a target with HLSP products
    lcc = lc_dir.search_lightcurve(
        1925740387, author="TESS-SPOC", mission="TESS"
    ).load()
    assert isinstance(lcc, lkx.LightCurveCollection)
    assert len(lcc) == 2

    # test search a target with wrong author
    search_results = lc_dir.search_lightcurve(1925740387, author="SPOC", mission="TESS")
    assert search_results is None
