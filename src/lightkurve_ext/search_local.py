import re
import os
import pickle
from pathlib import Path
import lightkurve as lk
from memoization import cached
from fnmatch import fnmatch
from .selection import _revise_author

AUTHOR_LIST = [
    "Kepler",
    "K2",
    "SPOC",
    "TESS-SPOC",
    "QLP",
    "TASOC",
    "PATHOS",
    "CDIPS",
    "K2SFF",
    "EVEREST",
]


class LightCurveDirectory():
    @cached
    def __init__(self, directories, use_cache=True):
        self.directories = directories
        if use_cache:
            cache_path = Path.home() / '.lightkurve_ext-cache'
            dumped_file_paths = [dumped_file_path for dumped_file_path in cache_path.iterdir()
                                    if dumped_file_path.name.startswith('obsid_path_dict_')]
            if len(dumped_file_paths) > 0:
                date_time_sorted_paths = sorted(dumped_file_paths, key=os.path.getmtime)
                with open(date_time_sorted_paths[-1], "rb") as f:
                    self.obsid_path_dict = pickle.load(f)
            else:
                import warnings
                warnings.warn('Cache file not found. Searching for local lightcurves without cache.')
                self.obsid_path_dict = {}
        else:
            self.obsid_path_dict = {}

    @cached
    def search_lightcurve(
        self,
        target,
        exptime=None,
        cadence=None,
        mission=("Kepler", "K2", "TESS"),
        author=None,
        quarter=None,
        month=None,
        campaign=None,
        sector=None,
        limit=None,
    ):
        """
        Search for local lightcurvefiles. 
        Not like lk.search_lightcurve, this method only search for observation ID from local directory.

        Parameters
        ----------
        target : int
            Target obsearvaion ID, the KIC or EPIC, TESS identifier as an integer.
        local_path : str or pathlib.Path or list of str or list of pathlib.Path
        exptime : 'long', 'short', 'fast', or a list of valid exptime
            'long' selects 10-min and 30-min cadence products;
            'short' selects 1-min and 2-min products;
            'fast' selects 20-sec products.
            Alternatively, you can pass the exact exposure time in seconds as
            an int or a float, e.g., ``exptime=600`` selects 10-minute cadence.
            By default, all cadence modes are returned.
        cadence : 'long', 'short', 'fast', or float
            Synonym for `exptime`. This keyword will likely be deprecated in the future.
        mission : str, tuple of str
            'Kepler', 'K2', or 'TESS'. By default, all will be returned.
        author : str, list or tuple of str, or "all"
            Author of the data product (`provenance_name` in the MAST API).
            Official Kepler, K2, and TESS pipeline products have author names
            'Kepler', 'K2', and 'SPOC'.
            Community-provided products that are supported include 'K2SFF', 'EVEREST'.
            By default, all light curves are returned regardless of the author.
        quarter, campaign, sector : int, list of ints
            Kepler Quarter, K2 Campaign, or TESS Sector number.
            By default all quarters/campaigns/sectors will be returned.
        month : 1, 2, 3, 4 or list of int
            For Kepler's prime mission, there are three short-cadence
            TargetPixelFiles for each quarter, each covering one month.
            Hence, if ``exptime='short'`` you can specify month=1, 2, 3, or 4.
            By default all months will be returned.
        limit : int
            Maximum number of products to return.
            By default all products will be returned.
        use_cache : bool
            If True, use the cache to speed up the search.
            By default, True.
        Returns
        ------- 
        LightCurve object
        """
        def kwargs_pattern_generator(
            target=target,
            exptime=exptime,
            cadence=cadence,
            mission=mission,
            author=author,
            quarter=quarter,
            month=month,
            campaign=campaign,
            sector=sector,
            limit=limit,
        ):

            def _pack_exptime(exptime):
                if isinstance(exptime, str):
                    exptime = exptime.lower()
                    if exptime in ["fast"]:
                        exptime = [20]
                    elif exptime in ["short"]:
                        exptime = [60, 120]
                    elif exptime in ["long", "ffi"]:
                        exptime = [600, 1200, 1800]
                    else:
                        raise ValueError(f"exptime={exptime} is not valid")
                    for e in exptime:
                        yield e
                elif isinstance(exptime, (int, float)):
                    yield exptime
                elif isinstance(exptime, (list, tuple, set)):
                    for e in exptime:
                        yield next(_pack_exptime(e))
                elif exptime is None:
                    yield "*"
                else:
                    raise TypeError(
                        "exptime must be a str, int, float, list, tuple, or set")

            if quarter:
                mission = "Kepler"
            if campaign:
                mission = "K2"
            if sector:
                mission = "TESS"

            if isinstance(sector, int):
                sector = [sector]
            elif isinstance(sector, (list, tuple)):
                pass
            elif sector is None or sector == "*" or sector == "all":
                sector = ['*']
            else:
                raise TypeError("sector must be an int or a list of ints")

            if isinstance(author, str):
                if author not in AUTHOR_LIST and author != "*" and author != "all":
                    raise ValueError(f"author must be one of {AUTHOR_LIST}")
                elif author == "*" or author == "all":
                    author = AUTHOR_LIST
                else:
                    author = [author]
            elif author is None:
                author = AUTHOR_LIST

            for s in sector:
                for et in set(_pack_exptime(exptime)):
                    for a in author:
                        # currently, I only implement the products of TESS mission
                        if a == 'SPOC' and (et == 120 or et == "*"):
                            pattern = f"tess*-s{s:{'04d' if s != '*' else ''}}-{target:016d}-[0-9]*-[xsab]_lc.fits*"
                            yield pattern
                        elif a == 'SPOC' and (et == 20 or et == "*"):
                            pattern = f"tess*-s{s:{'04d' if s != '*' else ''}}-{target:016d}-[0-9]*-[xsab]_fast-lc.fits*"
                            yield pattern
                        elif a == 'TESS-SPOC':
                            pattern = f"hlsp_tess-spoc_tess_phot_{target:016d}-s{s:{'04d' if s != '*' else ''}}_tess_v1_lc.fits*"
                            yield pattern
                        elif a == 'QLP':
                            pattern = f"hlsp_qlp_tess_ffi_s{s:{'04d' if s != '*' else ''}}-{target:016d}_tess_v01_llc.fits*"
                            yield pattern
                        elif a == 'TASOC':
                            pattern = f"hlsp_tasoc_tess_*_tic{target:011d}-s{s:{'02d' if s != '*' else ''}}-*-*-c{et:{'04d' if et != '*' else ''}}_tess_v*lc.fits*"
                            yield pattern
                        elif a == 'PATHOS':
                            pattern = f"hlsp_pathos_tess_lightcurve_tic-{target:010d}-s{s:{'04d' if s != '*' else ''}}_tess_v1_llc.fits*"
                            yield pattern

            def _pack_mission(mission):
                if isinstance(mission, list) or isinstance(mission, tuple):
                    pass
                if mission in ["Kepler", "K2", "TESS"]:
                    return mission
                else:
                    raise ValueError("Mission must be one of Kepler, K2, or TESS.")

        # Search for local lightcurves
        local_path = self.directories
        if isinstance(local_path, str):
            local_path = [Path(local_path)]

        if len(self.obsid_path_dict) > 0:
            cached_local_path = self.obsid_path_dict[target]
            local_path = [p if Path(lp) in p.parents else Path()
                        for p in cached_local_path for lp in local_path]

        files = []
        for path in local_path:
            path = Path(path)
            for pattern in kwargs_pattern_generator(
                target=target,
                exptime=exptime,
                cadence=cadence,
                mission=mission,
                author=author,
                quarter=quarter,
                month=month,
                campaign=campaign,
                sector=sector,
                limit=limit,
            ):

                if path.is_file():
                    if fnmatch(path.name, pattern):
                        files.append(path)
                else:
                    files.extend(path.rglob(pattern))

        if len(files) == 0:
            return None

        lc_collection = [_revise_author(lk.read(file)) for file in set(files)]
        # Return lightcurves
        return lk.LightCurveCollection(lc_collection)


    @cached
    def search_TESSlightcurve(
        self,
        target,
        exptime=None,
        cadence=None,
        author=None,
        sector=None,
        limit=None,
        has_sector_tree=True,
        use_cache=True
    ):
        """
        Search for local TESS lightcurves, and return a LightCurveCollection.

        Parameters
        ----------
        target : int
            Target obsearvaion ID, the KIC or EPIC, TESS identifier as an integer.
        local_path : str
            Path to local directory.
        exptime : str or list of ints
            Exposure time.
            By default all light curves are returned regardless of the exposure time.
        cadence : str or list of ints
            Cadence.
            By default all light curves are returned regardless of the cadence.
        author : str or list of str
            Author.
            By default all light curves are returned regardless of the author.
        sector : int, list of ints
            Kepler Quarter, K2 Campaign, or TESS Sector number.
            By default all quarters/campaigns/sectors will be returned.
        limit : int
            Maximum number of products to return.
        has_sector_tree : bool
            If True, local directory should be a constructed by different sectors.
            e.g., ``local_path/sector_1/**/*.fits``, ``local_path/sector_2/**/*.fits``, etc.
            Then, the search method will more effiencient.
            If False, the local directory are not constructed by different sectors, 
            and the search method might be slower.
        use_cache : bool
            If True, the search will use a cache to speed up the search.
            If False, the search will not use a cache.
            The cache is stored in ``~/.lightkurve_ext-cache/obsid_path_dict.pkl``.
            Default is True.
        Returns
        ------- 

        """
        def kwargs_pattern_generator(
            target=target,
            exptime=exptime,
            cadence=cadence,
            author=author,
            sector=sector,
            limit=limit,
        ):

            def _pack_exptime(exptime):
                if isinstance(exptime, str):
                    exptime = exptime.lower()
                    if exptime in ["fast"]:
                        exptime = [20]
                    elif exptime in ["short"]:
                        exptime = [60, 120]
                    elif exptime in ["long", "ffi"]:
                        exptime = [600, 1200, 1800]
                    else:
                        raise ValueError(f"exptime={exptime} is not valid")
                    for e in exptime:
                        yield e
                elif isinstance(exptime, (int, float)):
                    yield exptime
                elif isinstance(exptime, (list, tuple, set)):
                    for e in exptime:
                        yield next(_pack_exptime(e))
                elif exptime is None:
                    yield "*"
                else:
                    raise TypeError(
                        "exptime must be a str, int, float, list, tuple, or set")

            if isinstance(sector, int):
                sector = [sector]
            elif isinstance(sector, (list, tuple)):
                pass
            elif sector is None or sector == "*" or sector == "all":
                sector = ['*']
            else:
                raise TypeError("sector must be an int or a list of ints")

            if isinstance(author, str):
                if author not in AUTHOR_LIST:
                    raise ValueError(f"author must be one of {AUTHOR_LIST}")
                elif author == '*' or author == 'all':
                    author = AUTHOR_LIST
                else:
                    author = [author]
            elif author is None:
                author = AUTHOR_LIST

            for s in sector:
                for et in set(_pack_exptime(exptime)):
                    for a in author:
                        if a == 'SPOC' and (et == 120 or et == "*"):
                            pattern = f"tess*-s{s:{'04d' if s != '*' else ''}}-{target:016d}-[0-9]*-[xsab]_lc.fits*"
                            yield pattern, s
                        elif a == 'SPOC' and (et == 20 or et == "*"):
                            pattern = f"tess*-s{s:{'04d' if s != '*' else ''}}-{target:016d}-[0-9]*-[xsab]_fast-lc.fits*"
                            yield pattern, s
                        elif a == 'TESS-SPOC':
                            pattern = f"hlsp_tess-spoc_tess_phot_{target:016d}-s{s:{'04d' if s != '*' else ''}}_tess_v1_lc.fits*"
                            yield pattern, s
                        elif a == 'QLP':
                            pattern = f"hlsp_qlp_tess_ffi_s{s:{'04d' if s != '*' else ''}}-{target:016d}_tess_v01_llc.fits*"
                            yield pattern, s
                        elif a == 'TASOC':
                            pattern = f"hlsp_tasoc_tess_*_tic{target:011d}-s{s:{'02d' if s != '*' else ''}}-*-*-c{et:{'04d' if et != '*' else ''}}_tess_v*lc.fits*"
                            yield pattern, s
                        elif a == 'PATHOS':
                            pattern = f"hlsp_pathos_tess_lightcurve_tic-{target:010d}-s{s:{'04d' if s != '*' else ''}}_tess_v1_llc.fits*"
                            yield pattern, s

        # Search for local lightcurves
        local_path = self.directories
        if isinstance(local_path, str):
            local_path = [Path(local_path)]

        if not has_sector_tree:
            return self.search_lightcurve(
                target,
                exptime=exptime,
                cadence=cadence,
                mission='TESS',
                author=author,
                sector=sector,
                limit=limit,
            )
        else:
            local_sector_name_dict = {}
            for path in local_path:
                path = Path(path)
                for directory in [x.stem for x in path.iterdir() if x.is_dir()]:
                    if re.match('.*[0-9].*', directory):
                        local_sector_name_dict[int(
                            re.sub("[^0-9]", "", directory))] = directory
            if len(local_sector_name_dict) == 0:
                raise ValueError(
                    "Local directory is not constructed by different sectors")

        if len(self.obsid_path_dict) > 0:
                cached_local_path = self.obsid_path_dict[target]
                local_path = [p if Path(lp) in p.parents else Path(lp)
                        for p in cached_local_path for lp in local_path]

        files = []
        for path in local_path:
            for pattern, sec in kwargs_pattern_generator(
                target=target,
                exptime=exptime,
                cadence=cadence,
                author=author,
                sector=sector,
                limit=limit,
            ):
                if path.is_file():
                    if fnmatch(path.name, pattern):
                        files.append(path)
                elif sec == '*':
                    files.extend(path.rglob(pattern))
                else:
                    files.extend(
                        (path / local_sector_name_dict[sec]).rglob(pattern))

        if len(files) == 0:
            return None

        lc_collection = [_revise_author(lk.read(file)) for file in set(files)]
        # Return lightcurves
        return lk.LightCurveCollection(lc_collection)


if __name__ == '__main__':
    # print(search_local_lightcurve(25285075, '/home/ckm/TESS_download/s1/', sector=[1, 3], exptime='short', mission='TESS', author='SPOC'))
    # print(search_local_TESSlightcurve(25285075, '/home/ckm/TESS_download',
        #   sector="*", exptime=120, author='SPOC', has_sector_tree=True))
    # print(search_local_TESSlightcurve(25285075,
    #       '/home/ckm/TESS_download/', exptime=120, author=['SPOC', 'TESS-SPOC']))
    lc_dir = LightCurveDirectory(['/home/ckm/TESS_download', '/home/ckm/.lightkurve-cache/'])
    print(lc_dir.search_lightcurve(25285075, exptime=120, author='SPOC', mission='TESS'))
    print(lc_dir.search_TESSlightcurve(25285075, exptime=120, author='SPOC'))
