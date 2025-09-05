import io
import logging
from pathlib import Path
from typing import TYPE_CHECKING, List

from . import min_grib, common

if TYPE_CHECKING:
    import arkimet

log = logging.getLogger("arkimet")


def minimize_arkimet(path: Path, idx: int, md: "arkimet.Metadata") -> bytes:
    """
    Given an Arkimet metadata, return its serialized version after minimizing
    the GRIB data in it
    """
    # Get data
    data = md.data

    fmt = md.to_python("source")["format"]
    if fmt == "grib":
        # Replace its values with zeroes
        minimized = min_grib.minimize_grib_message(data)
    else:
        log.info(
            "%s:%d: unknown/unsupported format %s: leaving as it is",
            path,
            idx,
            fmt,
        )
        minimized = md.data

    # Check if result is smaller than original.
    # If smaller, overwrite; else, leave as is.
    if len(minimized) < len(data):
        log.debug(
            "%s:%d: GRIB minimized: %db → %db",
            path,
            idx,
            len(data),
            len(minimized),
        )

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
    def __init__(self, path: Path) -> None:
        super().__init__(path)
        try:
            __import__("arkimet")
        except ModuleNotFoundError:
            raise common.BackendUnavailable(
                "arkimet python module is not installed"
            )

    def make_new_contents(self) -> List[bytes]:
        # Import here to avoid depending on arkimet for other unrelated features
        import arkimet

        # Read arkimet metadata
        with self.path.open("rb") as fd:
            mds = arkimet.Metadata.read_bundle(fd, pathname=self.path)

        # Minimize storing the resulting binary chunks in a list
        new_contents: List[bytes] = []
        for idx, md in enumerate(mds, start=1):
            log.debug("%s:%d: minimizing data", self.path, idx)
            new_contents.append(minimize_arkimet(self.path, idx, md))

        return new_contents
