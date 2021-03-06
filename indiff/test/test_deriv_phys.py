import sys
import unittest

import numpy as np
import xarray as xr

from indiff._constants import LON_STR, LAT_STR, PFULL_STR
from indiff.utils import wraparound
from indiff.deriv import (
    PhysDeriv, LonDeriv, LatDeriv, SphereEtaDeriv,
    LonFwdDeriv, LatFwdDeriv, EtaFwdDeriv, SphereFwdDeriv,
    LonBwdDeriv, LatBwdDeriv, EtaBwdDeriv, SphereBwdDeriv,
    SphereEtaFwdDeriv, SphereEtaBwdDeriv
)

from . import InfiniteDiffTestCase


class PhysDerivSharedTests(object):
    def test_init(self):
        self.assertDatasetIdentical(self.deriv_obj.arr, self.arr)
        self.assertEqual(self.deriv_obj.dim, self.dim)


class PhysDerivTestCase(InfiniteDiffTestCase):
    _DERIV_CLS = PhysDeriv
    _CYCLIC = False
    _COORD_KWARGS = dict(cyclic=_CYCLIC)

    def setUp(self):
        super(PhysDerivTestCase, self).setUp()
        self.dim = LAT_STR
        self.arr = xr.DataArray(np.random.random(self.lat.shape),
                                dims=self.lat.dims, coords=self.lat.coords)
        self.deriv_obj = self._DERIV_CLS(self.arr, self.dim,
                                         **self._COORD_KWARGS)


class TestPhysDeriv(PhysDerivSharedTests, PhysDerivTestCase):
    def test_deriv(self):
        self.assertNotImplemented(self.deriv_obj.deriv)


def _test_wrap_not_cyclic(obj, order):
    deriv_obj = obj._DERIV_CLS(obj.arr, obj.dim, order=order, cyclic=False)
    actual = deriv_obj._wrap(obj.arr)
    desired = obj.arr
    obj.assertDatasetIdentical(actual, desired)


def _test_wrap_cyclic(obj, order):
    deriv_obj = obj._DERIV_CLS(obj.arr, obj.dim, order=order, cyclic=True)
    actual = deriv_obj._wrap(obj.arr)
    desired = wraparound(
        obj.arr, obj.dim, circumf=obj._DERIV_CLS._WRAP_CIRCUMF,
        left_to_right=obj._DERIV_CLS._WRAP_LEFT_TO_RIGHT*order,
        right_to_left=obj._DERIV_CLS._WRAP_RIGHT_TO_LEFT*order
    )
    obj.assertDatasetIdentical(actual, desired)


class LonDerivTestCase(PhysDerivTestCase):
    _DERIV_CLS = LonDeriv
    _CYCLIC = True
    _COORD_KWARGS = dict(cyclic=_CYCLIC)

    def setUp(self):
        super(LonDerivTestCase, self).setUp()
        self.dim = LON_STR
        self.arr = xr.DataArray(np.random.random(self.lon.shape),
                                dims=self.lon.dims, coords=self.lon.coords)
        self.deriv_obj = self._DERIV_CLS(self.arr, self.dim,
                                         **self._COORD_KWARGS)


class TestLonDeriv(PhysDerivSharedTests, LonDerivTestCase):
    def test_deriv(self):
        self.assertNotImplemented(self.deriv_obj.deriv, 1)

    def test_wrap_cyclic(self):
        for order in [1, 2]:
            _test_wrap_cyclic(self, order)

    def test_wrap_not_cyclic(self):
        for order in [1, 2]:
            _test_wrap_not_cyclic(self, order)


class LonFwdDerivTestCase(LonDerivTestCase):
    _DERIV_CLS = LonFwdDeriv

    def setUp(self):
        super(LonFwdDerivTestCase, self).setUp()
        self.arr = xr.DataArray(
            np.random.random((self.lat.size, self.lon.size)),
            dims=[LAT_STR, LON_STR],
            coords={LON_STR: self.lon, LAT_STR: self.lat}
        )
        self.arr2 = xr.DataArray(np.random.random(self.lon.shape),
                                 dims=self.lon.dims, coords=self.lon.coords)
        self.zeros = xr.DataArray(np.zeros(self.arr.shape), dims=self.arr.dims,
                                  coords=self.arr.coords)
        self.ones = xr.DataArray(np.ones(self.arr.shape), dims=self.arr.dims,
                                 coords=self.arr.coords)
        self.deriv_obj = self._DERIV_CLS(self.arr, self.dim,
                                         **self._COORD_KWARGS)


