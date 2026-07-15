# -*- coding: utf-8 -*-
# MIT License
# 
# Copyright (c) 2025-02-26 Michael Krieger (lapmk) https://github.com/FAU-PHYSIK-EP/pyelabdata
# based on Michael Krieger (lapmk): https://github.com/FAU-PHYSIK-EP/pyelabdata/blob/main/pyelabdata/pyelabdata.py
# with licence "MIT License": https://github.com/FAU-PHYSIK-EP/pyelabdata/blob/main/LICENSE
# 
# 
# File: pyelabdata.py
# Author: Ron Dockhorn
# Date: 2026-07-15
# Description: A simple wrapper of the elabapi_python package.
# 
# Version: 0.3.1
# Modified: 2026-07-07
# 
# Changes:
# + added "get_info()"
#
# Version: 0.3.2
# Modified: 2026-07-15
# 
# Changes:
# + added "get_steps()"
# + added "create_step()"
# + added "update_step()"
# + added "delete_step()"

"""
  A simple wrapper of the elabapi_python package (https://github.com/elabftw/elabapi-python)
  based on Michael Krieger's "pyelabdata.py" (2025-02-21) ,see https://github.com/FAU-PHYSIK-EP/pyelabdata/blob/main/pyelabdata/pyelabdata.py
  with "MIT License": https://github.com/FAU-PHYSIK-EP/pyelabdata/blob/main/LICENSE
  This version is also released under "MIT License" 
  Mostly the wrapper adds and redefines the following features for eLabFTW (5.3.11):
    - creation of experiments
    - creation of metadata (modified grouping and standard)
  
  Attributes:
    None

  Methods:
  connect(host, apikey, verify_ssl) -- connect to server instance
  disconnect() -- disconnect from server
  get_teamid() -- return the team id of provided apikey
  list_experiments(searchstring, tags, only_current_team, list_keys) -- provides a list of all experiments which are accessible with the apikey
  create_experiment() --  creates an experiment on server
  open_experiment(expid, returndata) -- access an already existing experiment
  close_experiment() -- close the connection to experiment 
  get_info() -- return the public accessible info page
  get_experimentdata(expid) -- provides access to the record of an experiment
  get_maintext(format, expid) -- provides access to the general description (html body) of an experiment
  create_extrafield - creates an specific metadata field of an experiment
  update_extrafield - overwrites an specific metadata field of an experiment
  delete_extrafield - removes an specific metadata field of an experiment
  update_experiment_title(title, expid) -- overwrites the title of an experiment
  replace_experiment_metadata(metadata, expid) -- overwrites the metadata of an experiment
  upload_file(file, comment, replacefile, expid) -- upload of a file to the server
  upload_this_jupyternotebook(comment, replacefile, expid) -- self-contained upload of the jupyter notebook to server
  get_steps - provides a list of all steps which are associates with the experiment
  create_step - creates a step within the experiment
  update_step - updates a step of the experiment (title or finished flag)
  delete_step - deletes a step of the experiment
"""

import numpy as np
import pandas as pd
import json
import h5py
import tempfile
import os
from matplotlib.figure import Figure
from io import StringIO, BytesIO
from pathlib import Path
from datetime import datetime, date as dt_date, time as dt_time
from ipylab import JupyterFrontEnd
import asyncio
import requests
from typing import Any, Dict, List, Optional, Union, Tuple

import re
import time


__SESSION__: Optional[requests.Session] = None
__BASEURL__: Optional[str] = None  
__VERIFY_SSL__: bool = True
__EXPID__: Optional[int] = None

__APP__ = JupyterFrontEnd()


# -----------------------
# Low-level HTTP helpers
# -----------------------

class ElabAPIError(RuntimeError):
    pass


def _normalize_baseurl(host: str) -> str:
    host = host.strip()
    if host.endswith("/"):
        host = host[:-1]
    if "/api/v2" in host:
        return host
    return host + "/api/v2"


def _require_connected() -> Tuple[requests.Session, str]:
    if __SESSION__ is None or __BASEURL__ is None:
        raise RuntimeError("Not connected to eLabFTW server")
    return __SESSION__, __BASEURL__


