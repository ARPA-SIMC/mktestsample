from __future__ import annotations
import logging
import os
from typing import List

log = logging.getLogger("common")


class MinimizeFile:
    """
    Base class for format-dependent file minimization implementations.
    """

    def __init__(self, fname: str):
        self.fname = fname

    def minimize(self):
        """
        Replace the contents of the file with their minimized versions.

        Works on the file in-place, replacing it if the contents became smaller
        after minimization
        """
        log.debug("%s: minimizing file", self.fname)
        orig_st = os.stat(self.fname)
        orig_size = orig_st.st_size

        # Read arkimet metadata
        new_contents = self.make_new_contents()

        # If everthing went well so far, we can rewrite the original file
        new_size = sum(len(c) for c in new_contents)
        if orig_size == new_size:
            log.info("%s: size unchanged: leaving original file unchanged", self.fname)
        elif orig_size < new_size:
            log.error("%s: minimized size would go from %db to %db: bug? Leaving original file unchanged",
                      self.fname, orig_size, new_size)
        else:
            log.info("%s: size went from %db to %db", self.fname, orig_size, new_size)
            with open(self.fname, "wb") as fd:
                for c in new_contents:
                    fd.write(c)
            # Restore original modification times
            os.utime(self.fname, ns=(orig_st.st_atime_ns, orig_st.st_mtime_ns))

    def make_new_contents(self) -> List[bytes]:
        """
        Calculate the new, minimized contents for the file
        """
        raise NotImplementedError(f"{self.__class__}.make_new_contents() not implemented")
