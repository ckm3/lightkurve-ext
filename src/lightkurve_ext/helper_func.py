import numpy as np


def _revise_author(lc):
    """This function is useful because the author of TESS-SPOC file (one of a HLSP products) is same with SPOC file,
    That makes the selction useless when SPOC and TESS-SPOC are both in the list.
    """
    if lc.meta.get("AUTHOR") != "SPOC":
        return lc
    exptime = lc.meta.get("TIMEDEL")
    exptime_minute = exptime * 24 * 60
    exptime_second = exptime_minute * 60
    if np.isclose(exptime_minute, 2) or np.isclose(exptime_second, 20):
        return lc
    elif (
        np.isclose(exptime_minute, 30)
        or np.isclose(exptime_minute, 10)
        or np.isclose(exptime_second, 200)
    ):
        lc.meta["AUTHOR"] = "TESS-SPOC"
        return lc
    else:
        raise ValueError(
            f"The exptime of the {lc.meta.get('FILENAME')} is not correct for SPOC or TESS-SPOC"
        )


if __name__ == "__main__":
    pass