def _request(
    method: str,
    path: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    stream: bool = False,
    timeout: Union[float, Tuple[float, float]] = (10.0, 120.0),
) -> requests.Response:
    sess, base = _require_connected()
    url = f"{base}{path}"

    try:
        r = sess.request(
            method=method.upper(),
            url=url,
            params=params,
            json=json_body,
            data=data,
            files=files,
            stream=stream,
            timeout=timeout,
            verify=__VERIFY_SSL__,
        )
    except requests.RequestException as e:
        raise ElabAPIError(f"HTTP request failed: {method} {url}: {e}") from e

    if not r.ok:
        # Try to include server JSON error if present
        msg = f"API error {r.status_code} for {method} {url}"
        try:
            payload = r.json()
            msg += f": {payload}"
        except Exception:
            txt = (r.text or "").strip()
            if txt:
                msg += f": {txt}"
        raise ElabAPIError(msg)

    return r


def _get_json(path: str, *, params: Optional[Dict[str, Any]] = None) -> Any:
    r = _request("GET", path, params=params, stream=False)
    if r.status_code == 204:
        return None
    return r.json()


def _patch_json(path: str, body: Dict[str, Any]) -> Any:
    r = _request("PATCH", path, json_body=body, stream=False)
    if r.status_code == 204:
        return None
    return r.json()

def _post_json(path: str, body: Dict[str, Any], *, params: Optional[Dict[str, Any]] = None) -> Tuple[Any, int, Dict[str, Any]]:
    r = _request("POST", path, params=params, json_body=body, stream=False)

    status_code = r.status_code
    headers = dict(r.headers)

    if status_code == 204:
        return None, status_code, headers

    # empty / whitespace body
    if not r.text or not r.text.strip():
        return None, status_code, headers

    # JSON body (if any)
    try:
        return r.json(), status_code, headers
    except ValueError:
        raise RuntimeError(f"Non-JSON response ({status_code}): {r.text[:500]}")

# -----------------------
# General functions
# -----------------------

def connect(host: str, apikey: str, verify_ssl: bool = True):
    """Connect to eLabFTW server API v2.
    host: base instance URL or full .../api/v2
    apikey: API key
    """
    global __SESSION__, __BASEURL__, __VERIFY_SSL__
    __VERIFY_SSL__ = verify_ssl
    __BASEURL__ = _normalize_baseurl(host)

    s = requests.Session()
    # eLabFTW expects API key in Authorization header
    s.headers.update(
        {
            "Authorization": apikey,
            "Accept": "application/json",
        }
    )
    __SESSION__ = s


def disconnect():
    global __SESSION__, __BASEURL__
    if __SESSION__ is not None:
        __SESSION__.close()
    __SESSION__ = None
    __BASEURL__ = None


def get_teamid() -> int:
    """Return the team id associated with the api key used."""
    team = _get_json("/teams/current")  # id can be "current" per API :contentReference[oaicite:4]{index=4}
    return int(team["id"])


def list_experiments(
    searchstring: str = "",
    tags: List[str] = [],
    only_current_team: bool = True,
    list_keys: List[str] = ["id"],
) -> List[Any]:
    """Return a list of experiments matching searchstring and tags."""
    # API uses tags[] parameter in docs; requests supports list values
    # Many servers accept either "tags[]" or "tags" – we send "tags[]" explicitly.
    params: List[Tuple[str, Any]] = [("q", searchstring), ("limit", 9999)]
    for t in tags:
        params.append(("tags[]", t))

    exps = _get_json("/experiments", params=dict(params))  # may flatten duplicates on dict
    # If your server requires repeated tags[] keys, use params as list of tuples:
    # exps = _request("GET", "/experiments", params=params).json()

    teamid = get_teamid()
    explist = []
    for exp in exps:
        if (int(exp.get("team", -1)) == teamid) or (not only_current_team):
            if len(list_keys) == 1:
                explist.append(exp.get(list_keys[0]))
            else:
                expdata = {key: exp.get(key) for key in list_keys}
                explist.append(expdata)
    return explist


