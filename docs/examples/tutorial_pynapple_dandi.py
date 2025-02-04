# coding: utf-8
"""
Streaming data from Dandi
=========================

This script shows how to stream data from the [dandi archive](https://dandiarchive.org/) all the way to pynapple.

> Warning **This tutorial is still under construction.**

"""
# %%
# !!! warning
#     This tutorial uses seaborn and matplotlib for displaying the figure as well as the dandi package
#
#     You can install all with `pip install matplotlib seaborn dandi dandischema`

# %%
# ***
# Prelude
# -------
#
# The data used in this tutorial are hosted by the [DANDI](https://dandiarchive.org/dandiset/000582?search=sargolini&pos=1) archive and were used in this publication:
# __Sargolini, Francesca, et al. "Conjunctive representation of position, direction, and velocity in entorhinal cortex." Science 312.5774 (2006): 758-762.__
#
# mkdocs_gallery_thumbnail_number = 2

# %%
# ***
# Dandi
# -----
# Dandi allows you to stream data without downloading all the files. In this case the data extracted from the NWB file are stored in the nwb-cache folder.

from pynwb import NWBHDF5IO

from dandi.dandiapi import DandiAPIClient
import fsspec
from fsspec.implementations.cached import CachingFileSystem
import h5py


# ecephys
dandiset_id, filepath = (
    "000582",
    "sub-10073/sub-10073_ses-17010302_behavior+ecephys.nwb",
)


with DandiAPIClient() as client:
    asset = client.get_dandiset(dandiset_id, "draft").get_asset_by_path(filepath)
    s3_url = asset.get_content_url(follow_redirects=1, strip_query=True)

# first, create a virtual filesystem based on the http protocol
fs = fsspec.filesystem("http")

# create a cache to save downloaded data to disk (optional)
fs = CachingFileSystem(
    fs=fs,
    cache_storage="nwb-cache",  # Local folder for the cache
)

# next, open the file
file = h5py.File(fs.open(s3_url, "rb"))
io = NWBHDF5IO(file=file, load_namespaces=True)

print(io)

# %%
# Pynapple
# --------
# If opening the NWB works, you can start streaming data straight into pynapple with the `NWBFile` class.

import pynapple as nap
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

custom_params = {"axes.spines.right": False, "axes.spines.top": False}
sns.set_theme(style="ticks", palette="colorblind", font_scale=1.5, rc=custom_params)

nwb = nap.NWBFile(io.read())

print(nwb)


# %%
# We can load the spikes as a TsGroup for inspection.

units = nwb["units"]

print(units)


# %%
# As well as the position
position = nwb["SpatialSeriesLED1"]


# %%
# Here we compute the 2d tuning curves
tc, binsxy = nap.compute_2d_tuning_curves(units, position, 20)


# %%
# Let's plot the tuning curves

plt.figure(figsize=(15, 7))
for i in tc.keys():
    plt.subplot(2, 4, i + 1)
    plt.imshow(tc[i], origin="lower", aspect="auto")
    plt.title("Unit {}".format(i))
plt.tight_layout()
plt.show()


# %%
# Let's plot the spikes of unit 1 who has a nice grid
# Here I use the function `value_from` to assing to each spike the closest position in time.


plt.figure(figsize=(15, 6))
plt.subplot(121)
extent = (
    position["x"].min(),
    position["x"].max(),
    position["y"].min(),
    position["y"].max(),
)
plt.imshow(tc[1], origin="lower", extent=extent, aspect="auto")
plt.xlabel("x")
plt.ylabel("y")

plt.subplot(122)
plt.plot(position["y"], position["x"], color="grey")
spk_pos = units[1].value_from(position)
plt.plot(spk_pos["y"], spk_pos["x"], "o", color="red", markersize=5, alpha=0.5)
plt.xlabel("x")
plt.ylabel("y")
plt.tight_layout()
plt.show()
