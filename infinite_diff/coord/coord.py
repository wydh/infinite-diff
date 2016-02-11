"""Generic coordinates."""


class Coord(object):
    def _prep_dim(self, dim):
        msg = ("Specified dim '{}' does not match any dim in self._arr.\n"
               "self._arr.dims: {}").format(dim, self._arr.dims)
        if dim in self._arr.dims:
            return dim
        if dim is None:
            if self._arr.shape == 1:
                return self._arr.dims[0]
        raise ValueError(msg)

    def __init__(self, arr, dim=None, cyclic=False):
        self._arr = arr
        self._dim = self._prep_dim(dim)
        self._cyclic = cyclic

    def __getitem__(self, key):
        return self._arr[key]

    def deriv_prefactor(self, *args, **kwargs):
        raise NotImplementedError

    def deriv_factor(self, *args, **kwargs):
        raise NotImplementedError
