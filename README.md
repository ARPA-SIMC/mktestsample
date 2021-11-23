# mktestsample

Create a small test sample out of a bigger file.

This is very useful to create test cases for code that needs to work with file
metadata.

The idea is to zero out matrices in scientific data files, or blank out images,
so that compression, whether inherent in the file format or otherwise, can
reduce large files to a few hundred of bytes.


## Usage

```
$ mktestsample --help
usage: mktestsample [-h] [-v] [--debug] [-c] files [files ...]

Replace data in sample files with zeroes, to be used as test data without bloating code repositories

positional arguments:
  files          files to minimize

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  verbose output
  --debug        verbose output
  -c, --check    don't replace files, only check what would be done
```


## Formats supported

* [GRIB](https://en.wikipedia.org/wiki/GRIB) via [ecCodes](https://confluence.ecmwf.int/display/ECC/ecCodes+Home)
* [arkimet](https://github.com/ARPA-SIMC/arkimet) metadata with inline data
* JPEG via [PIL](https://pypi.org/project/Pillow/). JPEG cannot produce very
  small files even with blank images, but normal compressors will reduce the
  generated files immensely.
