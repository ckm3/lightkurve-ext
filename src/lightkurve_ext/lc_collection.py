# Override the LightCurveCollection class

import lightkurve as lk
import numpy as np
from astropy.units.quantity import Quantity
from astropy import units as u
from astropy.time import Time


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

    def stitch(self, corrector_func=None):
        if corrector_func is None:
            corrector_func = lambda x: x.normalize()
        lc = lk.LightCurveCollection.stitch(
            self, corrector_func=corrector_func)
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
            if gap_indices[i] != -1 and abs(gap_indices[i+1] - gap_indices[i]) > 1:
                yield lc[gap_indices[i]+1 if gap_indices[i] !=0 else 0 : None if gap_indices[i+1] == -1 else gap_indices[i+1]+1]

    def fill_gaps(self, method: str = "gaussian_noise"):
        """Fill in gaps in time. 
        Adopted from ``lightkurve`` package with few modification to support other methods.

        By default, the gaps will be filled with random white Gaussian noise
        distributed according to
        :math:`\mathcal{N} (\mu=\overline{\mathrm{flux}}, \sigma=\mathrm{CDPP})`.
        No other methods are supported at this time.

        Parameters
        ----------
        method : string {'gaussian_noise'}
            Method to use for gap filling. Fills with Gaussian noise by default.

        Returns
        -------
        filled_lightcurve : `LightCurve`
            A new light curve object in which all NaN values and gaps in time
            have been filled.
        """
        lc = self.copy().remove_nans()
        # nlc = lc.copy()
        newdata = {}

        # Find missing time points
        # Most precise method, taking into account time variation due to orbit
        if hasattr(lc, "cadenceno"):
            dt = lc.time.value - np.median(np.diff(lc.time.value)) * lc.cadenceno.value
            ncad = np.arange(lc.cadenceno.value[0], lc.cadenceno.value[-1] + 1, 1)
            in_original = np.in1d(ncad, lc.cadenceno.value)
            ncad = ncad[~in_original]
            ndt = np.interp(ncad, lc.cadenceno.value, dt)

            ncad = np.append(ncad, lc.cadenceno.value)
            ndt = np.append(ndt, dt)
            ncad, ndt = ncad[np.argsort(ncad)], ndt[np.argsort(ncad)]
            ntime = ndt + np.median(np.diff(lc.time.value)) * ncad
            newdata["cadenceno"] = ncad
        else:
            # Less precise method
            dt = np.nanmedian(lc.time.value[1::] - lc.time.value[:-1:])
            ntime = [lc.time.value[0]]
            for t in lc.time.value[1::]:
                prevtime = ntime[-1]
                while (t - prevtime) > 1.2 * dt:
                    ntime.append(prevtime + dt)
                    prevtime = ntime[-1]
                ntime.append(t)
            ntime = np.asarray(ntime, float)
            in_original = np.in1d(ntime, lc.time.value)

        # Fill in time points
        newdata["time"] = Time(ntime, format=lc.time.format, scale=lc.time.scale)
        f = np.zeros(len(ntime))
        f[in_original] = np.copy(lc.flux)
        fe = np.zeros(len(ntime))
        fe[in_original] = np.copy(lc.flux_err)

        # Temporary workaround for issue #1172.  TODO: remove the `if`` statement
        # below once we adopt AstroPy >=5.0.3 as a minimum dependency.
        if hasattr(lc.flux_err, 'mask'):
            fe[~in_original] = np.interp(ntime[~in_original], lc.time.value, lc.flux_err.unmasked)
        else:
            fe[~in_original] = np.interp(ntime[~in_original], lc.time.value, lc.flux_err)

        if method == "gaussian_noise":
            try:
                std = lc.estimate_cdpp().to(lc.flux.unit).value
            except:
                std = np.nanstd(lc.flux.value)
            f[~in_original] = np.random.normal(
                np.nanmean(lc.flux.value), std, (~in_original).sum()
            )
        elif method.casefold() == 'NaN'.casefold():
            f[~in_original] = np.nan
        elif method == 'zero':
            f[~in_original] = 0
        else:
            raise NotImplementedError("No such method as {}".format(method))

        newdata["flux"] = Quantity(f, lc.flux.unit)
        newdata["flux_err"] = Quantity(fe, lc.flux_err.unit)

        if hasattr(lc, "quality"):
            quality = np.zeros(len(ntime), dtype=lc.quality.dtype)
            quality[in_original] = np.copy(lc.quality)
            quality[~in_original] += 65536
            newdata["quality"] = quality
        """
        # TODO: add support for other columns
        for column in lc.columns:
            if column in ("time", "flux", "flux_err", "quality"):
                continue
            old_values = lc[column]
            new_values = np.empty(len(ntime), dtype=old_values.dtype)
            new_values[~in_original] = np.nan
            new_values[in_original] = np.copy(old_values)
            newdata[column] = new_values
        """
        return LightCurve(data=newdata, meta=self.meta)

if __name__ == "__main__":
    # lc = LightCurve(time=np.concatenate(
    #     [np.arange(0, 5, 0.1), np.arange(10, 15, 0.1)]), flux=np.arange(0, 10, 0.1), flux_err=0)
    # for temp_lc in LightCurveCollection(lc.split_by_gap()):
    #     print(temp_lc.time.value.min(), temp_lc.time.value.max())

    # raw_lc = LightCurveCollection(lc.split_by_gap()).stitch()
    # for temp_lc in LightCurveCollection(raw_lc.split_by_gap()):
    #     print(temp_lc.time.value.min(), temp_lc.time.value.max())

    from .search_local import LightCurveDirectory
    lc_dir = LightCurveDirectory('/home/ckm/.lightkurve-cache/mastDownload/TESS')
    lcc = lc_dir.search_lightcurve(73228647, author='SPOC')
    lc = LightCurve(lcc.stitch()).remove_nans()
    lc_length = len(lc)

    l = 0
    for lc in lc.split_by_gap():
        print(np.diff(lc.time.value).max())
        l += len(lc)
        print(len(lc.fill_gaps(method='gaussian_noise')))
        print(len(lc.fill_gaps(method='NaN')))
        print(len(lc.fill_gaps(method='zero')))
    
    assert l == lc_length