# -*- coding: utf-8 -*-
"""
@author: Michael Krieger (lapmk)
"""

import numpy as np
import elabapi_python
import pandas as pd
import json
import h5py
import tempfile
import os
import time
import ipyparams
from matplotlib.figure import Figure
from io import StringIO, BytesIO
from pathlib import Path
from datetime import datetime, date, time
from IPython.display import display, Javascript

__APICLIENT__ = None
__EXPID__ = None


### General functions ###


def connect(host: str, apikey: str):
    """Connect to eLabFTW server API.
    
    Parameters
    ----------
    host : str
        URL to V2 api on the eLabFTW server, 
        e.g. https://server/api/v2.
    apikey : str
        API key to be used in order to access the eLabFTW data.

    Returns
    -------
    None.

    """
    
    global __APICLIENT__
    
    # configure elabftw access
    conf = elabapi_python.Configuration()
    conf.api_key['api_key'] = apikey
    conf.api_key_prefix['api_key'] = 'Authorization'
    conf.host = host
    conf.debug = False
    conf.verify_ssl = True
    
    # connect to api
    __APICLIENT__ = elabapi_python.ApiClient(conf)
    __APICLIENT__.set_default_header(header_name='Authorization', 
                                     header_value=apikey)
    
    
def disconnect():
    """Disconnect from the eLabFTW server API
    
    Returns
    -------
    None.

    """
    
    global __APICLIENT__
    __APICLIENT__ = None


def list_experiments(searchstring: str='', tags=[]):
    """Return a list of all experiments that contain searchstring
    in title, body or elabid and that match the tags.

    Parameters
    ----------
    searchstring: str, optional
        A string that needs to be contained in the title, body or elabid
        of the experiments.
        The default is ''.
    tags : list, optional
        A list of tags for which experiments should be searched.
        The default is an empty list.

    Returns
    -------
    A list of experiment ids that match the tags.

    """

    global __APICLIENT__
    if __APICLIENT__ is None:
        raise RuntimeError('Not connected to eLabFTW server')
    exp_api = elabapi_python.ExperimentsApi(__APICLIENT__)

    exps = exp_api.read_experiments(q=searchstring, tags=tags, limit=9999)
    return [exp.id for exp in exps]


def open_experiment(expid: int, returndata: bool=False):
    """Open an experiment on eLabFTW.
    This experiment will be used for all subsequent commands 
    (unless otherwise specified.)

    Parameters
    ----------
    expid : int
        The id of the experiment in eLabFTW to be read.
    returndata : bool, optional
        If True, open_experiment will return a dictionary containing
        the experiment's metadata.
        The default is False

    Returns
    -------
    None.

    """

    global __APICLIENT__
    global __EXPID__
    __EXPID__ = expid
    
    if __APICLIENT__ is None:
        raise RuntimeError('Not connected to eLabFTW server')
    exp_api = elabapi_python.ExperimentsApi(__APICLIENT__)
    
    # fetch experiment
    exp = exp_api.get_experiment(__EXPID__)
    if returndata:
        return exp


def close_experiment():
    """Close experiment.
    Subsequent commands will not further operate on the experiment.
    
    Returns
    -------
    None.

    """

    global __EXPID__
    __EXPID__ = None


### Read experiment data ###    
    
    
def __conv_df_to_np(df: pd.DataFrame) -> dict:
    """Convert a pandas dataframe to a dictionary of numpy arrays
    for each column with keys corresponding to the column headings.
    In case of duplicate column headings, a consecutive number is
    appended.

    Parameters
    ----------
    df : pandas.dataframe
        The dataframe to be converted.
        
    Returns
    -------
    dictionary
        A dictionary of numpy arrays for each column of the parameter df

    """

    data = {}
    for name, column in df.items():
        cno = 0
        while name in data.keys():
            cno += 1
            name = name + '_' + str(cno)
        data[name] = np.array(column.to_numpy(), dtype=float)
    return data


