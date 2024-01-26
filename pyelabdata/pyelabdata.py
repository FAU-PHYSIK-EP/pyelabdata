# -*- coding: utf-8 -*-
"""
Created on Wed Jan 24 14:46:36 2024

@author: Michael Krieger (lapmk)
"""

import numpy as np
import elabapi_python
import pandas as pd
import tempfile
import os
import time
from matplotlib.figure import Figure
from io import StringIO
from pathlib import Path
from IPython.display import display, Javascript, HTML

__APICLIENT__ = None

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
    

def conv_df_to_np(df: pd.DataFrame) -> dict:
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


def get_table_data(expid: int, tableidx: int=0, header: bool=True, 
                   datatype: str='np'):   
    """Read and return table data from the body text of an experiment 
    stored in eLabFTW.

    Parameters
    ----------
    expid : int
        The id of the experiment in eLabFTW to be read.
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

    Returns
    -------
    pandas.dataframe or dictionary
        Return type depends on the parameter datatype (see above).

    """
    
    global __APICLIENT__
    if __APICLIENT__ is None:
        raise RuntimeError('Not connected to eLabFTW server')
    exp_api = elabapi_python.ExperimentsApi(__APICLIENT__)
    
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
        return conv_df_to_np(table)
    else:
        raise RuntimeError('Wrong datatype')
    

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
    

def get_file_csv_data(expid: int, filename: str, header: bool=True, sep: str=',', datatype: str='np'):   
    """Read and return data from a csv-like text file attached to 
    an experiment stored in eLabFTW.

    Parameters
    ----------
    expid : int
        The id of the experiment in eLabFTW to be read.
    filenamex : str
        The filename of the file to be read from the experiment.
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

    Returns
    -------
    pandas.dataframe or dictionary
        Return type depends on the parameter datatype (see above).

    """

    global __APICLIENT__
    if __APICLIENT__ is None:
        raise RuntimeError('Not connected to eLabFTW server')
    uploads_api = elabapi_python.UploadsApi(__APICLIENT__)
    
    uploadid = __get_upload_id(expid, filename)
          
    if uploadid is None:
        raise RuntimeError('File not found in eLabFTW experiment')
    else:
        # fetch file data
        filedata = uploads_api.read_upload(
            'experiments', expid, uploadid, format='binary', 
            _preload_content=False).data.decode('utf-8')
        
        # extract data
        df = pd.read_csv(StringIO(filedata), sep=sep, 
                         header=(0 if header else 'infer'))
           
        # return result
        if datatype == 'df':
            return df
        elif datatype == 'np':
            return conv_df_to_np(df)
        else:
            raise RuntimeError('Wrong datatype')
        
        
def upload_file(expid: int, file: str, comment: str,
                replacefile: bool=True):
    """Upload an excisting file to an experiment on eLabFTW
    
    Parameters
    ----------
    expid : int
        The id of the experiment in eLabFTW into which the file
        should be uploaded.
    file : str
        The name and path of the file to be uploaded.
    comment : str
        A comment decribing the file.
    replacefile : bool, optional
        If True, an existing file with the same name will be overwritten.
        The default is True.

    Returns
    -------
    None.

    """

    global __APICLIENT__
    if __APICLIENT__ is None:
        raise RuntimeError('Not connected to eLabFTW server')
    uploads_api = elabapi_python.UploadsApi(__APICLIENT__)
    
    if replacefile:
        uploadid = __get_upload_id(expid, os.path.basename(file))
        if uploadid is not None:
            uploads_api.delete_upload('experiments', expid, uploadid)
    
    uploads_api.post_upload('experiments', expid, 
                            file=file, comment=comment)


def upload_image_from_figure(expid: int, fig: Figure,
                             filename: str, comment: str,
                             replacefile: bool=True,
                             format: str='png', dpi='figure'):
    """Generate image from matplotlib figure and upload it to
    an experiment on eLabFTW
    
    Parameters
    ----------
    expid : int
        The id of the experiment in eLabFTW into which the image
        should be uploaded.
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

    Returns
    -------
    None.

    """

    # create a temporary directory for the image, create it and upload
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpfile = os.path.join(tmpdir, 
                               Path(filename).with_suffix('.' + format))
        fig.savefig(tmpfile, format=format, facecolor='white', dpi=dpi)
        upload_file(expid, tmpfile, comment, replacefile)
        
        
def upload_csv_data(expid: int, data,
                    filename: str, comment: str,
                    replacefile: bool=True,
                    index: bool=False):
    """Generate a csv file from a pandas dataframe or a dictionary of
    numpy arrays (column data) and upload it to an experiment on eLabFTW
    
    Parameters
    ----------
    expid : int
        The id of the experiment in eLabFTW into which the file
        should be uploaded.
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
        upload_file(expid, tmpfile, comment, replacefile)
    
    
def upload_this_jupyternotebook(expid: int, comment: str,
                                replacefile: bool=True):
    """Saves and uploads the current jupyter notebook
    to an experiment on eLabFTW
    
    Parameters
    ----------
    expid : int
        The id of the experiment in eLabFTW into which the jupyter notebook
        should be uploaded.
    comment : str
        A comment decribing the jupyter notebook.
    replacefile : bool, optional
        If True, an existing file with the same name will be overwritten.
        The default is True.
        
    Returns
    -------
    None.

    """
    
    # get Jupyter notebook filename
    # THIS STILL DOESN'T WORK !!!!!!!!!!!!!!!!!!!!!!!!!!!!
    filename = None
    html = '''
    <script>
        IPython.notebook.kernel.execute(
            'filename = "' + IPython.notebook.notebook_name + '"'
        )
    </script>
    '''
    display(HTML(html))
    if filename is None:
        raise RuntimeError('Could not retrieve the jupyter notebook filename')
    file = os.join(os.getcwd(), filename)
    
    # save notebook and wait for completion
    start = os.path.getmtime(file)
    display(Javascript('IPython.notebook.save_checkpoint()'))
    while os.path.getmtime(file) == start:
        time.sleep(0.1)
        
    # upload to elabftw
    upload_file(expid, file, comment, replacefile)
