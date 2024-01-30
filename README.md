# pyelabdata
pyelabdata provides functions for simple one-line access to data stored
in eLabFTW via Python or Jupyter.

## Examples
Examples for the use of pyelabdata can be found in the examples folder.

## Functions

```python
def connect(host: str, apikey: str):
```
Connects to the API interface of the eLabFTW server specified by the
parameter `host` (e.g. `https://yourserver.org/api/v2`) using the given
`apikey`.

```python
def disconnect():
```
Disconnect from the eLabFTW server.

```python
def open_experiment(expid: int):
```
Open an experiment in eLabFTW using the id of the experiment. The 
function returns a JSON with the metadata of the experiment.
All subsequent commands will operate on the opened experiment.

```python
def close_experiment():
```
Close the current experiment.
Subsequent commands will not further operate on the experiment.

```python
def get_table_data(tableidx: int=0, header: bool=True, 
                   datatype: str='np', expid: int=None):
```
In eLabFTW, tables can be defined in the body text of experiments.
The data of such tables can be retrieved by using this function.

All parameters are optional. `tableidx` tells the function the
return the data of the *n*<sup>th</sup> table, where counting starts with *n* = 0.
If `header` is true, the function assumes that the table contains
columns of data where the first element (row) is the column heading.
`datatype` may be either `'df'` or `'np'` (default). For `'df'`, a pandas dataframe
representing the table data is returned, whereas for `'np'` a dictionary
of numpy arrays for each column is returned, in which the keys correspond
to the column heading (in case of `header = True`).
`expid` is an integer number which identifies the eLabFTW experiment; 
if set to None, the currently opened experiment is used.


```python
def get_file_csv_data(filename: str, 
                      header: bool=True, sep: str=',', datatype: str='np', 
                      expid: int=None):
```
Get the data from csv files attached to eLabFTW experiments.
`filename` is the name of the file stored in the experiment. 

All other parameters are optional. `sep` is the column separator,
by default a comma. The parameters `header`, `datatype` and `expid` have the same
meaning as in `get_table_data()`.

```python
def upload_file(file: str, comment: str,
                replacefile: bool=True, expid: int=None):
```
Upload a file from local drives to an eLabFTW experiment.
`file` is the filepath of the file to be uploaded, 
`comment` is a description of the file.

All other parameters are optional. If `replacefile` is true, an existing 
file with the same filename will be replaced. Otherwise, a new attachment
with the same filename will be created. 
`expid` is an integer number which identifies the eLabFTW experiment; 
if set to None, the currently opened experiment is used.

```python
def upload_image_from_figure(fig: Figure, filename: str, comment: str,
                             replacefile: bool=True, format: str='png', dpi='figure'
                             expid: int=None):
```
Upload an image of a matplotlib Figure (e.g. created by `fig, ax = plt.subplots()`)
as attachment to an eLabFTW experiment. `fig` a `matplotlib.figure.Figure` object, `filename` the
name of the image file to be uploaded, and `comment` is a description of
the image.

All other parameters are optional. If `replacefile` is true, an existing 
file with the same filename will be replaced. Otherwise, a new attachment
with the same filename will be created. `format` or `dpi` specify the
file format or image resolution, respectively. They are passed to
matplotlib's `savefig()` function.
`expid` is an integer number which identifies the eLabFTW experiment; 
if set to None, the currently opened experiment is used.

```python
def upload_csv_data(data, filename: str, comment: str,
                    replacefile: bool=True, index: bool=False,
                    expid: int=None):
```
Generate a csv file from a pandas dataframe or a dictionary of
numpy arrays (column data) contained in `data` 
and upload it to an experiment on eLabFTW as csv file.
`comment` is a description of the data.

All other parameters are optional. If `replacefile` is true, an existing 
file with the same filename will be replaced. Otherwise, a new attachment
with the same filename will be created. If `index` is true, the line index
of the dataframe is also stored to the file.
`expid` is an integer number which identifies the eLabFTW experiment; 
if set to None, the currently opened experiment is used.

```python
def upload_this_jupyternotebook(comment: str, replacefile: bool=True,
                                expid: int=None):
```
Saves and uploads the current jupyter notebook
to an experiment on eLabFTW. `comment` is a description of the 
jupyter notebook.

All other parameters are optional. If `replacefile` is true, an existing 
file with the same filename will be replaced. Otherwise, a new attachment
with the same filename will be created. 
`expid` is an integer number which identifies the eLabFTW experiment; 
if set to None, the currently opened experiment is used.
