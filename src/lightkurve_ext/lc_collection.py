# Override the LightCurveCollection class

import lightkurve as lk
import numpy as np
from astropy.units.quantity import Quantity
from astropy import units as u


class LightCurveCollection(lk.LightCurveCollection):
    def __init__(self, lightcurves):
        super().__init__(lightcurves)

    def _norm_var(self, lc):
        lc = lc.copy()
        # This normlization can handle the negative flux values.
        median_flux = np.nanmedian(lc.flux.value)
        lc['flux'] = Quantity((lc.flux.value - median_flux) /
                              np.abs(median_flux), unit=u.dimensionless_unscaled)

        # The flux error is not well processed, I will probably use uncertainties to handle it.
        lc['flux_err'] = Quantity(
            lc['flux_err'].value/np.abs(median_flux), unit=u.dimensionless_unscaled)
        lc.meta["NORMALIZED"] = True
        return lc

    def stitch(self):
        lc = lk.LightCurveCollection.stitch(
            self, corrector_func=lambda x: self._norm_var(x))
        lc = LightCurve(lc)
        lc.sort()
        return lc


class LightCurve(lk.LightCurve):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def astronet_normalize(self):
        lc = self.copy()
        median_flux = np.nanmedian(lc.flux.value)
        min_flux = np.nanmin(lc.flux.value)
        lc.flux = Quantity((lc.flux.value - min_flux) /
                           (median_flux - min_flux) - 1, unit=u.dimensionless_unscaled)
        lc.flux_err = Quantity(
            lc.flux_err.value / (median_flux - min_flux), unit=u.dimensionless_unscaled)

        lc.meta["NORMALIZED"] = True
        return lc

    def split_by_gap(self, gap_threshold=1):
        lc = self.copy()
        lc.sort()
        time_diff = np.diff(lc.time.value)
        gap_indices = [0] + \
            np.where(time_diff > gap_threshold)[0].tolist() + [-1]

        for i in range(len(gap_indices)):
            if i == 0:
                continue
            if gap_indices[i] - gap_indices[i-1] > 1 or gap_indices[i] == -1:
                yield lc[gap_indices[i-1]:gap_indices[i]]


if __name__ == "__main__":
    lc = LightCurve(time=np.concatenate(
        [np.arange(0, 5, 0.1), np.arange(10, 15, 0.1)]), flux=np.arange(0, 10, 0.1), flux_err=0)
    for temp_lc in LightCurveCollection(lc.split_by_gap()):
        print(temp_lc.time.value.min(), temp_lc.time.value.max())

    raw_lc = LightCurveCollection(lc.split_by_gap()).stitch()
    for temp_lc in LightCurveCollection(raw_lc.split_by_gap()):
        print(temp_lc.time.value.min(), temp_lc.time.value.max())