def open_experiment(expid: int, returndata: bool = False):
    """Open an experiment on eLabFTW (sets global __EXPID__)."""
    global __EXPID__
    __EXPID__ = expid
    exp = _get_json(f"/experiments/{expid}")
    if returndata:
        return exp


def close_experiment():
    global __EXPID__
    __EXPID__ = None
    
def create_experiment(title="Untitled", body="", content_type=2):
    """
    Create an experiment on eLabFTW and return its id.
    """
    global __EXPID__
    
    # Build request payload according to API v2 docs
    payload = {
        "title": title,
        "body": body,
        "content_type": content_type,  # 1 (html) / 2 (MarkDown) depending on your instance mapping
    }

    response, status_code, headers = _post_json(f"/experiments", body=payload)
    
    
    if status_code in (200, 201):
        location = headers.get("Location") or headers.get("location")
        if not location:
            # sometimes id is returned in JSON
            if isinstance(response, dict) and "id" in response:
                exp_id = int(response["id"])
            else:
                raise RuntimeError(f"Created experiment but no Location header and no id in response: {response!r}")
        else:
            exp_id = int(location.rstrip("/").split("/")[-1])

        __EXPID__ = exp_id
        return exp_id

    raise RuntimeError(f"Could not create experiment (status={status_code}). Response: {response!r}")

# --------------------------------
# Get Info about eLabFTW 
# --------------------------------
def get_info():
     """Return the public info payload of the eLabFTW instance."""
     return _get_json("/info")

# -----------------------
# Read experiment data
# -----------------------

def __conv_df_to_np(df: pd.DataFrame) -> dict:
    data = {}
    for name, column in df.items():
        base = name
        cno = 0
        while name in data.keys():
            cno += 1
            name = f"{base}_{cno}"
        data[name] = np.array(column.to_numpy(), dtype=float)
    return data


def get_experimentdata(expid: int = None) -> Dict[str, Any]:
    if expid is None:
        global __EXPID__
        expid = __EXPID__
    if expid is None:
        raise RuntimeError("No experiment opened or specified")
    return _get_json(f"/experiments/{expid}")


def get_maintext(format: str = "html", expid: int = None) -> str:
    exp = get_experimentdata(expid)
    if format == "html":
        return exp.get("body_html") or ""
    return exp.get("body") or ""


def get_table_data(
    tableidx: int = 0,
    header: bool = True,
    decimal: str = ".",
    thousands: str = None,
    datatype: str = "np",
    expid: int = None,
):
    exp = get_experimentdata(expid)

    if thousands is None:
        thousands = "." if decimal == "," else ","

    tables = pd.read_html(StringIO(exp.get("body_html") or ""), decimal=decimal, thousands=thousands)

    if header:
        table = tables[tableidx].iloc[1:]
        table.columns = tables[tableidx].iloc[0]
    else:
        table = tables[tableidx]

    if datatype == "df":
        return table
    if datatype == "np":
        return __conv_df_to_np(table)
    raise RuntimeError("Wrong datatype")


def get_extrafields(fieldname: str = None, expid: int = None):
    exp = get_experimentdata(expid)
    md_raw = exp.get("metadata") or "{}"
    data = json.loads(md_raw).get("extra_fields", {})

    if fieldname is None:
        return data

    value = data[fieldname]["value"]
    ftype = data[fieldname].get("type", "text")
    if ftype == "number":
        return float(value)
    if ftype == "datetime-local":
        return datetime.fromisoformat(value)
    if ftype == "date":
        return dt_date.fromisoformat(value)
    if ftype == "time":
        return dt_time.fromisoformat(value)
    return value


# -----------------------
# Read files (uploads)
# -----------------------

def __read_uploads(expid: int) -> List[Dict[str, Any]]:
    # Endpoint: /{entity_type}/{id}/uploads :contentReference[oaicite:5]{index=5}
    return _get_json(f"/experiments/{expid}/uploads")


def __get_upload_id(expid: int, filename: str) -> Optional[int]:
    uploads = __read_uploads(expid)
    for upload in uploads:
        if upload.get("real_name") == filename:
            return int(upload["id"])
    return None


def __get_upload_id_by_long_name(expid: int, long_name: str) -> Optional[int]:
    uploads = __read_uploads(expid)
    for upload in uploads:
        if upload.get("long_name") == long_name:
            return int(upload["id"])
    return None


