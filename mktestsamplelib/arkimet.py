from __future__ import annotations
import io
import logging
from typing import TYPE_CHECKING, List

from . import grib, common

if TYPE_CHECKING:
    import arkimet

log = logging.getLogger("arkimet")


def minimize_arkimet(fname: str, idx: int, md: "arkimet.Metadata") -> bytes:
    """
    Given an Arkimet metadata, return its serialized version after minimizing
    the GRIB data in it
    """
    # Get data
    data = md.data

    # Replace its values with zeroes
    minimized = grib.minimize_grib_message(data)

    # Check if result is smaller than original.
    # If smaller, overwrite; else, leave as is.
    if len(minimized) < len(data):
        log.info("%s:%d: GRIB minimized: %db → %db", fname, idx, len(data), len(minimized))

        # Replace data size size in inline metadata
        source = md.to_python("source")
        source["size"] = len(minimized)
        md["source"] = source

        # Serialize the new metadata + data
        with io.BytesIO() as tf:
            # Note:
            #
            # There is no way to replace data in an arkimet metadata and it
            # makes sense, since for arkimet data is immutable. The kind of
            # mangling we do here is not something to have in arkimet, as it
            # breaks its invariants.
            #
            # We can work around this with knowledge of the arkimet metadata
            # stream. When using inline data, arkimet simply serializes the
            # metadata, and then adds source.size bytes of data.
            #
            # We can then:
            #  1. write out the modified metadata, with a special request to
            #     skip writing the data afterwards
            #  2. Append our own data

            # Write the new metadata followed by the original data
            md.write(tf, skip_data=True)

            # Write the new data
            tf.write(minimized)

            # Read the contents of the new file
            return tf.getvalue()
    else:
        # Serialize the old data, unchanged
        with io.BytesIO() as tf:
            md.write(tf)
            return tf.getvalue()


class MinimizeArkimet(common.MinimizeFile):
    def make_new_contents(self) -> List[bytes]:
        # Read arkimet metadata
        with open(self.fname, "rb") as fd:
            mds = arkimet.Metadata.read_bundle(fd, pathname=self.fname)

        # Minimize storing the resulting binary chunks in a list
        new_contents: List[bytes] = []
        for idx, md in enumerate(mds, start=1):
            log.debug("%s:%d: minimizing data", self.fname, idx)
            new_contents.append(minimize_arkimet(self.fname, idx, md))

        return new_contents
