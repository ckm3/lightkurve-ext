# I want to use this script to scan the files under a specific directory and
# create a dict to save the path of every ObsID.

import re
import sqlite3
from typing import Union
from tqdm import tqdm
from pathlib import Path
import logging
import time

# Create a logger
logger = logging.getLogger('database_logger')
logger.setLevel(logging.DEBUG)  # Set the logging level

def initialize_cache_dir() -> Path:
    """Initialize the cache directory for the obsid_path_dict"""
    cache_dir = Path.home() / ".lightkurve_ext-cache"
    if not cache_dir.exists():
        cache_dir.mkdir()
        print("Successfully create cache directory at {}".format(cache_dir))
    else:
        print("Cache directory already exists at {}".format(cache_dir))
    return cache_dir

def write_tess_lc_database(cache_dir, search_results) -> None:
    """Using databse to save the local TESS light curve file"""

    conn = sqlite3.connect(cache_dir / "TESS_light_curve.db")
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS tess_light_curve
        (ticid int, author text, sector int, exp_time int, file_path text,
        PRIMARY KEY (ticid, sector, exp_time, author))
        """
    )

    c.executemany(
        "INSERT OR IGNORE INTO tess_light_curve VALUES (?,?,?,?,?)", search_results
    )

    conn.commit()
    conn.close()


def cache_obsid_path(
    dir_path: Union[str, Path],
) -> None:
    """Given a directory, return a dict of ObsID and a list of paths of the files

    Args:
        dir_path (strorPath): input directory
        dump_results (bool, optional): whether to dump the results to a file. Defaults to True.

    Returns:
        dict: obsid and paths of the files
    """
    cache_dir = initialize_cache_dir()
    # Create a file handler
    handler = logging.FileHandler(cache_dir.parent / 'database.log')
    handler.setLevel(logging.DEBUG)  # Set the handler level
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    def get_obsid_path_dict_from_single_path(path: Path) -> dict:
        tqdm.write("Scanning available LC products in path: {}".format(path))
        output_list = []
        for file_path in tqdm(path.rglob("*.fits")):
            file_name = file_path.name
            SPOC_match = re.match(
                r"tess\d{13}-s(\d{4})-(\d{16})-\d{4}-[xsab]_lc.fits*", file_name
            )
            fast_SPOC_match = re.match(
                r"tess\d{13}-s(\d{4})-(\d{16})-\d{4}-[xsab]_fast-lc.fits*", file_name
            )
            TESS_SPOC_match = re.match(
                r"hlsp_tess-spoc_tess_phot_(\d{16})-s(\d{4})_tess_v1_lc.fits*",
                file_name,
            )
            QLP_match = re.match(
                r"hlsp_qlp_tess_ffi_s(\d{4})-(\d{16})_tess_v01_llc.fits*", file_name
            )
            TASOC_match = re.match(
                r"hlsp_tasoc_tess_*_tic(\d{11})-s(\d{4})-*-*-c\d{4}_tess_*_*-lc.fits*",
                file_name,
            )

            if SPOC_match:
                author = "SPOC"
                obsid = int(SPOC_match.group(2))
                sector = int(SPOC_match.group(1))
                exptime = 120
            elif fast_SPOC_match:
                author = "SPOC"
                obsid = int(fast_SPOC_match.group(2))
                sector = int(fast_SPOC_match.group(1))
                exptime = 20
            elif TESS_SPOC_match:
                author = "TESS_SPOC"
                obsid = int(TESS_SPOC_match.group(1))
                sector = int(TESS_SPOC_match.group(2))
                exptime = 1800 if sector < 27 else (600 if sector < 56 else 200)
            elif QLP_match:
                author = "QLP"
                obsid = int(QLP_match.group(2))
                sector = int(QLP_match.group(1))
                exptime = 1800 if sector < 27 else (600 if sector < 56 else 200)
            elif TASOC_match:
                author = "TASOC"
                obsid = int(TASOC_match.group(1))
                sector = int(TASOC_match.group(2))
                exptime = 1800 if sector < 27 else (600 if sector < 56 else 200)
            else:
                continue

            unique_tuple = (obsid, author, sector, exptime)

            # if object already exists in the list, skip
            if unique_tuple in output_list:
                continue
            output_list.append(unique_tuple + (file_path.absolute().as_posix(),))

        if len(output_list) == 0:
            print("No matched fits file found in {}".format(path))
        return output_list

    if isinstance(dir_path, str) or isinstance(dir_path, Path):
        dir_path = Path(dir_path)
        obsid_path_list = get_obsid_path_dict_from_single_path(dir_path)
        write_tess_lc_database(cache_dir, obsid_path_list)
        print("Successfully cache the light curve files in {}".format(dir_path))
        logger.info("Successfully cache the light curve files in {}".format(dir_path))
    else:
        raise TypeError(
            "dir_path must be a str or Path object or a list of str or Path object"
        )


if __name__ == "__main__":

    dir_path = "/storage/tess/spoc_full_cadence/S01/"
    obsid_path_dict = cache_obsid_path(
        dir_path,
    )