def get_file_data(filename: str, filename_is_long_name: bool = False, expid: int = None) -> bytes:
    if expid is None:
        global __EXPID__
        expid = __EXPID__
    if expid is None:
        raise RuntimeError("No experiment opened or specified")

    uploadid = (
        __get_upload_id_by_long_name(expid, filename)
        if filename_is_long_name
        else __get_upload_id(expid, filename)
    )

    if uploadid is None:
        raise RuntimeError("File not found in eLabFTW experiment")

    # Binary download: GET /{entity_type}/{id}/uploads/{subid}?format=binary :contentReference[oaicite:6]{index=6}
    r = _request(
        "GET",
        f"/experiments/{expid}/uploads/{uploadid}",
        params={"format": "binary"},
        stream=True,
    )
    return r.content


def get_file_csv_data(
    filename: str,
    filename_is_long_name: bool = False,
    header: bool = True,
    sep: str = ",",
    decimal: str = ".",
    thousands: str = None,
    datatype: str = "np",
    expid: int = None,
):
    filedata = get_file_data(filename, filename_is_long_name, expid).decode("utf-8")

    if thousands is None:
        thousands = "." if decimal == "," else ","

    df = pd.read_csv(
        StringIO(filedata),
        sep=sep,
        header=(0 if header else "infer"),
        decimal=decimal,
        thousands=thousands,
    )

    if datatype == "df":
        return df
    if datatype == "np":
        return __conv_df_to_np(df)
    raise RuntimeError("Wrong datatype")


def get_file_hdf5_data(filename: str, filename_is_long_name: bool = False, expid: int = None):
    filestream = BytesIO(get_file_data(filename, filename_is_long_name, expid))
    return h5py.File(filestream, "r")


# -----------------------
# Update experiment data
# -----------------------

def update_experiment_title(title: str, expid: int=None):
    """Update the title of an experiment.

    Parameters
    ----------
    title : str
        The new title name of the experiment.
    expid : int, optional
        The id of the experiment in eLabFTW to be read.
        If None, the experiment specified by open_experiment() or create_experiment() is used.
        The default is None.

    Returns
    -------
    None.

    """
    if expid is None:
        global __EXPID__
        expid = __EXPID__

    if expid is None:
        raise RuntimeError('No experiment opened or specified')

    if not isinstance(title, str):
        raise TypeError("title must be a str")
    _patch_json(f"/experiments/{expid}", body={"title": title})
    

def create_extrafield(
    fieldname: str,
    value,
    fieldtype: str = "text",
    unit: str = None,
    units=None,
    description: str = None,
    groupname: str = None,
    readonly: bool = False,
    required: bool = False,
    position: int = None,
    options: list = None,
    expid: int = None,
):
    if expid is None:
        global __EXPID__
        expid = __EXPID__
    if expid is None:
        raise RuntimeError("No experiment opened or specified")

    exp = get_experimentdata(expid)
    if exp.get("metadata") is None:
        metadata = {"extra_fields": {}}
    else:
        metadata = json.loads(exp["metadata"])
        metadata.setdefault("extra_fields", {})

    if fieldname in metadata["extra_fields"]:
        update_extrafield(fieldname, value, expid)
        return

    groupid = None
    if groupname is not None:
        metadata.setdefault("elabftw", {})
        metadata["elabftw"].setdefault("extra_fields_groups", [])
        groups = metadata["elabftw"]["extra_fields_groups"]

        existing = [g["id"] for g in groups if g.get("name") == groupname]
        groupid = existing[0] if existing else None

        if groupid is None:
            groupid = (max([g["id"] for g in groups]) + 1) if groups else 1
            groups.append({"id": groupid, "name": groupname})

    if fieldtype == "datetime":
        fieldtype = "datetime-local"

    metadata["extra_fields"][fieldname] = {"type": fieldtype}

    if not isinstance(value, str):
        if fieldtype == "number":
            value = str(value)
        elif fieldtype == "datetime-local":
            value = datetime.isoformat(value.replace(second=0, microsecond=0))
        elif fieldtype == "date":
            value = dt_date.isoformat(value)
        elif fieldtype == "time":
            value = dt_time.isoformat(value.replace(second=0, microsecond=0))

    metadata["extra_fields"][fieldname]["value"] = value

    if unit is not None:
        metadata["extra_fields"][fieldname]["unit"] = unit
        if units is None:
            units = [unit]
    if units is not None:
        metadata["extra_fields"][fieldname]["units"] = units
    if description is not None:
        metadata["extra_fields"][fieldname]["description"] = description
    if groupid is not None:
        metadata["extra_fields"][fieldname]["group_id"] = groupid
    if readonly:
        metadata["extra_fields"][fieldname]["readonly"] = True
    if required:
        metadata["extra_fields"][fieldname]["required"] = True
    if position is not None:
        metadata["extra_fields"][fieldname]["position"] = position
    
    if fieldtype == "checkbox":
        if isinstance(value, str):
            if value not in ("on", "off"):
                raise ValueError("checkbox value must be 'on' or 'off'")
        else:
            raise ValueError("checkbox value must be a string 'on' or 'off'")

    metadata["extra_fields"][fieldname]["value"] = value

    if fieldtype == "select":
        options = options or []
        if value not in options:
            options.append(value)
        metadata["extra_fields"][fieldname]["options"] = options
    
    
    # PATCH /experiments/{id} with {"metadata": "<json string>"} :contentReference[oaicite:7]{index=7}
    _patch_json(f"/experiments/{expid}", {"metadata": json.dumps(metadata)})