def get_experimentdata(expid: int=None):
    """Read and return the record of an experiment
    stored in eLabFTW.
    
    Parameters
    ----------
    expid : int, optional
        The id of the experiment in eLabFTW to be read.
        If None, the experiment specified by open_experiment() is used.
        The default is None.

    Returns
    -------
    dictionary
        Returns the experiment data

    """

    global __APICLIENT__
    if __APICLIENT__ is None:
        raise RuntimeError('Not connected to eLabFTW server')
    exp_api = elabapi_python.ExperimentsApi(__APICLIENT__)
    
    if expid is None:
        global __EXPID__
        expid = __EXPID__

    if expid is None:
        raise RuntimeError('No experiment opened or specified')
   
    # fetch experiment
    return exp_api.get_experiment(expid)


def get_maintext(format: str='html', expid: int=None):
    """Read and return the main (or body) text of an experiment
    stored in eLabFTW.
    
    Parameters
    ----------
    format: str, optional
        If format is 'html', the content of body_html of the experiment
        is returned, otherwise the content of body.
        The default is 'html'.
    expid : int, optional
        The id of the experiment in eLabFTW to be read.
        If None, the experiment specified by open_experiment() is used.
        The default is None.

    Returns
    -------
    str
        Returns the main (or body) text

    """

    global __APICLIENT__
    if __APICLIENT__ is None:
        raise RuntimeError('Not connected to eLabFTW server')
    exp_api = elabapi_python.ExperimentsApi(__APICLIENT__)
    
    if expid is None:
        global __EXPID__
        expid = __EXPID__

    if expid is None:
        raise RuntimeError('No experiment opened or specified')
   
    # fetch experiment
    exp = exp_api.get_experiment(expid)
    
    if format == 'html':
        return exp.body_html
    else:
        return exp.body


def get_table_data(tableidx: int=0, header: bool=True, 
                   datatype: str='np', expid: int=None):   
    """Read and return table data from the body text of an experiment 
    stored in eLabFTW.

    Parameters
    ----------
    tableidx : int, optional
        The index of the table to be read; first table has index 0. 
        The default is 0.
    header : bool, optional
        If True, the first table row contains the column names, which
        are used as headings for the pandas dataframe. 
        The default is True.
    datatype : str, optional
        'df': return a pandas dataframe,
        'np': return a dictionary of numpy arrays for each column. 
        The default is 'np'.
    expid : int, optional
        The id of the experiment in eLabFTW to be read.
        If None, the experiment specified by open_experiment() is used.
        The default is None.

    Returns
    -------
    pandas.dataframe or dictionary
        Return type depends on the parameter datatype (see above).

    """
    
    global __APICLIENT__
    if __APICLIENT__ is None:
        raise RuntimeError('Not connected to eLabFTW server')
    exp_api = elabapi_python.ExperimentsApi(__APICLIENT__)
    
    if expid is None:
        global __EXPID__
        expid = __EXPID__

    if expid is None:
        raise RuntimeError('No experiment opened or specified')
   
    # fetch experiment
    exp = exp_api.get_experiment(expid)
    
    # extract table
    tables = pd.read_html(exp.body_html)
    
    # extract selected table and assign header if requested
    if header:
        table = tables[tableidx].iloc[1:]
        table.columns = tables[tableidx].iloc[0]
    else:
        table = tables[tableidx]
        
    # return result
    if datatype == 'df':
        return table
    elif datatype == 'np':
        return __conv_df_to_np(table)
    else:
        raise RuntimeError('Wrong datatype')

        