class TestLonFwdDeriv(TestLonDeriv, LonFwdDerivTestCase):
    def test_init(self):
        for cyclic in [True, False]:
            deriv_obj = self._DERIV_CLS(self.arr, self.dim, cyclic=cyclic,
                                        fill_edge=True)
            self.assertEqual(deriv_obj.cyclic, cyclic)
            self.assertEqual(deriv_obj.fill_edge, not cyclic)

    def test_deriv(self):
        self.deriv_obj.deriv(0.)
        self.deriv_obj.deriv(self.lat)

    def test_deriv_output_coords(self):
        # Scalar latitude.
        deriv_obj = self._DERIV_CLS(self.arr2, self.dim, cyclic=True)
        actual = deriv_obj.deriv(0.)
        desired = self.arr2
        self.assertCoordsIdentical(actual, desired)
        # Array of latitudes.
        actual = self.deriv_obj.deriv(self.lat)
        desired = self.arr
        self.assertCoordsIdentical(actual, desired)
        # With extra, non-lat, non-lon dimension.
        arr = xr.DataArray(
            np.random.random((self.pfull.size, self.lat.size, self.lon.size)),
            dims=[PFULL_STR, LAT_STR, LON_STR],
            coords={PFULL_STR: self.pfull, LON_STR: self.lon,
                    LAT_STR: self.lat}
        )
        deriv_obj = self._DERIV_CLS(arr, self.dim, cyclic=True)
        actual = deriv_obj.deriv(self.lat)
        desired = arr
        self.assertCoordsIdentical(actual, desired)

    def test_deriv_output_coords_not_cyclic(self):
        # Scalar latitude.
        actual = self._DERIV_CLS(self.arr2, self.dim, cyclic=False,
                                 fill_edge=True).deriv(0.)
        desired = self.arr2
        self.assertCoordsIdentical(actual, desired)
        # Array of latitudes.
        actual = self._DERIV_CLS(self.arr, self.dim, cyclic=False,
                                 fill_edge=True).deriv(self.lat)
        desired = self.arr
        self.assertCoordsIdentical(actual, desired)

    def test_deriv_zero_slope(self):
        desired = self.zeros
        for o in [1, 2]:
            actual = self._DERIV_CLS(self.ones, self.dim, order=o,
                                     cyclic=True).deriv(0.)
        self.assertDatasetIdentical(actual, desired)


class LonBwdDerivTestCase(LonFwdDerivTestCase):
    _DERIV_CLS = LonBwdDeriv


class TestLonBwdDeriv(TestLonFwdDeriv, LonBwdDerivTestCase):
    pass


class LatDerivTestCase(PhysDerivTestCase):
    _DERIV_CLS = LatDeriv
    _COORD_KWARGS = dict(fill_edge=True)

    def setUp(self):
        super(LatDerivTestCase, self).setUp()
        self.dim = LAT_STR
        self.arr = xr.DataArray(np.random.random(self.lat.shape),
                                dims=self.dim, coords={self.dim: self.lat})
        self.arr2 = xr.DataArray(
            np.random.random((self.lat.size, self.lon.size)),
            dims=[LAT_STR, LON_STR],
            coords={LON_STR: self.lon, LAT_STR: self.lat}
        )
        self.zeros = xr.DataArray(np.zeros(self.arr.shape), dims=self.arr.dims,
                                  coords=self.arr.coords)
        self.ones = xr.DataArray(np.ones(self.arr.shape), dims=self.arr.dims,
                                 coords=self.arr.coords)
        self.deriv_obj = self._DERIV_CLS(self.arr, self.dim,
                                         **self._COORD_KWARGS)


class TestLatDeriv(PhysDerivSharedTests, LatDerivTestCase):
    def test_deriv(self):
        self.assertNotImplemented(self.deriv_obj.deriv, 'divg')

    def test_wrap(self):
        desired = self.arr
        for order in [1, 2]:
            deriv_obj = self._DERIV_CLS(self.arr, self.dim, order=order)
            actual = deriv_obj._wrap(self.arr)
            self.assertDatasetIdentical(actual, desired)


class LatFwdDerivTestCase(LatDerivTestCase):
    _DERIV_CLS = LatFwdDeriv
    _CYCLIC = False

    def setUp(self):
        super(LatFwdDerivTestCase, self).setUp()
        self.dim = LAT_STR
        self.arr = xr.DataArray(np.random.random(self.lat.shape),
                                dims=self.dim, coords={self.dim: self.lat})
        self.arr2 = xr.DataArray(
            np.random.random((self.lat.size, self.lon.size)),
            dims=[LAT_STR, LON_STR],
            coords={LON_STR: self.lon, LAT_STR: self.lat}
        )
        self.deriv_obj = self._DERIV_CLS(self.arr, self.dim,
                                         **self._COORD_KWARGS)


