import subprocess
import tempfile
import logging
from pathlib import Path
from typing import TYPE_CHECKING, List
import shutil

from . import common

if TYPE_CHECKING:
    import netCDF4 as nc

log = logging.getLogger("arkimet")

#     # Check if result is smaller than original.
#     # If smaller, overwrite; else, leave as is.
#     if len(minimized) < len(data):
#         log.debug(
#             "%s:%d: GRIB minimized: %db → %db",
#             path,
#             idx,
#             len(data),
#             len(minimized),
#         )


class MinimizeNetCDF(common.MinimizeFile):
    def __init__(self, path: Path) -> None:
        super().__init__(path)
        try:
            __import__("netCDF4")
        except ModuleNotFoundError:
            raise common.BackendUnavailable(
                "netCDF4 python module is not installed"
            )
        if (nccopy := shutil.which("nccopy")) is None:
            raise common.BackendUnavailable("nccopy not found in path")
        self.nccopy = nccopy

    def make_new_contents(self) -> List[bytes]:
        # Import here as it is an optional dependency
        import netCDF4 as nc

        # Make a copy of the file before minimizing it, and work on the copy
        with tempfile.NamedTemporaryFile(
            dir=self.path.parent, prefix=self.path.name
        ) as zeroed_file:
            zeroed = Path(zeroed_file.name)
            # Try to use reflink for the copy, if available, as it is a
            # significant speedup for large filefs
            subprocess.run(
                [
                    "cp",
                    "--reflink=auto",
                    self.path.as_posix(),
                    zeroed.as_posix(),
                ],
                check=True,
            )

            with nc.Dataset(zeroed, "r+") as root:
                self.minimize_tree(root)

            with tempfile.NamedTemporaryFile(
                dir=self.path.parent, prefix=self.path.name
            ) as compressed_file:
                compressed = Path(compressed_file.name)

                subprocess.run(
                    [
                        "nccopy",
                        "-d",
                        "9",
                        zeroed.as_posix(),
                        compressed.as_posix(),
                    ]
                )
                return [compressed.read_bytes()]

    def minimize_dataset(self, dataset: "nc.Dataset") -> None:
        log.debug("%s: checking dataset %s", self.path, dataset.name)
        for name, var in dataset.variables.items():
            if not var.shape:
                continue
            fill = var.get_fill_value()
            var[:] = fill
            log.debug(
                "%s: checking variable %s → %s %r fill:%r",
                self.path,
                dataset.name,
                name,
                var.shape,
                fill,
            )

    def minimize_tree(self, dataset: "nc.Dataset") -> None:
        self.minimize_dataset(dataset)
        for name, subgroup in dataset.groups.items():
            self.minimize_tree(subgroup)