def update_extrafield(fieldname: str, value, expid: int = None):
    if expid is None:
        global __EXPID__
        expid = __EXPID__
    if expid is None:
        raise RuntimeError("No experiment opened or specified")

    if not isinstance(value, str):
        exp = get_experimentdata(expid)
        metadata = json.loads(exp.get("metadata") or "{}")
        fieldtype = metadata["extra_fields"][fieldname]["type"]

        if fieldtype == "number":
            value = str(value)
        elif fieldtype == "datetime-local":
            value = datetime.isoformat(value.replace(second=0, microsecond=0))
        elif fieldtype == "date":
            value = dt_date.isoformat(value)
        elif fieldtype == "time":
            value = dt_time.isoformat(value.replace(second=0, microsecond=0))

    # Same behavior as elabapi_python: PATCH with action "updatemetadatafield"
    _patch_json(f"/experiments/{expid}", {"action": "updatemetadatafield", fieldname: value})


def delete_extrafield(fieldname: str, expid: int = None):
    if expid is None:
        global __EXPID__
        expid = __EXPID__
    if expid is None:
        raise RuntimeError("No experiment opened or specified")

    exp = get_experimentdata(expid)
    metadata = json.loads(exp.get("metadata") or "{}")
    if "extra_fields" in metadata and fieldname in metadata["extra_fields"]:
        del metadata["extra_fields"][fieldname]

    _patch_json(f"/experiments/{expid}", {"metadata": json.dumps(metadata)})

def replace_experiment_metadata(metadata: dict, expid: int=None):
    """Update the metadata of an experiment.

    Parameters
    ----------
    metadata : dict
        A JSON based metadata entry following a special schema in eLabFTW.
    expid : int, optional
        The id of the experiment in eLabFTW to be read.
        If None, the experiment specified by open_experiment() or create_experiment() is used.
        The default is None.

    Returns
    -------
    None.

    """

    if expid is None:
        global __EXPID__
        expid = __EXPID__
    if expid is None:
        raise RuntimeError("No experiment opened or specified")
    
    if not isinstance(metadata, dict):
        raise TypeError("metadata must be a dict")
    _patch_json(f"/experiments/{expid}", {"metadata": json.dumps(metadata)})

def get_steps(expid: int = None) -> List[Dict[str, Any]]:
    """Get all steps for an experiment.
    
    Parameters
    ----------
    expid : int, optional
        The experiment ID. If None, uses the currently opened experiment.
        
    Returns
    -------
    list of dict
        A list of step dictionaries containing step information
        
    Raises
    ------
    RuntimeError
        If no experiment is opened or specified and no experiment ID is provided
    """
    if expid is None:
        global __EXPID__
        expid = __EXPID__
    if expid is None:
        raise RuntimeError("No experiment opened or specified")
    return _get_json(f"/experiments/{expid}/steps")

