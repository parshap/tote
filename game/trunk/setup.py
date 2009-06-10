from distutils.core import setup
import py2exe

setup(
    console=['main.py'],
    options = {
        "py2exe": {
            "dll_excludes": [
                "MSVCP90.dll",
                "MSVCR90.dll",
                "boost_python-vc90-mt-1_37.dll"
            ]
        }
    }
)