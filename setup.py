# -*- coding: utf-8 -*-

import setuptools

setuptools.setup(
    name="lightkurve-ext",
    version="0.1.1",
    author="Kaiming Cui",
    author_email="cuikaiming@sjtu.edu.cn",
    description='Extras for the "lightkurve" library.',
    packages=setuptools.find_packages(where="src"),
    long_description="""
        # LightKurve-ext
        This is an extension for the [LightKurve](https://github.com/lightkurve/lightkurve) package.
        It provides some useful functions for light curve analysis.
        E.g. ``search_lightcurve`` can search your downloaded light curve files locally and return a LightCurveCollection object.
    """,
    long_description_content_type="text/markdown",
    package_dir={"": "src"},
    include_package_data=True,
    url="https://github.com/ckm3/lightkurve-ext",
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Astronomy",
        "Topic :: Scientific/Engineering :: Physics"],
    python_requires='>=3.8.0',
    install_requires=["lightkurve>=2.0"],
)