class TestLatFwdDeriv(PhysDerivSharedTests, LatFwdDerivTestCase):
    def test_deriv_output_coords(self):
        for oper in ['grad', 'divg']:
            # Scalar latitude
            actual = self.deriv_obj.deriv(oper=oper)
            desired = self.deriv_obj.arr
            self.assertCoordsIdentical(actual, desired)
            # Array of latitudes.
            deriv_obj = self._DERIV_CLS(self.arr2, self.dim,
                                        **self._COORD_KWARGS)
            actual = deriv_obj.deriv(oper=oper)
            desired = self.arr2
            self.assertCoordsIdentical(actual, desired)

        # With extra, non-lat, non-lon dimension.
        arr = xr.DataArray(
            np.random.random((self.pfull.size, self.lat.size, self.lon.size)),
            dims=[PFULL_STR, LAT_STR, LON_STR],
            coords={PFULL_STR: self.pfull, LON_STR: self.lon,
                    LAT_STR: self.lat}
        )
        deriv_obj = self._DERIV_CLS(arr, self.dim, fill_edge=True)
        desired = arr
        for oper in ['grad', 'divg']:
            actual = deriv_obj.deriv(oper=oper)
            self.assertCoordsIdentical(actual, desired)

    def test_deriv_zero_slope(self):
        desired = self.zeros
        for o in [1, 2]:
            actual = self._DERIV_CLS(self.ones, self.dim, order=o).deriv()
        self.assertDatasetIdentical(actual, desired)


class LatBwdDerivTestCase(LatFwdDerivTestCase):
    _DERIV_CLS = LatBwdDeriv


class TestLatBwdDeriv(TestLatFwdDeriv, LatBwdDerivTestCase):
    pass


class SphereFwdDerivTestCase(InfiniteDiffTestCase):
    _DERIV_CLS = SphereFwdDeriv

    def setUp(self):
        super(SphereFwdDerivTestCase, self).setUp()
        self.arr = xr.DataArray(
            np.random.random((len(self.pfull), len(self.lat), len(self.lon))),
            dims=[PFULL_STR, LAT_STR, LON_STR],
            coords={PFULL_STR: self.pfull, LAT_STR: self.lat,
                    LON_STR: self.lon}
        )
        self.zeros = xr.DataArray(np.zeros(self.arr.shape), dims=self.arr.dims,
                                  coords=self.arr.coords)
        self.ones = xr.DataArray(np.ones(self.arr.shape), dims=self.arr.dims,
                                 coords=self.arr.coords)
        self.deriv_obj = self._DERIV_CLS(self.arr)


class TestSphereFwdDeriv(PhysDerivSharedTests, SphereFwdDerivTestCase):
    def test_init(self):
        self.assertDatasetIdentical(self.deriv_obj.arr, self.arr)

    def test_deriv(self):
        self.deriv_obj.d_dx()
        self.deriv_obj.d_dy()
        self.deriv_obj.horiz_grad()

    def test_deriv_coords(self):
        desired = self.arr
        for deriv in ['d_dx', 'd_dy']:
            for o in [1, 2]:
                deriv_obj = self._DERIV_CLS(self.arr, order=o, cyclic_lon=True,
                                            fill_edge_lat=True)
                actual = getattr(deriv_obj, deriv)()
                self.assertCoordsIdentical(actual, desired)

    def test_deriv_zero_slope(self):
        desired = self.zeros
        for deriv in ['d_dx', 'd_dy']:
            for o in [1, 2]:
                deriv_obj = self._DERIV_CLS(self.ones, order=o,
                                            cyclic_lon=True,
                                            fill_edge_lat=True)
                actual = getattr(deriv_obj, deriv)()
                self.assertDatasetIdentical(actual, desired)


class SphereBwdDerivTestCase(SphereFwdDerivTestCase):
    _DERIV_CLS = SphereBwdDeriv


class TestSphereBwdDeriv(TestSphereFwdDeriv, SphereBwdDerivTestCase):
    pass


class EtaFwdDerivTestCase(InfiniteDiffTestCase):
    _DERIV_CLS = EtaFwdDeriv

    def setUp(self):
        super(EtaFwdDerivTestCase, self).setUp()
        self.dim = PFULL_STR
        self.arr = xr.DataArray(np.random.random(self.pfull.shape),
                                dims=self.dim, coords={self.dim: self.pfull})
        self.zeros = xr.DataArray(np.zeros(self.pfull.shape),
                                  dims=self.arr.dims, coords=self.arr.coords)
        self.ones = xr.DataArray(np.ones(self.pfull.shape),
                                 dims=self.arr.dims, coords=self.arr.coords)
        self.ps = 1e5
        self.deriv_obj = self._DERIV_CLS(self.arr, self.pk, self.bk, self.ps,
                                         order=2, fill_edge=True)


