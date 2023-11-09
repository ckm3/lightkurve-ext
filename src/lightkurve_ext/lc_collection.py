# Override the LightCurveCollection class

import lightkurve as lk
import numpy as np
from astropy import units as u
from astropy.time import Time
from astropy.utils.masked.core import MaskedNDArray
from astropy.units.quantity import Quantity
from .helper_func import _revise_author


class LightCurveCollection(lk.LightCurveCollection):
    def __init__(self, lightcurves):
        lightcurves = [LightCurve(lc) for lc in lightcurves]
        sorted_lightcurves = sorted(lightcurves, key=lambda x: x.meta.get("TSTART"))
        super().__init__(sorted_lightcurves)

    def _norm_var(self, lc):
        lc = lc.copy()
        # This normlization can handle the negative flux values.
        if isinstance(lc.flux, MaskedNDArray):
            median_flux = np.nanmedian(lc.flux.data)
        else:
            median_flux = np.nanmedian(lc.flux.value)
        lc["flux"] = Quantity(
            (lc.flux.value - median_flux) / np.abs(median_flux),
            unit=u.dimensionless_unscaled,
        )

        # The flux error is not well processed, I will probably use uncertainties to handle it.
        lc["flux_err"] = Quantity(
            lc["flux_err"].value / np.abs(median_flux), unit=u.dimensionless_unscaled
        )
        lc.meta["NORMALIZED"] = True
        return lc

    def stitch(self, corrector_func=None):
        if corrector_func is None:

            def corrector_func(x):
                return self._norm_var(x)

        lc = lk.LightCurveCollection.stitch(self, corrector_func=corrector_func)
        lc = LightCurve(lc)
        lc.sort()
        return lc

    def select_lc_with_author_priority(
        self, author_priority_list=["SPOC", "TESS-SPOC", "QLP", "TASOC"]
    ):
        """
        Given a list of authors, return a lc according to the given author priority
        """
        if len(self) == 0:
            raise ValueError("The lc_collection is empty")
        u, c = np.unique(self.sector, return_counts=True)

        lcc_without_duplicates = LightCurveCollection([])
        for i, sec in enumerate(u):
            if c[i] > 1:
                dup_lcc = self[self.sector == sec]

                have_found = 0
                for pr in author_priority_list:
                    if have_found == 1:
                        break
                    for lc in dup_lcc:
                        lc = _revise_author(lc.copy())
                        if lc.meta.get("AUTHOR") == pr:
                            lcc_without_duplicates.append(lc)
                            have_found = 1
                            break
            else:
                lcc_without_duplicates.append(self[self.sector == sec][0])

        return lcc_without_duplicates


