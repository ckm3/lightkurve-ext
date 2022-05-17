# I want to use this script to scan the files under a specific directory and 
# create a dict to save the path of every ObsID.

from fileinput import filename
from pathlib import Path
from tqdm import tqdm
import fnmatch
import re


def get_obsid_path(dir_path: str or Path) -> dict:
    """Given a directory, return a dict of ObsID and a list of paths of the files

    Args:
        dir_path (strorPath): input directory

    Returns:
        dict: obsid and paths of the files
    """
    obsid_path = {}
    dir_path = Path(dir_path)

    for file_path in tqdm(dir_path.rglob('*.fits')):
        file_name = file_path.name
        SPOC_match = re.match(r'tess\d{13}-s\d{4}-(\d{16})-\d{4}-[xsab]_lc.fits*', file_name)
        fast_SPOC_match = re.match(r'tess\d{13}-s\d{4}-(\d{16})-\d{4}-[xsab]_fast-lc.fits*', file_name)
        TESS_SPOC_match = re.match(r'hlsp_tess-spoc_tess_phot_(\d{16})-s\d{4}_tess_v1_lc.fits*', file_name)
        QLP_match = re.match(r"hlsp_qlp_tess_ffi_s\d{4}-(\d{16})_tess_v01_llc.fits*", file_name)
        TASOC_match = re.match(r"hlsp_tasoc_tess_*_tic(\d{11})-s\d{4}-*-*-c\d{4}_tess_*_*-lc.fits", file_name)

        if SPOC_match:
            obsid = int(SPOC_match.group(1))
        elif fast_SPOC_match:
            obsid = int(fast_SPOC_match.group(1))
        elif TESS_SPOC_match:
            obsid = int(TESS_SPOC_match.group(1))
        elif QLP_match:
            obsid = int(QLP_match.group(1))
        elif TASOC_match:
            obsid = int(TASOC_match.group(1))
        
        try:
            obsid_path[obsid].append(file_path)
        except KeyError:
            obsid_path[obsid] = [file_path]
    return obsid_path


if __name__ == '__main__':
    dir_path = '/home/ckm/.lightkurve-cache/mastDownload/TESS'
    obsid_path_dict = get_obsid_path(dir_path)
    for key, value in obsid_path_dict.items():
        print(key, value)
        break