def create_step(expid: int = None, body: Optional[str] = None) -> int:
    """Create a new step for an experiment.
    
    Parameters
    ----------
    expid : int, optional
        The experiment ID (uses current if not specified)
    body : str, optional
        The body content for the new step
        
    Returns
    -------
    int
        The ID of the newly created step
        
    Raises
    ------
    RuntimeError
        If the step creation fails
    ValueError
        If body is not a string
    """
    if expid is None:
        global __EXPID__
        expid = __EXPID__
    if expid is None:
        raise RuntimeError("No experiment opened or specified")
    
    # Validate input
    if not isinstance(body, str):
        raise ValueError("body must be a string")
    
    payload = {
        "body": body,
    }
    
    response, status_code, headers = _post_json(f"/experiments/{expid}/steps", body=payload)                                                                                                                                           
    if status_code in (200, 201):
        location = headers.get("Location") or headers.get("location")
        if not location:
            # sometimes id is returned in JSON
            if isinstance(response, dict) and "id" in response:
                step_id = int(response["id"])
                return step_id
            else:
                raise RuntimeError(f"Created step but no Location header and no id in response: {response!r}")
        else:
            step_id = int(location.rstrip("/").split("/")[-1])
            return step_id
    
    raise RuntimeError(f"Could not create step (status={status_code}). Response: {response!r}")                                                                                                                                        

def update_step(stepid: int, expid: int = None, body: Optional[str] = None, toggle_finished: Optional[bool] = None) -> Dict[str, Any]:
    """Update an existing step.
    
    Parameters
    ----------
    stepid : int
        The ID of the step to update
    expid : int, optional
        The experiment ID (uses current if not specified)
    body : str, optional
        New body content for the step
    toggle_finished : bool, optional
        Toggle the finished status of the step
        
    Returns
    -------
    dict
        Status information about the update operation
    """
    if expid is None:
        global __EXPID__
        expid = __EXPID__
    if expid is None:
        raise RuntimeError("No experiment opened or specified")
    
    # Validate inputs
    if not isinstance(stepid, int) or stepid <= 0:
        raise ValueError("stepid must be a positive integer")
    
    if body is not None and not isinstance(body, str):
        raise TypeError("body must be a string")
    
    if toggle_finished is not None and not isinstance(toggle_finished, bool):
        raise TypeError("toggle_finished must be a boolean")
    
    responses: List[Any] = []
    
    if body is not None:
        resp = _patch_json(f"/experiments/{expid}/steps/{stepid}", {"body": body})
        responses.append({"type": "update", "response": resp})
    if toggle_finished is not None:
        # For finishing a step, we need to use the action parameter correctly
        if toggle_finished:
            resp = _patch_json(f"/experiments/{expid}/steps/{stepid}", {"action": "finish"})
            responses.append({"type": "finish", "response": resp})
    
    return responses

def delete_step(stepid: int, expid: int = None) -> None:
    """Delete a step from an experiment.
    
    Parameters
    ----------
    stepid : int
        The ID of the step to delete
    expid : int, optional
        The experiment ID. If None, uses the currently opened experiment.
        
    Raises
    ------
    RuntimeError
        If no experiment is opened or specified and no experiment ID is provided
    """
    if expid is None:
        global __EXPID__
        expid = __EXPID__
    if expid is None:
        raise RuntimeError("No experiment opened or specified")
    
    _request("DELETE", f"/experiments/{expid}/steps/{stepid}")

# -----------------------
# Upload files
# -----------------------

def upload_file(file: str, comment: str, replacefile: bool = True, expid: int = None):
    if expid is None:
        global __EXPID__
        expid = __EXPID__
    if expid is None:
        raise RuntimeError("No experiment opened or specified")

    uploadid = __get_upload_id(expid, os.path.basename(file)) if replacefile else None

    with open(file, "rb") as fh:
        files = {"file": fh}
        data = {"comment": comment}

        if uploadid is None:
            # POST /experiments/{id}/uploads :contentReference[oaicite:8]{index=8}
            _request("POST", f"/experiments/{expid}/uploads", data=data, files=files)
        else:
            # Replace: POST /experiments/{id}/uploads/{subid} :contentReference[oaicite:9]{index=9}
            _request("POST", f"/experiments/{expid}/uploads/{uploadid}", data=data, files=files)


