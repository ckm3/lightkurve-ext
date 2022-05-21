# Use this script to create a lc with given author priority

import numpy as np
from .lc_collection import LightCurveCollection


def select_lc_with_author_priority(lc_collection, author_priority_list=['SPOC', 'TESS-SPOC', 'QLP', 'TASOC']):
    """
    Given a list of authors, return a lc according to the given author priority
    """
    if len(lc_collection) == 0:
        raise ValueError("The lc_collection is empty")
    u, c = np.unique(lc_collection.sector, return_counts=True)

    lcc_without_duplicates = LightCurveCollection([])
    for i, sec in enumerate(u):
        if c[i] > 1:
            dup_lcc = lc_collection[lc_collection.sector == sec]

            have_found = 0
            for pr in author_priority_list:
                if have_found == 1:
                    break
                for lc in dup_lcc:
                    lc = _revise_author(lc.copy())
                    if lc.meta.get('AUTHOR') == pr:
                        lcc_without_duplicates.append(lc)
                        have_found = 1
                        break
        else:
            lcc_without_duplicates.append(
                lc_collection[lc_collection.sector == sec][0])

    return lcc_without_duplicates


def _revise_author(lc):
    """This function is useful because the author of TESS-SPOC file is same with SPOC file, 
    That makes the selction useless when SPOC and TESS-SPOC are both in the list.
    """
    if lc.meta.get('AUTHOR') != 'SPOC':
        return lc
    exptime =  lc.meta.get('TIMEDEL')
    exptime_minute = exptime * 24 * 60
    exptime_second = exptime_minute * 60
    if np.isclose(exptime_minute, 2) or np.isclose(exptime_second, 20):
        return lc
    elif np.isclose(exptime_minute, 30) or np.isclose(exptime_minute, 10) or np.isclose(exptime_second, 200):
        lc.meta['AUTHOR'] = 'TESS-SPOC'
        return lc
    else:
        raise ValueError(f"The exptime of the {lc.meta.get('FILENAME')} is not correct for SPOC or TESS-SPOC")


if __name__ == "__main__":
    pass