def get_extrafields(fieldname: str=None, expid: int=None):
    """Read and return the extra fields of an experiment
    stored in eLabFTW.
    
    Parameters
    ----------
    fieldname: str, optional
        If fieldname is None, a dictionary of all extra fields is returned,
        otherwise the value of the field specified.
        The default is None.
    expid : int, optional
        The id of the experiment in eLabFTW to be read.
        If None, the experiment specified by open_experiment() is used.
        The default is None.

    Returns
    -------
    str or dictionary
        Returns either the value of the field specified or a dictionary
        of all extra fields.

    """

    global __APICLIENT__
    if __APICLIENT__ is None:
        raise RuntimeError('Not connected to eLabFTW server')
    exp_api = elabapi_python.ExperimentsApi(__APICLIENT__)
    
    if expid is None:
        global __EXPID__
        expid = __EXPID__

    if expid is None:
        raise RuntimeError('No experiment opened or specified')
   
    # fetch experiment
    exp = exp_api.get_experiment(expid)
    
    data = json.loads(exp.metadata)['extra_fields']
    if fieldname is None:
        return data
    else:
        value = data[fieldname]['value']
        if data[fieldname]['type'] == 'number':
            return float(value)
        if data[fieldname]['type'] == 'datetime-local':
            return datetime.fromisoformat(value)
        if data[fieldname]['type'] == 'date':
            return date.fromisoformat(value)
        if data[fieldname]['type'] == 'time':
            return time.fromisoformat(value)
        else:
            return value

        
### Read files ###    
    
    
def __get_upload_id(expid: int, filename: str):
    global __APICLIENT__
    if __APICLIENT__ is None:
        raise RuntimeError('Not connected to eLabFTW server')
    uploads_api = elabapi_python.UploadsApi(__APICLIENT__)

    # fetch metadata of all uploads and search for filename
    uploads = uploads_api.read_uploads('experiments', expid)
    uploadid = None
    for upload in uploads:
        if upload.real_name == filename:
            uploadid = upload.id
            break   
    return uploadid


def __get_upload_id_by_long_name(expid: int, long_name: str):
    global __APICLIENT__
    if __APICLIENT__ is None:
        raise RuntimeError('Not connected to eLabFTW server')
    uploads_api = elabapi_python.UploadsApi(__APICLIENT__)

    # fetch metadata of all uploads and search for filename
    uploads = uploads_api.read_uploads('experiments', expid)
    uploadid = None
    for upload in uploads:
        if upload.long_name == long_name:
            uploadid = upload.id
            break   
    return uploadid


def get_file_data(filename: str, filename_is_long_name: bool=False, expid: int=None):   
    """Read and return binary data from a file attached to 
    an experiment stored in eLabFTW.

    Parameters
    ----------
    filename : str
        The filename of the file to be read from the experiment.
    filename_is_long_name: bool
        The value of filename is the long_name stored used in eLabFTW.
        The default is False.
    expid : int, optional
        The id of the experiment in eLabFTW to be read.
        If None, the experiment specified by open_experiment() is used.
        The default is None.

    Returns
    -------
    bytes
        Returns the binary data of the specified file.

    """

    global __APICLIENT__   
    if __APICLIENT__ is None:
        raise RuntimeError('Not connected to eLabFTW server')
    uploads_api = elabapi_python.UploadsApi(__APICLIENT__)
    
    if expid is None:
        global __EXPID__
        expid = __EXPID__

    if expid is None:
        raise RuntimeError('No experiment opened or specified')
    
    if filename_is_long_name:
        uploadid = __get_upload_id_by_long_name(expid, filename)
    else:
        uploadid = __get_upload_id(expid, filename)
          
    if uploadid is None:
        raise RuntimeError('File not found in eLabFTW experiment')
    else:
        # fetch file data
        return uploads_api.read_upload(
            'experiments', expid, uploadid, format='binary', 
            _preload_content=False).data

    
def get_file_csv_data(filename: str, 
                      filename_is_long_name: bool=False,
                      header: bool=True, sep: str=',', 
                      datatype: str='np', expid: int=None):   
    """Read and return data from a csv-like text file attached to 
    an experiment stored in eLabFTW.

    Parameters
    ----------
    filename : str
        The filename of the file to be read from the experiment.
    filename_is_long_name: bool
        The value of filename is the long_name stored used in eLabFTW.
        The default is False.
    header : bool, optional
        If True, the first table row contains the column names, which
        are used as headings for the pandas dataframe. 
        The default is True.
    sep : str, optional
        The column separator used in the file.
        The default is ','.
    datatype : str, optional
        'df': return a pandas dataframe,
        'np': return a dictionary of numpy arrays for each column. 
        The default is 'np'.
    expid : int, optional
        The id of the experiment in eLabFTW to be read.
        If None, the experiment specified by open_experiment() is used.
        The default is None.

    Returns
    -------
    pandas.dataframe or dictionary
        Return type depends on the parameter datatype (see above).

    """

    # fetch file data
    filedata = get_file_data(filename, filename_is_long_name, expid).decode('utf-8')

    # extract data
    df = pd.read_csv(StringIO(filedata), sep=sep, 
                     header=(0 if header else 'infer'))

    # return result
    if datatype == 'df':
        return df
    elif datatype == 'np':
        return __conv_df_to_np(df)
    else:
        raise RuntimeError('Wrong datatype')

            
