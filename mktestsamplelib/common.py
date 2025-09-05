import logging
import os
from pathlib import Path
from typing import List, Optional

log = logging.getLogger("common")


class BackendUnavailable(Exception):
    """Excpetion raised when a minimizer backend is not installed."""


class MinimizeFile:
    """
    Base class for format-dependent file minimization implementations.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.orig_st = self.path.stat()

    @classmethod
    def for_path(cls, path: Path) -> Optional["MinimizeFile"]:
        """Instantiate a MinimizeFile for a Path."""
        match path.suffix:
            case ".arkimet":
                from .min_arkimet import MinimizeArkimet

                return MinimizeArkimet(path)
            case ".grib":
                from .min_grib import MinimizeGRIB

                return MinimizeGRIB(path)
            case ".jpg" | ".jpeg":
                from .min_jpeg import MinimizeJPEG

                return MinimizeJPEG(path)
            case ".nc" | ".netcdf":
                from .min_netcdf import MinimizeNetCDF

                return MinimizeNetCDF(path)
            case _:
                return None

    def compute(self) -> Optional[List[bytes]]:
        """
        Scan the file and compute its minimized contents.

        If the return value is None, it means no minimization happened.
        """
        log.debug("%s: minimizing file", self.path)
        orig_size = self.orig_st.st_size

        # Read arkimet metadata
        new_contents = self.make_new_contents()

        # If everthing went well so far, we can rewrite the original file
        new_size = sum(len(c) for c in new_contents)
        if orig_size == new_size:
            log.info(
                "%s: size unchanged: leaving original file unchanged",
                self.path,
            )
            return None
        elif orig_size < new_size:
            log.error(
                "%s: minimized size would go from %db to %db: bug?"
                " Leaving original file unchanged",
                self.path,
                orig_size,
                new_size,
            )
            return None
        else:
            log.info(
                "%s: size went from %db to %db", self.path, orig_size, new_size
            )
            return new_contents

    def write(self, new_contents: List[bytes]):
        """
        Replace the file with its new contents
        """
        with open(self.path, "wb") as fd:
            for c in new_contents:
                fd.write(c)
        # Restore original modification times
        os.utime(
            self.path, ns=(self.orig_st.st_atime_ns, self.orig_st.st_mtime_ns)
        )

    def minimize(self):
        """
        Scan the file, and if the minimized contents are smaller than its
        current size, replace it
        """
        new_contents = self.compute()
        if new_contents is not None:
            self.write(new_contents)

    def check(self):
        """
        Read-only version of minimize()
        """
        self.compute()

    def make_new_contents(self) -> List[bytes]:
        """
        Calculate the new, minimized contents for the file
        """
        raise NotImplementedError(
            f"{self.__class__}.make_new_contents() not implemented"
        )
