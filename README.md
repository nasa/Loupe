# Loupe
Copyright 2022, by the California Institute of Technology. ALL RIGHTS RESERVED

SHERLOC Raman and fluorescence spectroscopy visualization tool


### Description:
Loupe is a modular, interactive environment to visualize, process, and analyze SHERLOC Raman and fluorescence spectroscopy data. Loupe relies on the [SPAR](https://github.com/NASA-AMMOS/SPAR) library. SPAR is the SOFF PDS4 Array Reader, which reads data files in the PDS that are described by a SOFF (Spectrometer Open File Format) manifest file. SOFF files may be generated manually, or using the SOFF write features in a future version of the SPAR library.


### Features:

#### Main tab
The main tab presents SHERLOC hypserpectral data co-registered with ACI context images. Users can define workspaces, select individual points within a map to display, compare SHERLOC CCD regions, toggle processing steps, and define regions of interest. Metadata associated with each measurement is also displayed in tables on the left pane.
<img width="1762" alt="MainTab" src="https://user-images.githubusercontent.com/98192066/189041451-cd64873a-5616-474d-889b-ec70760d1670.png">

#### Cosmic Ray Removal Tab:
The cosmic ray removal tab enables a user to de-noise a hyperspectral dataset workspace using the automated technique described in Uckert et. al (2019), or by manually removing individual cosmic rays. Cosmic rays may be replaced using an average or interpolation of intensity values of nearby neighboring channels.

#### Laser Normalization Tab:
The laser normalization tab displays the SHERLOC laser photodiode intensity map, along with the laser photodiode statistics. The laser normalization function corrects the intensity of each spectral point to account for variability in laser intensity at the surface.

#### False Color Map Tab:
The false color map tab contains interactive tools to display RGB maps of spectral regions of interest, superimposed on the ACI context image to reveal spectral variability.
<img width="1762" alt="FalseColorMapTab" src="https://user-images.githubusercontent.com/98192066/189041495-93e65af2-f7ac-41e8-9917-20629d53e9d3.png">

### References:
- **SHERLOC**: Bhartia, R., Beegle, L. W., DeFlores, L., Abbey, W., Hollis, J. R., Uckert, K., ... & Zan, J. (2021). [Perseverance’s Scanning Habitable Environments with Raman and Luminescence for Organics and Chemicals (SHERLOC) investigation](https://link.springer.com/article/10.1007/s11214-021-00812-z). Space Science Reviews, 217(4), 1-115.
- **Cosmic Ray Removal**: Uckert, Kyle, Rohit Bhartia, and John Michel. (2019). [A semi-autonomous method to detect cosmic rays in Raman hyperspectral data sets.](https://journals.sagepub.com/doi/full/10.1177/0003702819850584) Applied Spectroscopy 73.9, 1019-1027.
- **SOFF**: Uckert, K., & Deen, R. G. (2020, December). [Spectrometer Open File Format](https://ui.adsabs.harvard.edu/abs/2020AGUFMGC0220016U/abstract). In AGU Fall Meeting Abstracts (Vol. 2020, pp. GC022-0016).
- **Loupe**: *in preparation*