def get_file_hdf5_data(filename: str, filename_is_long_name: bool=False, expid: int=None):   
    """Read and return data from a hdf5 file attached to 
    an experiment stored in eLabFTW.

    Parameters
    ----------
    filename : str
        The filename of the file to be read from the experiment.
    filename_is_long_name: bool
        The value of filename is the long_name stored used in eLabFTW.
        The default is False.
    expid : int, optional
        The id of the experiment in eLabFTW to be read.
        If None, the experiment specified by open_experiment() is used.
        The default is None.

    Returns
    -------
    h5py file object
        Returns a file object as created by h5py.File.

    """

    # fetch file data
    filestream = BytesIO(get_file_data(filename, filename_is_long_name, expid))

    # open and return hdf5
    return h5py.File(filestream, 'r')


### Update experiment data ###


def create_extrafield(fieldname: str, value, fieldtype: str='text',
                      unit: str=None, units=None, description: str=None,
                      groupname: str=None,
                      readonly: bool=False, required: bool=False,
                      expid: int=None):
    """Create an extra field in an experiment.

    Parameters
    ----------
    fieldname : str
        The fieldname of the entry.
    value :
        The value of the entry.
    fieldtype : str
        The type of the field. Possible values: text, number, date, time, datetime-local.
        The default is 'text'.
    unit : str
        The unit of the quantity.
        The default is None.
    description : str
        The description of the entry.
        The default is None.
    readonly : bool
        Make the field readonly.
        The default is False.
    required : bool
        Make the field required.
        The default is False.
    expid : int, optional
        The id of the experiment in eLabFTW to be read.
        If None, the experiment specified by open_experiment() is used.
        The default is None.

    Returns
    -------
    None.

    """

    global __APICLIENT__
    if __APICLIENT__ is None:
        raise RuntimeError('Not connected to eLabFTW server')
    exp_api = elabapi_python.ExperimentsApi(__APICLIENT__)
    
    if expid is None:
        global __EXPID__
        expid = __EXPID__

    if expid is None:
        raise RuntimeError('No experiment opened or specified')
   
    # fetch experiment
    exp = exp_api.get_experiment(expid)
    metadata = json.loads(exp.metadata)
    
    # check if fieldname already exists
    if fieldname in metadata['extra_fields'].keys():
        raise RuntimeError('Fieldname already exists')
    
    if groupname is not None:
        # check if group already exists
        groupid = [group['id'] for group in metadata['elabftw']['extra_fields_groups'] 
                   if group['name']==groupname]
        groupid = groupid[0] if len(groupid)>0 else None

        # create group if not yet existing
        if groupid is None:
            groupid = max([group['id'] for group in metadata['elabftw']['extra_fields_groups']]) + 1
            metadata['elabftw']['extra_fields_groups'].append({'id': groupid, 'name': groupname})
    
    # create field
    if fieldtype == 'datetime':
        fieldtype = 'datetime-local'
    metadata['extra_fields'][fieldname] = {'type': fieldtype}

    if type(value) != str:
        if fieldtype == 'number':
            value = str(value)
        if fieldtype == 'datetime-local':
            value = datetime.isoformat(value.replace(second=0, microsecond=0))
        if fieldtype == 'date':
            value = date.isoformat(value)
        if fieldtype == 'time':
            value = time.isoformat(value.replace(second=0, microsecond=0))

    metadata['extra_fields'][fieldname]['value'] = value
    
    if unit is not None:
        metadata['extra_fields'][fieldname]['unit'] = unit
        if units is None:
            units = [unit]
    if units is not None:
        metadata['extra_fields'][fieldname]['units'] = units
    if description is not None:
        metadata['extra_fields'][fieldname]['description'] = description
    if groupname is not None:
        metadata['extra_fields'][fieldname]['group_id'] = groupid
    if readonly:
        metadata['extra_fields'][fieldname]['readonly'] = True
    if required:
        metadata['extra_fields'][fieldname]['required'] = True

    # save to elabftw
    exp_api.patch_experiment(expid, body={'metadata': json.dumps(metadata)})


