# Lightkurve-ext

This is an extension for the [Lightkurve](https://github.com/lightkurve/lightkurve) package.

Lightkurve (lk) is a Python package is designed for the analysis of Kepler/K2/TESS light curves.

Thanks to lk, I can easily access the data of the light curves, and perform some basic analysis.
Although it's excellent, I still have some own requirements on my daily work. Therefore, I created this extensive package.
Some features are listed below:

- lk provides a conventient interface to search for light cuves from MAST, but usually I already have downloaded some data. Our `lkx.LightCurveDirectory` class can handle directories contain light curves. `search_lightcurve()` method can search for the light curve files in the above directory and return them as a `lk.LightCurveCollection` object.
- Before running the search, I highly recommend you to scan your target directories and crate a cache file. This can be done with a simple line of code and dramatically accelerate your following search work.
```
>>> import lightkurve_ext as lkx
>>> lkx.cache_obsid_path(local_path)
```
For example

    >>> lkx_dir = lkx.LightCurveDirectory(local_path)
    >>> lkx_dir.search_lightcurve(target=ticid, exptime=120, author='SPOC')
    
    LightCurveCollection of 4 objects:
    0: <TessLightCurve LABEL="TIC 386319774" SECTOR=44 AUTHOR=SPOC FLUX_ORIGIN=pdcsap_flux>
    1: <TessLightCurve LABEL="TIC 386319774" SECTOR=6 AUTHOR=SPOC FLUX_ORIGIN=pdcsap_flux>
    2: <TessLightCurve LABEL="TIC 386319774" SECTOR=33 AUTHOR=SPOC FLUX_ORIGIN=pdcsap_flux>
    3: <TessLightCurve LABEL="TIC 386319774" SECTOR=45 AUTHOR=SPOC FLUX_ORIGIN=pdcsap_flux>

Also the `search_TESSlightcurve()` function can search local TESS light curves more efficiently with a sector constructed directory.

Moreover, I also supply a function for selecting light curves between different products (authors). That can be very useful when multiple products like SPOC and HLSP data are both available at a sector. To achieve this, use `lkx.select_lc_with_author_priority` to create a new `LightCurveCollection` with a given author priority.

## Installation
```
git clone https://github.com/ckm3/lightkurve-ext.git
cd lightkurve-ext
pip install .
```