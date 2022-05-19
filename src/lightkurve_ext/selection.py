# Use this script to create a lc with given author priority

import numpy as np
import lightkurve as lk


def select_lc_with_author_priority(lc_collection, author_priority_list=['SPOC', 'TESS-SPOC', 'QLP', 'TASOC']):
    """
    Given a list of authors, return a lc according to the given author priority
    """
    u, c = np.unique(lc_collection.sector, return_counts=True)

    lcc_without_duplicates = []
    for i, sec in enumerate(u):
        if c[i] > 1:
            dup_lcc = lc_collection[lc_collection.sector == sec]
            for pr in author_priority_list:
                for lc in dup_lcc:
                    if lc.meta.get('AUTHOR') == pr:
                        lcc_without_duplicates.append(lc)
                        break
                break
        else:
            lcc_without_duplicates.append(
                lc_collection[lc_collection.sector == sec][0])

    return lk.LightCurveCollection(lcc_without_duplicates)


if __name__ == "__main__":
    pass