def update_extrafield(fieldname: str, value, expid: int=None):
    """Update the value of an extra field of an experiment.

    Parameters
    ----------
    fieldname : str
        The fieldname of the entry.
    value
        The value of the entry.
    expid : int, optional
        The id of the experiment in eLabFTW to be read.
        If None, the experiment specified by open_experiment() is used.
        The default is None.

    Returns
    -------
    None.

    """

    global __APICLIENT__
    if __APICLIENT__ is None:
        raise RuntimeError('Not connected to eLabFTW server')
    exp_api = elabapi_python.ExperimentsApi(__APICLIENT__)
    
    if expid is None:
        global __EXPID__
        expid = __EXPID__

    if expid is None:
        raise RuntimeError('No experiment opened or specified')
        
    if type(value) != str:
        # fetch type of metadatafield
        exp = exp_api.get_experiment(expid)
        metadata = json.loads(exp.metadata)
        fieldtype = metadata['extra_fields'][fieldname]['type']

        if fieldtype == 'number':
            value = str(value)
        if fieldtype == 'datetime-local':
            value = datetime.isoformat(value.replace(second=0, microsecond=0))
        if fieldtype == 'date':
            value = date.isoformat(value)
        if fieldtype == 'time':
            value = time.isoformat(value.replace(second=0, microsecond=0))
        
    exp_api.patch_experiment(expid, body={'action': 'updatemetadatafield', fieldname: value})

    
def delete_extrafield(fieldname: str, expid: int=None):
    """Delete an extra field in an experiment.

    Parameters
    ----------
    fieldname : str
        The fieldname of the entry.
    expid : int, optional
        The id of the experiment in eLabFTW to be read.
        If None, the experiment specified by open_experiment() is used.
        The default is None.

    Returns
    -------
    None.

    """

    global __APICLIENT__
    if __APICLIENT__ is None:
        raise RuntimeError('Not connected to eLabFTW server')
    exp_api = elabapi_python.ExperimentsApi(__APICLIENT__)
    
    if expid is None:
        global __EXPID__
        expid = __EXPID__

    if expid is None:
        raise RuntimeError('No experiment opened or specified')
   
    # fetch experiment
    exp = exp_api.get_experiment(expid)
    metadata = json.loads(exp.metadata)
      
    del metadata['extra_fields'][fieldname]

    # save to elabftw
    exp_api.patch_experiment(expid, body={'metadata': json.dumps(metadata)})
    
    
### Upload files ###

        
def upload_file(file: str, comment: str,
                replacefile: bool=True, expid: int=None):
    """Upload an excisting file to an experiment on eLabFTW
    
    Parameters
    ----------
    file : str
        The name and path of the file to be uploaded.
    comment : str
        A comment decribing the file.
    replacefile : bool, optional
        If True, an existing file with the same name will be overwritten.
        The default is True.
    expid : int, optional
        The id of the experiment in eLabFTW into which the file
        should be uploaded.
        If None, the experiment specified by open_experiment() is used.
        The default is None.

    Returns
    -------
    None.

    """

    global __APICLIENT__
    if __APICLIENT__ is None:
        raise RuntimeError('Not connected to eLabFTW server')
    uploads_api = elabapi_python.UploadsApi(__APICLIENT__)

    if expid is None:
        global __EXPID__
        expid = __EXPID__

    if expid is None:
        raise RuntimeError('No experiment opened or specified')
    
    if replacefile:
        uploadid = __get_upload_id(expid, os.path.basename(file))
    else:
        uploadid = None
        
    if uploadid is None:
        uploads_api.post_upload('experiments', expid, 
                                file=file, comment=comment)
    else:
        uploads_api.post_upload_replace('experiments', expid, uploadid,
                                        file=file, comment=comment)


