# Lightkurve-ext

This is an extension for the [Lightkurve](https://github.com/lightkurve/lightkurve) package.

Lightkurve (lk) is a Python package designed for the analysis of Kepler/K2/TESS light curves.

Thanks to lk, one can easily access the data of the light curves, and perform some basic analysis.
Although it's excellent design greatly enhances productivity, I still have some own requirements on my daily work. Therefore, I created this extensive package.
Some features are listed below:

- lk provides a conventient interface to search for light cuves from MAST, but usually I have already downloaded some data.
So, I use similar API to implement a searching process on local directory. The `lkx.LightCurveDirectory` class can handle directories contain light curves. `search_lightcurve()` method can search for the light curve files in the above directory and return them as a `lkx.SearchResults` object. It can be simply loaded as a `lkx.LightCurveCollection` object with the `load()` method.
- Before running the search, I highly recommend you to scan your target directories and crate a cache file. This can be done with a toggling `scan_dir=True` and dramatically accelerate your following search work. Once you have saved your cache file (with `dump_scan_resutls=True`), you can search for light curve files with `use_cache=True`, and no need to re-scan your directories until the content of directories are changed.

For example

    >>> import lightkurve_ext as lkx
    >>> lkx_dir = lkx.LightCurveDirectory(local_path, use_cache=False, scan_dir=True, dump_scan_results=True)
    >>> lkx_dir.search_lightcurve(target=ticid, exptime=120, author='SPOC').load()
    
    LightCurveCollection of 4 objects:
    0: <TessLightCurve LABEL="TIC 386319774" SECTOR=44 AUTHOR=SPOC FLUX_ORIGIN=pdcsap_flux>
    1: <TessLightCurve LABEL="TIC 386319774" SECTOR=6 AUTHOR=SPOC FLUX_ORIGIN=pdcsap_flux>
    2: <TessLightCurve LABEL="TIC 386319774" SECTOR=33 AUTHOR=SPOC FLUX_ORIGIN=pdcsap_flux>
    3: <TessLightCurve LABEL="TIC 386319774" SECTOR=45 AUTHOR=SPOC FLUX_ORIGIN=pdcsap_flux>

Also the `search_TESSlightcurve()` function can search local TESS light curves more efficiently with a sector constructed directory.

Moreover, I also supply a function for selecting light curves between different products (authors). That can be very useful when multiple products like SPOC and HLSP data are both available at a sector. To achieve this, use `select_lc_with_author_priority` method of our `lkx.LightCurveCollection` object and then return a `LightCurveCollection` as given author priority.

- Overwrite the `LightCurve` and `LightCurveCollection` classes to add some useful methods. For instance, our  `stitch` method of `LightCurveCollection` can handle negative flux value and normalize it as the relative variability. The `split_by_gap` method of `LightCurve` object will split a light curve into different parts with a given gap threshold. I also added some new method for the `fill_gaps` method to make it support filling with NaN and zero.

## Installation
```
git clone https://github.com/ckm3/lightkurve-ext.git
cd lightkurve-ext
pip install .
```