# SphereQuery

![example](screenshots/ESOQuery.png)

Package to browse and explore the ESO archive. This should be the equivalent of searching from the official raw [ESO archive](http://archive.eso.org/eso/eso_archive_main.html) but the results should be presented in a more comprehensible way.

Indeed, instead of having endless pages with one fits file per line, this package groups several fits files together, depending on the program ID and when the observations were taken. Therefore, at a quick glance, you can see how many times your favorite star has been observed with different instruments.

There is the possibility to query for the raw data or the phase 3 data.

## Query parameters

At the top of the window, you can see that there are a number of query parameters: all of them being optional. They should all be self explanatory but here is the list:

- Starname: stellar name, the program will try to resolve the name using Simbad
- Prog. ID: program ID from ESO
- DPR Tech: can take several values such as "POLARIMETRY,CORONOGRAPHY"
- Comb IFLT: filter used during the observations
- DROT2 MODE: pupil- or field-stabilized observations (ELEV or SKY, respectively)
- Start and End dates: query for a period of time

## Displaying results

Once the query is done, if there are some results, they will be displayed in a Table with the following columns:

- Downloaded: if you already downloaded the data (see next section for the download directory) there will be a round mark in this column. This is to avoid downloading the same dataset several times
- Simbad name: to avoid possible confusion with the name found in the fits file header, the package will always query Simbad to find the main identifier. This may sometimes slow down the display of information but will save time as you keep using it (see next section)
- OBJECT name: the name found in the header
- RA: mean value of the right ascension found in the header of the fits files
- Dec: same for the declination
- Program ID: taken from the headers, should be unique for each row
- OB ID: taken from the fits file, should be unique for each row, and this is how the different fits file are sorted
- Filter: filter used during the observations
- DROT: will show if this is pupil- or field-stabilized
- DIT: will show the DITs used in the sequence. There can be multiple values (e.g., for F, C, O, or S)
- Observing date: the dates of the fits file. There can be multiple dates if the observations was taken through midnight
- Release date: when the data will become public
- DPR Tech: will show the kind of observations
- Comments: if you double click on an entry, it will show a pop up window where you can add some comments.

## Preferences

Preferences can be accessed by clicking on the `Preferences` button in the upper right corner of the interface.

The package will create a directory in $HOME/.config/spherequery/, meaning that all preferences are stored locally and will stay on your computer. There should be at maximum three files that are saved there:

- spherequery.conf: where your login and password for the ESO archive are stored. Again, this is saved locally and remains private. There is also a section on where to download the data.
- comments.csv: to save the comments that you enter from the main interace. It is a comma-separated file, using a ";" as the separator, so try to avoid using ";" when writing comments.
- resolved_names.csv: when displaying the results of a query, the code will take the "OBJECT" field from the headers and will query Simbad to find the main identifier. To avoid doing that every time, the package will save the result of the Simbad query in that file to speed up the display over time.

## Data download

After doing one query, you can select one of the row and press the `Download` button. There will be a pop-up window showing up where you can access the `Preferences` in case you need to change the download directory, and you can also select the kind of data you want. You can select from the following three options:

- Science files only
- Science and raw calibration files
- Science and processed calibration files

The first option will always be faster than the other two since the calibration cascade does not have to be run.

Once you start downloading something, there should be a progress bar that appears at the bottom of the interface, and you should not be able to use the program for a while (to avoid starting multiple download at the same time, I doubt this would work very well).

## Data structure

I strongly recommend to pick one location for the data that you download and stick to it. The package will try to see if you already downloaded some data to avoid downloading them multiple times. The structure to save the data will be the following:

```
path_set_in_preferences/star_name_from_simbad/observing_night/ob_id
```

It will use the main identifier that it got from Simbad (there might be some problems if the stellar name is not resolved with Simbad, I did not encounter such cases yet), the observing night, and the "OB ID" that is provided by the observatory. The fits file will be saved in a subfolder `raw` and will be uncompressed.

## Requirements

The requirements can be found below. The main interface is done using `PyQt5`, while the query to the ESO SPHERE archive is done using `astroquery`. There are some scripts that come directly from the ESO webpages (`eso_programmatic.py`) which are using the `pyvo` package.

I also included a script to have a first look reduction of the ADI observations. The file `data_reduction.py` will be copied to the directory where the data has been downloaded, and can be run from there. This scripts makes use of the `vlt-sphere` package from [@avigan](https://github.com/avigan).

```python

astropy==5.0.4
astroquery==0.4.6
imutils==0.5.4
numpy==1.17.4
PyQt5==5.15.9
pyvo==1.3
requests==2.22.0
scikit_learn==1.2.2
vlt_sphere==1.5.1

```

## Operating systems and such

This package has only been tested on Linux, I have not idea if/how it will work on MacOS or Windows.

On Ubuntu, I added a file `spherequery.desktop` in `$HOME/.local/share/applications` containing the following:

```
[Desktop Entry]
Name=SphereQuery
GenericName=SphereQuery
Exec=python3 <path to the folder you downloaded>/SPHEREQuery/SPHEREQuery.py
Terminal=false
Type=Application
```

This should allow to start the application from your favorite launcher.

Otherwise, you can go to the folder where you downloaded this repository and start it using `python3 SPHEREQuery.py`.

## TODO

- [x] Include IRDIS
- [ ] Include IFS
- [ ] Include ZIMPOL