def upload_image_from_figure(fig: Figure, filename: str, comment: str,
                             replacefile: bool=True,
                             format: str='png', dpi='figure',
                             expid: int=None):
    """Generate image from matplotlib figure and upload it to
    an experiment on eLabFTW
    
    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The matplotlib figure.
    filename : str
        The filename without extension.
    comment : str
        A comment decribing the figure.
    replacefile : bool, optional
        If True, an existing file with the same name will be overwritten.
        The default is True.
    format : str, optional
        The image file format. 
        The default is 'png'.
    dpi : optional
        The resolution of the image as defined in matplotlib's savefig().
        The default is 'figure'.
    expid : int, optional
        The id of the experiment in eLabFTW into which the image
        should be uploaded.
        If None, the experiment specified by open_experiment() is used.
        The default is None.

    Returns
    -------
    None.

    """

    # create a temporary directory for the image, create it and upload
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpfile = os.path.join(tmpdir, 
                               Path(filename).with_suffix('.' + format))
        fig.savefig(tmpfile, format=format, facecolor='white', dpi=dpi)
        upload_file(tmpfile, comment, replacefile, expid=expid)
        
        
def upload_csv_data(data, filename: str, comment: str,
                    replacefile: bool=True, index: bool=False,
                    expid: int=None):
    """Generate a csv file from a pandas dataframe or a dictionary of
    numpy arrays (column data) and upload it to an experiment on eLabFTW
    
    Parameters
    ----------
    data :
        The data to be stored. This can be either a pandas.DataFrame or
        a dictionary of 1-dimensional numpy arrays representing column
        data; in the latter case, the dictionary will be converted into
        a dataframe before creating the csv file.
    filename : str
        The filename with extension (e.g. .txt).
    comment : str
        A comment decribing the file.
    replacefile : bool, optional
        If True, an existing file with the same name will be overwritten.
        The default is True.
    index : bool, optional
        If True, write also dataframe row names (index) to file.
        The default is False.
    expid : int, optional
        The id of the experiment in eLabFTW into which the file
        should be uploaded.
        If None, the experiment specified by open_experiment() is used.
        The default is None.

    Returns
    -------
    None.

    """

    # if data is not a dataframe, try to convert data to dataframe
    if isinstance(data, pd.DataFrame):
        df = data
    else:
        df = pd.DataFrame(data)

    # create a temporary directory for the file, create it and upload
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpfile = os.path.join(tmpdir, filename)
        df.to_csv(tmpfile, index=index)
        upload_file(tmpfile, comment, replacefile, expid=expid)
    
    
def upload_this_jupyternotebook(comment: str, replacefile: bool=True,
                                expid: int=None):
    """Saves and uploads the current jupyter notebook
    to an experiment on eLabFTW
    
    Parameters
    ----------
    comment : str
        A comment decribing the jupyter notebook.
    replacefile : bool, optional
        If True, an existing file with the same name will be overwritten.
        The default is True.
    expid : int, optional
        The id of the experiment in eLabFTW into which the jupyter notebook
        should be uploaded.
        If None, the experiment specified by open_experiment() is used.
        The default is None.
        
    Returns
    -------
    None.

    """
   
    # get Jupyter notebook filename
    filename = ipyparams.notebook_name
    file = os.path.join(os.getcwd(), filename)
    
    # save notebook and wait for completion
    start = os.path.getmtime(file)
    display(Javascript('IPython.notebook.save_checkpoint()'))
    while os.path.getmtime(file) == start:
        time.sleep(0.1)
        
    # upload to elabftw
    upload_file(file, comment, replacefile, expid=expid)
