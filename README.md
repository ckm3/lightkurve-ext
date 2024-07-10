# Lightkurve-ext

![PyPI](https://img.shields.io/pypi/v/lightkurve-ext?style=flat) ![PyPI - License](https://img.shields.io/pypi/l/lightkurve-ext)

Lightkurve-ext is an extension for the [Lightkurve](https://github.com/lightkurve/lightkurve) package, a Python library designed for the analysis of Kepler/K2/TESS light curves. While Lightkurve provides easy access to light curve data and basic analysis tools, Lightkurve-ext extends its functionality to meet specific requirements in daily work.

## Features

- **Local Directory Search**: Lightkurve-ext provides a convenient interface to search for light curves from local directories. The `lkx.LightCurveDirectory` class can handle directories containing light curves. The `search_lightcurve()` method can search for light curve files in the directory and return them as a `lkx.SearchResults` object. These results can be loaded as a `lkx.LightCurveCollection` object with the `load()` method.

- **Directory Scanning and Caching**: To speed up the search process, Lightkurve-ext allows you to scan your target directories and create a cache database. This can be done by setting `scan_dir=True`. Once you have finished the scanning, you can search for light curve files with `use_cache=True`, eliminating the need to re-scan your directories unless their content changes.

Here's an example of how to use these features:

```python
import lightkurve_ext as lkx
lkx_dir = lkx.LightCurveDirectory(local_path, use_cache=True, scan_dir=True)
lkx_dir.search_lightcurve(target=ticid, exptime=120, author='SPOC').load()
```



- **Additional Methods for LightCurve and LightCurveCollection**: Lightkurve-ext extends the `LightCurve` and `LightCurveCollection` classes with additional methods to provide more flexibility and functionality for light curve analysis. 
  
    - **Author priority selection**: Lightkurve-ext provides a function for selecting light curves between different products (authors). This is useful when multiple products like SPOC and HLSP data are both available at a sector. To achieve this, use the `select_lc_with_author_priority` method of the `lkx.LightCurveCollection` object.

    - **Stitch light curves**: The `stitch` method of `LightCurveCollection` is designed to handle negative flux values, which can occur due to noise or other anomalies in the data. This method normalizes these values, treating them as relative variability. This allows for a more accurate and meaningful analysis of the light curve data.

    - **Split light curve by gaps**: The `split_by_gap` method of the `LightCurve` object is used when a light curve needs to be divided into different segments based on a specified gap threshold. This is particularly useful when analyzing light curves that have significant gaps or discontinuities. By splitting the light curve into smaller, continuous segments, each segment can be analyzed separately, providing more detailed and accurate results.

    - **Fill gaps**: The `fill_gaps` method has been enhanced to support filling gaps in the light curve data with NaN (Not a Number) or zero. This is useful when dealing with missing or incomplete data. By filling these gaps, the continuity of the light curve can be maintained, which is important for many types of light curve analysis.

## Installation
You can install Lightkurve-ext using pip:
```
pip install lightkurve-ext -U
```
Or install from source (recommended because the package is still under development):
```
git clone https://github.com/ckm3/lightkurve-ext.git
cd lightkurve-ext
pip install .
```