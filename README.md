# pyelabdata
pyelabdata provides functions for simple one-line access to data stored
in eLabFTW via Python or Jupyter.

## Examples
Examples for the use of pyelabdata can be found in the examples folder.

## Functions

### General functions

```python
def connect(host: str, apikey: str, verify_ssl: bool=True):
```
Connects to the API interface of the eLabFTW server specified by the
parameter `host` (e.g. `https://yourserver.org/api/v2`) 
using the given `apikey`.
If `api` is missing in the url, `/api/v2` will be added automatically.
Thus, `https://yourserver.org` would be enough.
The optional parameter `verify_ssl` allows to disable ssl verification.

```python
def disconnect():
```
Disconnect from the eLabFTW server.

```python
def get_info():
```
Return the info page about the instance.

```python
def get_teamid():
```
Return the team id associated with the api key used.

```python
def list_experiments(searchstring: str='', tags=[], only_current_team: bool=True,
                     list_keys=['id']):
```
Retrieve a list of all experiments that contain `searchstring`
in the title, body or elabid and that match the tags specified in `tags`. If `only_current_team` is set to true, only experiments within the current team are listed. With `list_keys` the keys are defined which are returned by the function; if only one key is listed, the return value is a list of values corresponding to that key (e.g. by default only a list of experiment ids is returned), if more than one key is requested, a list of dictionaries (with key-value pairs) is returned.
All parameters are optional. If nothing is specified, all ids of accessible
experiments will be listed.

```python
def create_experiment(title="Untitled", body="", content_type=2):
```
Creates and opens an empty experiment in eLabFTW returning the id of the entry. The `body` can be used to provide the main text of the experiment.
The `content_type` specifies the content type for main text: (1) HTML or (2) Markdown (default). All subsequent commands will operate on the opened experiment.

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
                   decimal: str='.', thousands: str=None,
                   datatype: str='np', expid: int=None):
```
In eLabFTW, tables can be defined in the body text of experiments.
The data of such tables can be retrieved by using this function.

All parameters are optional. `tableidx` tells the function the
return the data of the *n*<sup>th</sup> table, where counting starts with *n* = 0.
If `header` is true, the function assumes that the table contains
columns of data where the first element (row) is the column heading.
`decimal` or `thousands` define the character representing the decimal point or
the separator of thousands, respectively. If `thousands` is None, `,` or `.` is
used if decimal is `.` or `,`, respectively. The default is `.` for `decimal` and None
for `thousands`.
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
                      decimal: str='.', thousands: str=None,
                      datatype: str='np', expid: int=None):
```
Get the data from csv files attached to eLabFTW experiments.
`filename` is the name of the file stored in the experiment. 
if `filename_is_long_name` is set to True, `filename` is 
regarded as the long_name of the file stored in eLabFTW.

All other parameters are optional. `sep` is the column separator,
by default a comma. The parameters `header`, `decial`, `thousands`, 
`datatype` and `expid` have the same
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
                      position: int = None, options: list = None,
                      expid: int=None):
```
Create a new extra field with the name `fieldname` of type `fieldtype`
(possible values: text, number, date, time, datetime, select, checkbox; the default type is `text`) containing the value of `value`,
see also the [eLabFTW documentation](https://doc.elabftw.net/docs/usage/metadata#extra-fields-objects). 
If the field already exists, only the value will be updated
(all other parameters are ignored in this case).
You can define a list of possible units in the
parameter `units` and specify the default unit in `unit`.
The extra field may be assigned to an extra field group with name
`groupname`; if the group doesn't exist, it will be created.  
The `readonly` and `required` control the respective property of the
extra field. The `position` adjusts the order of appearance in the group `groupname`.  
Depending on `fieldtype`, `value` will automatically be converted
to string using appropriate functions (e.g. datetime.isoformat).  
In the case of `fieldtype='select'`, the `options` provide a list of defined values; if `value` is not a member of `options` it will be added to the default list.
In the case of `fieldtype='checkbox'` the `value` must be either `on` or `off`.  
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

```python
def replace_experiment_metadata(metadata: dict, expid: int=None):
```
Deletes and replaces all extra fields of the experiment with dictionary `metadata`. The `metadata` dict should be JSON-serializable according to the schema:
```python
metadata = {
    "elabftw": {
        "extra_fields_groups":[
            {"id":1, "name": "Group Name1"}, 
            {"id":2, "name": "Group Name2"},
            ]
        },
    "extra_fields":{
        "ExtraField1": {
            "type":"text", "value": "Some Value",
            "group_id":1, "position":0,
            },
        "ExtraField2": {
            "type":"text", "value": "Another Value",
            "group_id":2, "position":0,
            },
	 }
}
```


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


### Experiment Steps

```python
def get_steps(expid: int=None):
```
Get all steps for an experiment.

All parameters are optional.
`expid` is an integer number which identifies the eLabFTW experiment; 
if set to None, the currently opened experiment is used.

The function returns a list of dictionaries containing the step data.

```python
def create_step(expid: int=None, body: str=""):
```
Create a new step for an experiment.

All parameters are optional.
`expid` is an integer number which identifies the eLabFTW experiment; 
if set to None, the currently opened experiment is used.
`body` is the body content for the new step.

The function returns the ID of the newly created step.

```python
def update_step(stepid: int, expid: int=None, body: str=None, toggle_finished: bool=None):
```
Update an existing step.

All parameters are optional except stepid.
`stepid` is the ID of the step to update.
`expid` is an integer number which identifies the eLabFTW experiment; 
if set to None, the currently opened experiment is used.
`body` is the new body content for the step (optional).
`toggle_finished` is a boolean to toggle the finished status of the step from `on` to `off` and vice versa (optional).

The function returns a dictionary with status information about the update operation.

```python
def delete_step(stepid: int, expid: int=None):
```
Delete a step from an experiment.

All parameters are optional.
`stepid` is the ID of the step to delete.
`expid` is an integer number which identifies the eLabFTW experiment; 
if set to None, the currently opened experiment is used.
