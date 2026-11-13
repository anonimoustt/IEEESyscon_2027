# Downloads the NOAA weather benchmark (Elwell and Polikar 2011) and checks both files by SHA256.
# Source: the public copy of Losing, Hammer, and Wersing (2016), https://github.com/vlosing/driftDatasets
# Usage: python download_weather.py [DATA_DIR]   (default DATA_DIR: data/weather)
import hashlib  # file checks
import os  # paths
import sys  # command line arguments
import urllib.request  # download

DATA_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join("data", "weather")  # target folder
URL = "https://raw.githubusercontent.com/vlosing/driftDatasets/master/realWorld/weather/"  # public copy
FILES = {  # file name and its SHA256 hash, as used for the paper
    "NEweather_data.csv": "e38ef95890ec0df3daee0493e92e59c38ae1c27cd01c4805367f189d52dfeed9",  # eight daily features
    "NEweather_class.csv": "90f39b754a9c95fc34047beb41752ebeb6fa1cde4e2d03fad3d3c5a46aee360f",  # rain label, 1 = rain
}  # end of the file list

os.makedirs(DATA_DIR, exist_ok=True)  # create the folder
for name, sha in FILES.items():  # each file
    path = os.path.join(DATA_DIR, name)  # local path
    if not os.path.exists(path):  # not downloaded yet
        print("downloading", name)  # progress
        urllib.request.urlretrieve(URL + name, path)  # download
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()  # hash of the local file
    if digest != sha:  # different file
        sys.exit("hash mismatch for %s: delete it and run again" % path)  # stop with a message
    n = sum(1 for _ in open(path))  # number of rows
    print("ok", path, n, "rows")  # 18159 rows expected
