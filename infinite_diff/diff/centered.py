"""Centered finite differencing."""
import xarray as xr

from . import FiniteDiff, BwdDiff, FwdDiff


class CenDiff(FiniteDiff):
    """Centered finite differencing."""
    def __init__(self, arr, dim):
        super(CenDiff, self).__init__(arr, dim)
        self._diff_bwd = BwdDiff(arr, dim).diff
        self._diff_fwd = FwdDiff(arr, dim).diff

    def _diff_edge(self, spacing=1, side='left'):
        """One-sided differencing of array edge."""
        if side == 'left':
            trunc = slice(0, spacing+1)
            method = self._diff_fwd
        elif side == 'right':
            trunc = slice(-(spacing+1), None)
            method = self._diff_bwd
        else:
            raise ValueError("Parameter `side` must be either 'left' "
                             "or 'right': {}").format(side)
        arr_edge = self._slice_arr_dim(trunc)
        return method(arr=arr_edge)

    # def _concat(self, left, center, right):

    def diff(self, arr=None, spacing=1, fill_edge=False):
        """Centered differencing of the DataArray or Dataset.

        :param fill_edge: Whether or not to fill in the edge cells
            that don't have the needed neighbor cells for the stencil.  If
            `True`, use one-sided differencing with the same order of accuracy
            as `order`, and the outputted array is the same shape as `arr`.

            If `'left'` or `'right'`, fill only that side.

            If `False`, the outputted array has a length in the computed axis
            reduced by `order`.
        """
        arr = self._find_arr(arr)
        self._check_spacing(spacing)
        self._check_arr_len(arr=arr, spacing=2*spacing, pad=1)

        left = self._slice_arr_dim(slice(0, -spacing))
        right = self._slice_arr_dim(slice(spacing, None))
        interior = (self._diff_fwd(arr=right, spacing=spacing) +
                    self._diff_bwd(arr=left, spacing=spacing))

        if fill_edge in ('left', 'both'):
            diff_left = self._diff_edge(side='left')
            interior = xr.concat([diff_left, interior], dim=self.dim)
        if fill_edge == ('right', 'both'):
            diff_right = self._diff_edge(side='right')
            interior = xr.concat([interior, diff_right], dim=self.dim)
        return interior