class TestEtaFwdDeriv(PhysDerivSharedTests, EtaFwdDerivTestCase):
    def test_deriv(self):
        self.deriv_obj.deriv()

    def test_deriv_output_coords_fill(self):
        desired = self.arr
        for o in [1, 2]:
            actual = self._DERIV_CLS(self.arr, self.pk, self.bk, self.ps,
                                     order=o, fill_edge=True).deriv()
        self.assertCoordsIdentical(actual, desired)

    def test_deriv_zero_slope(self):
        desired = self.zeros
        for o in [1, 2]:
            actual = self._DERIV_CLS(self.ones, self.pk, self.bk, self.ps,
                                     order=o, fill_edge=True).deriv()
        self.assertDatasetIdentical(actual, desired)


class EtaBwdDerivTestCase(EtaFwdDerivTestCase):
    _DERIV_CLS = EtaBwdDeriv


class TestEtaBwdDeriv(TestEtaFwdDeriv, EtaBwdDerivTestCase):
    pass


class SphereEtaDerivTestCase(InfiniteDiffTestCase):
    _DERIV_CLS = SphereEtaDeriv

    def setUp(self):
        super(SphereEtaDerivTestCase, self).setUp()
        self.arr = xr.DataArray(
            np.random.random((len(self.pfull), len(self.lat), len(self.lon))),
            dims=[PFULL_STR, LAT_STR, LON_STR],
            coords={PFULL_STR: self.pfull, LAT_STR: self.lat,
                    LON_STR: self.lon}
        )
        self.ps = xr.DataArray(
            np.random.random((len(self.lat), len(self.lon))),
            dims=[LAT_STR, LON_STR],
            coords={LAT_STR: self.lat, LON_STR: self.lon}
        )*1e3 + 1e5

        self.deriv_obj = self._DERIV_CLS(self.arr, self.pk, self.bk, self.ps)


class TestSphereEtaDeriv(PhysDerivSharedTests, SphereEtaDerivTestCase):
    def test_init(self):
        self.assertDatasetIdentical(self.deriv_obj.arr, self.arr)

    def test_deriv(self):
        self.assertNotImplemented(self.deriv_obj.d_dx)
        self.assertNotImplemented(self.deriv_obj.d_dy, 'divg')


class SphereEtaFwdDerivTestCase(SphereEtaDerivTestCase):
    _DERIV_CLS = SphereEtaFwdDeriv
    _SPHERE_CLS = SphereFwdDeriv


class TestSphereEtaFwdDeriv(TestSphereEtaDeriv, SphereEtaFwdDerivTestCase):
    def test_deriv(self):
        self.deriv_obj.d_dx()
        self.deriv_obj.d_dy()
        self.deriv_obj.horiz_grad()

    def test_deriv_const_p(self):
        self.deriv_obj.d_dx_const_p()
        self.deriv_obj.d_dy_const_p()
        self.deriv_obj.horiz_grad_const_p()

    def test_deriv_output_coords(self):
        desired = self.arr
        for deriv in ['d_dx', 'd_dy', 'd_dx_const_p', 'd_dy_const_p']:
            for o in [1, 2]:
                deriv_obj = self._DERIV_CLS(self.arr, self.pk, self.bk,
                                            self.ps, order=o,
                                            fill_edge_lat=True)
                actual = getattr(deriv_obj, deriv)()
                self.assertCoordsIdentical(actual, desired)

    def test_deriv_uniform_ps(self):
        ps = self.ps.copy()
        ps.values = 1e5*np.ones(self.ps.shape)
        sphere_eta_obj = self._DERIV_CLS(self.arr, self.pk, self.bk, ps,
                                         order=1, fill_edge_lat=True)
        sphere_obj = self._SPHERE_CLS(self.arr, order=1)
        derivs = ['d_dx', 'd_dy', 'horiz_grad']
        derivs_p = [d + '_const_p' for d in derivs]
        for deriv, deriv_p in zip(derivs, derivs_p):
            self.assertDatasetIdentical(getattr(sphere_eta_obj, deriv_p)(),
                                        getattr(sphere_obj, deriv)())


class SphereEtaBwdDerivTestCase(SphereEtaDerivTestCase):
    _DERIV_CLS = SphereEtaBwdDeriv
    _SPHERE_CLS = SphereBwdDeriv


class TestSphereEtaBwdDeriv(TestSphereEtaFwdDeriv, SphereEtaBwdDerivTestCase):
    pass


if __name__ == '__main__':
    sys.exit(unittest.main())