def upload_image_from_figure(
    fig: Figure,
    filename: str,
    comment: str,
    replacefile: bool = True,
    format: str = "png",
    dpi="figure",
    bbox_inches="tight",
    expid: int = None,
):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpfile = os.path.join(tmpdir, Path(filename).with_suffix("." + format))
        fig.savefig(tmpfile, format=format, facecolor="white", dpi=dpi, bbox_inches=bbox_inches)
        upload_file(tmpfile, comment, replacefile, expid=expid)


def upload_csv_data(
    data,
    filename: str,
    comment: str,
    replacefile: bool = True,
    index: bool = False,
    expid: int = None,
):
    if isinstance(data, pd.DataFrame):
        df = data
    else:
        df = pd.DataFrame(data)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpfile = os.path.join(tmpdir, filename)
        df.to_csv(tmpfile, index=index)
        upload_file(tmpfile, comment, replacefile, expid=expid)


# -----------------------
# Jupyter notebook upload
# -----------------------

def _kernel_id_from_connection_file() -> str:
    import ipykernel
    cf = ipykernel.get_connection_file()
    m = re.search(r"kernel-(.+)\.json$", cf)
    if not m:
        raise RuntimeError(f"Cannot parse kernel id from connection file: {cf}")
    return m.group(1)

def _list_running_servers():
    try:
        from jupyter_server.serverapp import list_running_servers
        return list(list_running_servers())
    except Exception:
        from notebook.notebookapp import list_running_servers
        return list(list_running_servers())

def _find_notebook_path_via_sessions() -> Path:
    kid = _kernel_id_from_connection_file()
    servers = _list_running_servers()
    if not servers:
        raise RuntimeError("No running Jupyter servers found via list_running_servers().")

    last_err = None
    for s in servers:
        url = (s.get("url") or "").rstrip("/")
        token = s.get("token") or ""
        nbdir = s.get("notebook_dir") or s.get("root_dir") or ""

        sessions_url = f"{url}/api/sessions"
        params = {"token": token} if token else {}

        try:
            r = requests.get(sessions_url, params=params, timeout=(5, 20))
            if r.status_code != 200:
                last_err = f"{sessions_url} -> {r.status_code}: {r.text[:200]}"
                continue
            sessions = r.json()
        except Exception as e:
            last_err = repr(e)
            continue

        for sess in sessions:
            k = (sess.get("kernel") or {})
            if k.get("id") == kid:
                path = sess.get("path") or (sess.get("notebook") or {}).get("path")
                if not path:
                    raise RuntimeError("Matched session but could not find notebook path in session JSON.")
                return (Path(nbdir) / Path(path)).resolve()

    raise RuntimeError(f"Could not locate current notebook via /api/sessions. Last error: {last_err}")

def upload_this_jupyternotebook(
    comment: str,
    replacefile: bool = True,
    expid: int = None,
    warn_if_older_than_s: int = 20,
):
    """
    Upload current notebook file as it exists on disk.
    User should save (Ctrl+S) before calling to include latest changes.
    """
    if expid is None:
        global __EXPID__
        expid = __EXPID__
    if expid is None:
        raise RuntimeError("No experiment opened or specified")

    nb_path = _find_notebook_path_via_sessions()
    if not nb_path.exists():
        raise FileNotFoundError(f"Notebook file not found on disk: {nb_path}")

    st = nb_path.stat()
    age_s = time.time() - st.st_mtime

    if age_s > warn_if_older_than_s:
        print(
            f"[elab] Warning: Notebook on disk was last modified {age_s:.1f}s ago.\n"
            f"       If you changed cells recently, press Ctrl+S first to save, then upload again."
        )

    print(f"[elab] Uploading notebook from disk: {nb_path}")
    upload_file(str(nb_path), comment, replacefile, expid=expid)
    print("[elab] Done.")
    
