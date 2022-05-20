# I want to use this script to scan the files under a specific directory and
# create a dict to save the path of every ObsID.

from os import pathsep
import re
import time
import pickle
from tqdm import tqdm
from pathlib import Path
from memoization import cached


@cached
def cache_obsid_path(dir_path: str or Path or list, dump_results: bool = True, save_update_report: bool = True) -> dict:
    """Given a directory, return a dict of ObsID and a list of paths of the files

    Args:
        dir_path (strorPath): input directory or list of directories
        dump_results (bool, optional): whether to dump the results to a file. Defaults to True.

    Returns:
        dict: obsid and paths of the files
    """
    def get_obsid_path_dict_from_single_path(path: Path, output_dict: dict) -> dict:
        tqdm.write("Scanning path: {}".format(path))
        for file_path in tqdm(path.rglob('*.fits')):
            file_name = file_path.name
            SPOC_match = re.match(
                r'tess\d{13}-s\d{4}-(\d{16})-\d{4}-[xsab]_lc.fits*', file_name)
            fast_SPOC_match = re.match(
                r'tess\d{13}-s\d{4}-(\d{16})-\d{4}-[xsab]_fast-lc.fits*', file_name)
            TESS_SPOC_match = re.match(
                r'hlsp_tess-spoc_tess_phot_(\d{16})-s\d{4}_tess_v1_lc.fits*', file_name)
            QLP_match = re.match(
                r"hlsp_qlp_tess_ffi_s\d{4}-(\d{16})_tess_v01_llc.fits*", file_name)
            TASOC_match = re.match(
                r"hlsp_tasoc_tess_*_tic(\d{11})-s\d{4}-*-*-c\d{4}_tess_*_*-lc.fits*", file_name)

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
            else:
                continue

            try:
                # if obsid already exists in the dict, skip
                if file_name in [p.name for p in output_dict[obsid]]:
                    continue
                output_dict[obsid].append(file_path)
            except KeyError:
                output_dict[obsid] = [file_path]
        return output_dict

    obsid_path_dict = {}

    if isinstance(dir_path, str) or isinstance(dir_path, Path):
        dir_path = Path(dir_path)
        obsid_path_dict = get_obsid_path_dict_from_single_path(
            dir_path, obsid_path_dict)
    elif isinstance(dir_path, list):
        for path in dir_path:
            path = Path(path)
            obsid_path_dict = get_obsid_path_dict_from_single_path(
                path, obsid_path_dict)

    if dump_results:
        _create_obsid_path_file(obsid_path_dict)
        if save_update_report:
            _generate_update_report()
        else:
            pass

    return obsid_path_dict


def _generate_update_report():
    import os
    save_path = Path.home() / '.lightkurve_ext-cache'

    dumped_file_paths = [dumped_file_path for dumped_file_path in save_path.iterdir()
            if dumped_file_path.name.startswith('obsid_path_dict_')]
    if len(dumped_file_paths) < 2:
        return None

    def __compare_two_dicts(new_dict, old_dict):
        # find updates between two dicts
        updates = {}
        tqdm.write('Comparing two cached files')
        for key in tqdm(new_dict.keys()):
            if key in old_dict.keys():
                list_in_new_but_not_old = list(
                    set(new_dict[key]) - set(old_dict[key]))
                if len(list_in_new_but_not_old) > 0:
                    updates[key] = list_in_new_but_not_old
            else:
                updates[key] = new_dict[key]
        return updates

    date_time_sorted_paths = sorted(
        dumped_file_paths, key=os.path.getmtime)
    file_name_sorted_paths = sorted(dumped_file_paths, key=lambda x: time.strptime(x.stem.split('_')[-1], '%y%m%d%H%M%S'))

    if date_time_sorted_paths[-1] != file_name_sorted_paths[-1] or date_time_sorted_paths[-2] != file_name_sorted_paths[-2]:
        import warnings
        warnings.warn(
            "The modification time of the cached files are not in the same order of the file names records. Please check it in detail.")
    with open(date_time_sorted_paths[-1], 'rb') as f:
        obsid_path_dict_current = pickle.load(f)
    with open(date_time_sorted_paths[-2], 'rb') as f:
        obsid_path_dict_previous = pickle.load(f)
    if obsid_path_dict_current == obsid_path_dict_previous:
        print("No updates since last time.")
        return None
    else:
        update_dict = __compare_two_dicts(
            obsid_path_dict_current, obsid_path_dict_previous)
        with open(save_path / f"updates_{file_name_sorted_paths[-2].stem.split('_')[-1]}_{file_name_sorted_paths[-1].stem.split('_')[-1]}.pkl", 'wb') as f:
            pickle.dump(update_dict, f)


def _create_obsid_path_file(obsid_path_dict: dict) -> None:
    """Create a file to save the obsid and paths of the files

    Args:
        obsid_path_dict (dict): obsid and paths of the files
    """
    def dump_dict(path, dict):
        with open(path, 'wb') as f:
            pickle.dump(dict, f)

    save_path = Path.home() / '.lightkurve_ext-cache'
    local_time = time.strftime("%y%m%d%H%M%S", time.localtime())

    if not save_path.exists():
        save_path.mkdir()
        dump_dict(
            save_path / f"obsid_path_dict_{local_time}.pkl", obsid_path_dict)
    else:
        dump_dict(
            save_path / f"obsid_path_dict_{local_time}.pkl", obsid_path_dict)


if __name__ == '__main__':
    dir_path = ['/home/ckm/.lightkurve-cache/mastDownload/TESS',
                '/home/ckm/TESS_download/']
    obsid_path_dict = cache_obsid_path(dir_path)
    # for key, value in obsid_path_dict.items():
    #     print(key, value)
    #     break