class LightCurve(lk.LightCurve):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def astronet_normalize(self):
        lc = self.copy()
        median_flux = np.nanmedian(lc.flux.value)
        min_flux = np.nanmin(lc.flux.value)
        lc.flux = Quantity(
            (lc.flux.value - min_flux) / (median_flux - min_flux) - 1,
            unit=u.dimensionless_unscaled,
        )
        lc.flux_err = Quantity(
            lc.flux_err.value / (median_flux - min_flux), unit=u.dimensionless_unscaled
        )

        lc.meta["NORMALIZED"] = True
        return lc

    def split_by_gap(self, gap_threshold=1):
        lc = self.copy()
        lc.sort()
        time_diff = np.diff(lc.time.value)
        gap_indices = [0] + np.where(time_diff > gap_threshold)[0].tolist() + [-1]

        for i in range(len(gap_indices)):
            if gap_indices[i] != -1 and abs(gap_indices[i + 1] - gap_indices[i]) >= 1:
                yield lc[
                    gap_indices[i] + 1
                    if gap_indices[i] != 0
                    else 0 : None
                    if gap_indices[i + 1] == -1
                    else gap_indices[i + 1] + 1
                ]

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
        if hasattr(lc.flux_err, "mask"):
            fe[~in_original] = np.interp(
                ntime[~in_original], lc.time.value, lc.flux_err.unmasked
            )
        else:
            fe[~in_original] = np.interp(
                ntime[~in_original], lc.time.value, lc.flux_err
            )

        if method == "gaussian_noise":
            try:
                std = lc.estimate_cdpp().to(lc.flux.unit).value
            except:
                std = np.nanstd(lc.flux.value)
            f[~in_original] = np.random.normal(
                np.nanmean(lc.flux.value), std, (~in_original).sum()
            )
        elif method.casefold() == "NaN".casefold():
            f[~in_original] = np.nan
        elif method == "zero":
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
        return self.__class__(data=newdata, meta=self.meta)

    def fast_bin(self, num_bins, bin_width=None, x_min=None, x_max=None):
        """Fast binning of light curve data.

        Parameters
        ----------
        num_bins : int
            The number of intervals to divide the x-axis into. Must be at
            least 2.
        bin_width : `~astropy.units.Quantity`
            The width of each bin on the x-axis. Must be positive, and less
            than x_max - x_min. Defaults to (x_max - x_min) / num_bins.
        x_min : `~astropy.units.Quantity`
            The inclusive leftmost value to consider on the x-axis. Must be less
            than or equal to the largest value of x. Defaults to min(x).
        x_max : `~astropy.units.Quantity`
            The exclusive rightmost value to consider on the x-axis. Must be
            greater than x_min. Defaults to max(x).

        Returns
        -------
        binned_lightcurve : `LightCurve`
            A new light curve object with the data binned.
        """
        x = self.time.value
        y = self.flux.value

        if num_bins < 2:
            raise ValueError("num_bins must be at least 2. Got: %d" % num_bins)

        # Validate the lengths of x and y.
        x_len = len(x)
        if x_len < 2:
            raise ValueError("len(x) must be at least 2. Got: %s" % x_len)
        if x_len != len(y):
            raise ValueError(
                "len(x) (got: %d) must equal len(y) (got: %d)" % (x_len, len(y))
            )

        # Validate x_min and x_max.
        x_min = x_min if x_min is not None else x[0]
        x_max = x_max if x_max is not None else x[-1]
        if x_min >= x_max:
            raise ValueError(
                "x_min (got: %d) must be less than x_max (got: %d)" % (x_min, x_max)
            )
        if x_min > x[-1]:
            raise ValueError(
                "x_min (got: %d) must be less than or equal to the largest value of x "
                "(got: %d)" % (x_min, x[-1])
            )

        # Validate bin_width.
        bin_width = bin_width if bin_width is not None else (x_max - x_min) / num_bins
        if bin_width <= 0:
            raise ValueError("bin_width must be positive. Got: %d" % bin_width)
        if bin_width >= x_max - x_min:
            raise ValueError(
                "bin_width (got: %d) must be less than x_max - x_min (got: %d)"
                % (bin_width, x_max - x_min)
            )

        bin_spacing = (x_max - x_min - bin_width) / (num_bins - 1)

        # Bins with no y-values will fall back to the global median.
        result = np.repeat(np.nan, num_bins)

        # Find the first element of x >= x_min. This loop is guaranteed to produce
        # a valid index because we know that x_min <= x[-1].
        x_start = 0
        while x[x_start] < x_min:
            x_start += 1

        # The bin at index i is the median of all elements y[j] such that
        # bin_min <= x[j] < bin_max, where bin_min and bin_max are the endpoints of
        # bin i.
        bin_min = x_min  # Left endpoint of the current bin.
        bin_max = x_min + bin_width  # Right endpoint of the current bin.
        j_start = x_start  # Inclusive left index of the current bin.
        j_end = x_start  # Exclusive end index of the current bin.

        for i in range(num_bins):
            # Move j_start to the first index of x >= bin_min.
            while j_start < x_len and x[j_start] < bin_min:
                j_start += 1

            # Move j_end to the first index of x >= bin_max (exclusive end index).
            while j_end < x_len and x[j_end] < bin_max:
                j_end += 1

            if j_end > j_start:
                # Compute and insert the median bin value.
                result[i] = np.nanmedian(y[j_start:j_end])

            # Advance the bin.
            bin_min += bin_spacing
            bin_max += bin_spacing

        return self.__class__(
            time=np.linspace(
                x_min + bin_spacing / 2,
                x_max - bin_spacing / 2,
                num_bins,
                endpoint=True,
            ),
            flux=result * self.flux.unit,
            meta=self.meta,
        )
