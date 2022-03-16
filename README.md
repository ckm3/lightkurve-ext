# Lightkurve-ext

This is an extension for the [Lightkurve](https://github.com/lightkurve/lightkurve) package.

Lightkurve(lk) is a Python package is designed for the analysis of Kepler/K2/TESS light curves.

Thanks to lk, I can easily access the data of the light curves, and perform some basic analysis.
Although it's excellent, I still have some own requirements on my daily work. Therefore, I created this extensive package.
Some features are listed below:

- lk provides a conventient interface to search for light cuves from MAST, but usually I already have downloaded some data. Our `lkx.search_local_lightcurve()` function can search for the light curve files in the specific local directory and return them as a `lk.LightCurveCollection` object.

For example

    >>> import lightkurve_ext as lkx
    >>> lkx.search_local_lightcurve(target=ticid, local_path='~/.lightkurve-cache', exptime=120, author='SPOC')
    
    LightCurveCollection of 4 objects:
    0: <TessLightCurve LABEL="TIC 386319774" SECTOR=44 AUTHOR=SPOC FLUX_ORIGIN=pdcsap_flux>
    1: <TessLightCurve LABEL="TIC 386319774" SECTOR=6 AUTHOR=SPOC FLUX_ORIGIN=pdcsap_flux>
    2: <TessLightCurve LABEL="TIC 386319774" SECTOR=33 AUTHOR=SPOC FLUX_ORIGIN=pdcsap_flux>
    3: <TessLightCurve LABEL="TIC 386319774" SECTOR=45 AUTHOR=SPOC FLUX_ORIGIN=pdcsap_flux>

Also the `lkx.search_local_TESSlightcurve()` function can search local TESS light curves more efficiently with a sector constructed directory.

## Installation
```
git clone https://github.com/ckm3/lightkurve-ext.git
cd lightkurve-ext
pip install .
```