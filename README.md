# pyelabdata
pyelabdata provides functions for simple one-line access to data stored
in eLabFTW via Python or Jupyter.

## Examples
Examples for the use of pyelabdata can be found in the examples folder.

## Functions

### General functions

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
def list_experiments(searchstring: str='', tags=[]):
```
Retrieve a list of ids of all experiments that contain `searchstring`
in the title, body or elabid and that match the tags specified in `tags`.
All parameters are optional. If nothing is specified, all accessible
experiments will be listed.

```python
def open_experiment(expid: int, returndata: bool=False):
```
Open an experiment in eLabFTW using the id of the experiment. If `returndata`
is `True`, the function returns a dictionary with the metadata of the 
experiment.
All subsequent commands will operate on the opened experiment.

```python
def close_experiment():
```
Close the current experiment.
Subsequent commands will not further operate on the experiment.

### Read experiment data

```python
def get_experimentdata(expid: int=None):
```
Retrieve the complete data of the experiment.

All parameters are optional.
`expid` is an integer number which identifies the eLabFTW experiment; 
if set to None, the currently opened experiment is used.

The function returns a dictionary with the structured data.

```python
def get_maintext(format: str='html', expid: int=None):
```
Retrieve the body text of the experiment.

All parameters are optional. If `format` is `'html'`, the content of
body_html is returned, i.e. the body text in html format. Otherwise
the content of body is returned, which depends on the format used in
eLabFTW (markdown or html).
`expid` is an integer number which identifies the eLabFTW experiment; 
if set to None, the currently opened experiment is used.

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
def get_extrafields(fieldname: str=None, expid: int=None):
```
In eLabFTW, so-called extra fields can be defined. These are
key-value pairs, which are additionally described with units,
value type, description and which may be grouped.

All parameters are optional. If `fieldname` is None,
all extra fields are returned as a dictionary.
If `fieldname` is specified, the value of the entry
is returned. If the field type is numeric or date/time,
the return value is of the respective type.

### Read files

```python
def get_file_data(filename: str, filename_is_long_name: bool=False, expid: int=None):
```
Get the (binary) data from a file attached to eLabFTW experiments.
`filename` is the name of the file stored in the experiment. 
if `filename_is_long_name` is set to True, `filename` is 
regarded as the long_name of the file stored in eLabFTW.

The parameter `expid` is optional and has the same meaning as in
`get_table_data()`. The binary data is returned as a byte string.

```python
def get_file_csv_data(filename: str, filename_is_long_name: bool=False,
                      header: bool=True, sep: str=',', 
                      datatype: str='np', expid: int=None):
```
Get the data from csv files attached to eLabFTW experiments.
`filename` is the name of the file stored in the experiment. 
if `filename_is_long_name` is set to True, `filename` is 
regarded as the long_name of the file stored in eLabFTW.

All other parameters are optional. `sep` is the column separator,
by default a comma. The parameters `header`, `datatype` and `expid` have the same
meaning as in `get_table_data()`.

```python
def get_file_hdf5_data(filename: str, filename_is_long_name: bool=False, expid: int=None):
```
Get the data from a hdf5 file attached to eLabFTW experiments.
`filename` is the name of the file stored in the experiment. 
if `filename_is_long_name` is set to True, `filename` is 
regarded as the long_name of the file stored in eLabFTW.

The parameter `expid` is optional and has the same meaning as in
`get_table_data()`. The function returns a hdf5 file object as 
created by `h5py.File()`.

### Update experiment data

```python
def create_extrafield(fieldname: str, value, fieldtype:str='text',
                      unit: str=None, units=None, description: str=None,
                      groupname: str=None,
                      readonly: bool=False, required: bool=False,
                      expid: int=None):
```
Create a new extra field with the name `fieldname` of type `fieldtype`
(possible values: text, number, date, time, datetime; the default
type is `text`) containing the value of `value`. 
You can define a list of possible units in the
parameter `units` and specify the default unit in `unit`.
The extra field may be assigned to an extra field group with name
`groupname`; if the group doesn't exist, it will be created.
`readonly` and `required` control the respective property of the
extra field. 
Depending on `fieldtype`, `value` will automatically be converted
to string using appropriate functions (e.g. datetime.isoformat).
The parameter `expid` is optional and has the same meaning as in
`get_table_data()`.

```python
def update_extrafield(fieldname: str, value, expid: int=None):
```
Update the value of the extra field with the name `fieldname`.
Depending on the type of the extra field, 
`value` will automatically be converted
to string using appropriate functions (e.g. datetime.isoformat).
The parameter `expid` is optional and has the same meaning as in
`get_table_data()`.

```python
def delete_extrafield(fieldname: str, expid: int=None):
```
Delete the extra field with name `fieldname`.
The parameter `expid` is optional and has the same meaning as in
`get_table_data()`.

### Upload files

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
                             replacefile: bool=True, 
                             format: str='png', dpi='figure',
                             expid: int=None):
```
Upload an image of a matplotlib Figure (e.g. created by 
`fig, ax = plt.subplots()`) as attachment to an eLabFTW experiment. 
`fig` a `matplotlib.figure.Figure` object, `filename` the name of the image 
file to be uploaded, and `comment` is a description of the image.

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
