from __future__ import annotations
import logging
from typing import BinaryIO, Sequence, List

from . import common

log = logging.getLogger("grib")

# In case we are going to need to minimize GRIBs preserving some aspects of the
# data, tip from @dcesari:
#
# Non so se può servire, il comando di libsim:
#
# vg6d_transform [--trans-mode=s] --trans-type=boxregrid --sub-type=average \
#  --npx=4 --npy=4 gribin gribout
#
# trasforma un grib facendo la media su blocchi di 4x4 punti (ovviamente si
# possono usare altri valori), per cui può essere utile per ridurre la
# risoluzione e quindi le dimensioni di un messaggio senza ridurne
# significativamente l'area geografica e mantenendo un contenuto informativo
# ragionevole, nel caso serva avere dei numeri veri che occupano poco spazio.


def replace_data(gid: int):
    """
    Replace all data in an eccodes GRIB handle with zeroes
    """
    # Import here to avoid depending on eccodes for other unrelated features
    import eccodes
    import numpy

    values = eccodes.codes_get_values(gid)
    zeros = numpy.zeros(values.shape)
    eccodes.codes_set_values(gid, zeros)


def minimize_grib_message(data: bytes) -> bytes:
    """
    Given GRIB data, return its version after setting values to all zeroes
    """
    # Import here to avoid depending on eccodes for other unrelated features
    import eccodes

    gid = eccodes.codes_new_from_message(data)
    try:
        replace_data(gid)

        return eccodes.codes_get_message(gid)
    finally:
        eccodes.codes_release(gid)


def iter_grib_file(fd: BinaryIO) -> Sequence[int]:
    """
    Iterate the contents of a GRIB file, returning eccodes gids for each GRIB
    in the file.

    Each gid is properly deallocated after use
    """
    # Import here to avoid depending on eccodes for other unrelated features
    import eccodes

    while True:
        gid = eccodes.codes_grib_new_from_file(fd)
        if gid is None:
            break
        try:
            yield gid
        finally:
            eccodes.codes_release(gid)


class MinimizeGRIB(common.MinimizeFile):
    def make_new_contents(self) -> List[bytes]:
        # Import here to avoid depending on eccodes for other unrelated features
        import eccodes

        # Read GRIB contents, computing minified versions
        new_contents = []
        with open(self.fname, "rb") as fd:
            for gid in iter_grib_file(fd):
                replace_data(gid)
                new_contents.append(eccodes.codes_get_message(gid))

        return new_contents
