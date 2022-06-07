# I want to use this script to scan the files under a specific directory and
# create a dict to save the path of every ObsID.

import re
import time
import pickle
import hashlib
from tqdm import tqdm
from pathlib import Path


def cache_obsid_path(
    dir_path: str or Path or list,
    dump_results: bool = True,
    save_update_report: bool = False,
) -> dict:
    """Given a directory, return a dict of ObsID and a list of paths of the files

    Args:
        dir_path (strorPath): input directory or list of directories
        dump_results (bool, optional): whether to dump the results to a file. Defaults to True.

    Returns:
        dict: obsid and paths of the files
    """

    def get_obsid_path_dict_from_single_path(path: Path) -> dict:
        tqdm.write("Scanning path: {}".format(path))
        output_dict = {}
        for file_path in tqdm(path.rglob("*.fits")):
            file_name = file_path.name
            SPOC_match = re.match(
                r"tess\d{13}-s\d{4}-(\d{16})-\d{4}-[xsab]_lc.fits*", file_name
            )
            fast_SPOC_match = re.match(
                r"tess\d{13}-s\d{4}-(\d{16})-\d{4}-[xsab]_fast-lc.fits*", file_name
            )
            TESS_SPOC_match = re.match(
                r"hlsp_tess-spoc_tess_phot_(\d{16})-s\d{4}_tess_v1_lc.fits*", file_name
            )
            QLP_match = re.match(
                r"hlsp_qlp_tess_ffi_s\d{4}-(\d{16})_tess_v01_llc.fits*", file_name
            )
            TASOC_match = re.match(
                r"hlsp_tasoc_tess_*_tic(\d{11})-s\d{4}-*-*-c\d{4}_tess_*_*-lc.fits*",
                file_name,
            )

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
        if len(output_dict) == 0:
            print("No matched fits file found in {}".format(path))
        return output_dict

    obsid_path_dicts = []
    if isinstance(dir_path, str) or isinstance(dir_path, Path):
        dir_path = Path(dir_path)
        obsid_path_dicts = [get_obsid_path_dict_from_single_path(dir_path)]
    elif isinstance(dir_path, set):
        for path in dir_path:
            obsid_path_dicts.append(get_obsid_path_dict_from_single_path(path))
    elif isinstance(dir_path, list):
        dir_path = set([Path(p) for p in dir_path])
        for path in dir_path:
            obsid_path_dicts.append(get_obsid_path_dict_from_single_path(path))
    else:
        raise TypeError(
            "dir_path must be a str or Path object or a list of str or Path object"
        )

    updates = []
    for path, obsid_path_dict in zip(dir_path, obsid_path_dicts):
        update_dict = _generate_update_report(
            path, obsid_path_dict, dump_updates=save_update_report
        )
        if dump_results and update_dict != {}:
            _create_obsid_path_file(path, obsid_path_dict)
        updates.append(update_dict)

    return obsid_path_dicts, updates


def _generate_update_report(
    path: str or Path, new_dict: dict = None, dump_updates: bool = True
) -> None:
    import os

    path_hash = hashlib.md5(Path(path).as_posix().encode("utf-8")).hexdigest()
    save_path = Path.home() / ".lightkurve_ext-cache" / path_hash
    if not save_path.exists():
        return None

    dumped_file_paths = [
        dumped_file_path
        for dumped_file_path in save_path.iterdir()
        if dumped_file_path.name.startswith("obsid_path_dict_")
        or not save_path.exists()
    ]
    if len(dumped_file_paths) < 1:
        print("Can not find any previous dumped file.")
        return None

    def __compare_two_dicts(new_dict, old_dict):
        # find updates between two dicts
        updates = {}
        tqdm.write("Comparing two cached files")
        for key in tqdm(new_dict.keys()):
            if key in old_dict.keys():
                list_in_new_but_not_old = list(set(new_dict[key]) - set(old_dict[key]))
                if len(list_in_new_but_not_old) > 0:
                    updates[key] = list_in_new_but_not_old
            else:
                updates[key] = new_dict[key]
        return updates

    date_time_sorted_paths = sorted(dumped_file_paths, key=os.path.getmtime)
    file_name_sorted_paths = sorted(
        dumped_file_paths,
        key=lambda x: time.strptime(x.stem.split("_")[-1], "%y%m%d%H%M%S"),
    )

    if date_time_sorted_paths[-1] != file_name_sorted_paths[-1]:
        import warnings

        warnings.warn(
            "The modification time of the cached files are not in the same order of the file names records. Please check it in detail."
        )
    with open(date_time_sorted_paths[-1], "rb") as f:
        obsid_path_dict_previous = pickle.load(f)
    if new_dict == obsid_path_dict_previous:
        print(f"Cache already exist, no updates for {path} since last time.")
        return {}
    else:
        update_dict = __compare_two_dicts(new_dict, obsid_path_dict_previous)

        if update_dict == {}:
            print(f"Cache already exist, no updates for {path} since last time.")
            return update_dict

        if dump_updates:
            with open(
                save_path
                / f"updates_to_{file_name_sorted_paths[-1].stem.split('_')[-1]}.pkl",
                "wb",
            ) as f:
                pickle.dump(update_dict, f)
                print(
                    "Successfully dump updates to {}".format(
                        save_path
                        / f"updates_to_{file_name_sorted_paths[-1].stem.split('_')[-1]}.pkl"
                    )
                )
        else:
            return update_dict


def _create_obsid_path_file(path: str or Path, obsid_path_dict: dict) -> None:
    """Create a file to save the obsid and paths of the files

    Args:
        obsid_path_dict (dict): obsid and paths of the files
    """

    def dump_dict(save_path, dict):
        with open(save_path, "wb") as f:
            pickle.dump(dict, f)
            print(f"Successfully dump cache file to {save_path} for {path}")

    path_hash = hashlib.md5(Path(path).as_posix().encode("utf-8")).hexdigest()
    save_path = Path.home() / ".lightkurve_ext-cache" / path_hash
    local_time = time.strftime("%y%m%d%H%M%S", time.localtime())

    if not save_path.exists():
        save_path.mkdir()
        dump_dict(save_path / f"obsid_path_dict_{local_time}.pkl", obsid_path_dict)
    else:
        dump_dict(save_path / f"obsid_path_dict_{local_time}.pkl", obsid_path_dict)


if __name__ == "__main__":
    dir_path = [
        "/home/ckm/.lightkurve-cache/mastDownload/TESS",
        "/home/ckm/.lightkurve-cache/mastDownload/TESS",
    ]
    obsid_path_dict = cache_obsid_path(
        dir_path, dump_results=True, save_update_report=True
    )
