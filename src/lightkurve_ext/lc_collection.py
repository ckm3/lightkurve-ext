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
        median_sap_flux = np.nanmedian(lc.sap_flux.value)
        lc['flux'] = Quantity((lc.flux.value - median_flux)/np.abs(median_flux), unit=u.dimensionless_unscaled)
        lc['sap_flux'] = Quantity((lc.sap_flux.value - median_sap_flux)/np.abs(median_sap_flux), unit=u.dimensionless_unscaled)
        
        # The flux error is not well processed, I will probably use uncertainties to handle it.
        lc['flux_err'] = Quantity(lc['flux_err'].value/np.abs(median_flux), unit=u.dimensionless_unscaled)
        lc.meta["NORMALIZED"] = True
        return lc

    def stitch(self):
        lc = lk.LightCurveCollection.stitch(self, corrector_func=lambda x: self._norm_var(x))
        lc.sort()
        return lc
