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
parameter host (e.g. https://yourserver.org/api/v2) using the given
apikey.

```python
def disconnect():
```
Disconnect from the eLabFTW server.

```python
def get_table_data(expid: int, 
                   tableidx: int=0, header: bool=True, datatype: str='np'):
```
In eLabFTW, tables can be defined in the body text of experiments.
The data of such tables can be retrieved by using this function.
expid is an integer number which identifies the eLabFTW experiment.

All other parameters are optional. tableidx tells the function the
return the data of the n-th table, where counting starts with n = 0.
If header is true, the function assumes that the table contains
columns of data where the first element (row) is the column heading.
datatype may be either 'df' or 'np' (default). For 'df', a pandas dataframe
representing the table data is returned, whereas for 'np' a dictionary
of numpy arrays for each column is returned, in which the keys correspond
to the column heading (in case of header=True).

```python
def get_file_csv_data(expid: int, filename: str, 
                      header: bool=True, sep: str=',', datatype: str='np'):
```
Get the data from csv files attached to eLabFTW experiments.
expid is the experiment identifier (integer number), filename is
the name of the file stored in the experiment. 

All other parameters are optional. sep is the column separator,
by default a comma. The parameters header and datatype have the same
meaning as in get_table_data()

```python
def upload_image_from_figure(expid: int, fig: Figure,
                             filename: str, comment: str,
                             replacefile: bool=True,
                             format: str='png', dpi='figure'):
```
Upload an image of a matplotlib Figure (e.g. created by: fig, ax = plt.subplots())
as attachment to an eLabFTW experiment. expid is the experiment identifier
(integer number), fig a matplotlib.figure.Figure object, filename the
name of the image file to be uploaded, and comment is a description of
the image.

All other parameters are optional. If replacefile is true, an existing 
file with the same filename will be replaced. Otherwise, a new attachment
with the same filename will be created. format or dpi specify the
file format or image resolution, respectively. They are passed to
matplotlib's savefig() function.
