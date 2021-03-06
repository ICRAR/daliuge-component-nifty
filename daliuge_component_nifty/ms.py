#
#    ICRAR - International Centre for Radio Astronomy Research
#    (c) UWA - The University of Western Australia, 2017
#    Copyright by UWA (in the framework of the ICRAR)
#    All rights reserved
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#    MA  02110-1301, USA.

import os
import io
import logging
import pickle
import urllib.error
import urllib.request

import time
import numpy as np
import casacore
import casacore.tables
from dataclasses import dataclass, astuple
from typing import Optional, Tuple

from dlg import droputils, utils
from dlg.drop import BarrierAppDROP, BranchAppDrop, ContainerDROP
from dlg.exceptions import DaliugeException
from dlg.meta import dlg_float_param, dlg_string_param
from dlg.meta import dlg_bool_param, dlg_int_param
from dlg.meta import dlg_component, dlg_batch_input
from dlg.meta import dlg_batch_output, dlg_streaming_input
from dlg.meta import (dlg_batch_input, dlg_batch_output, dlg_component,
                      dlg_float_param, dlg_int_param, dlg_streaming_input,
                      dlg_string_param, dlg_bool_param)

from dlg.apps.pyfunc import serialize_data, deserialize_data

logger = logging.getLogger(__name__)

from dlg.io import OpenMode

def drop_to_numpy(drop) -> np.ndarray:
    bio = drop.getIO()
    bio.open(OpenMode.OPEN_READ)
    buf = bio.buffer()
    res = np.load(io.BytesIO(buf))
    bio.close()
    return res

def numpy_to_drop(array: np.ndarray, drop):
    buf = io.BytesIO()
    np.save(buf, array)
    drop.write(buf.getbuffer())

@dataclass
class PortOptions:
    table: casacore.tables.table
    name: str
    dtype: str
    rows: range
    slicer: Tuple[slice]

##
# @brief MSReadApp
# @details Extracts measurement set tables to numpy arrays.
# @par EAGLE_START
# @param category PythonApp
# @param[in] param/appclass appclass/daliuge_component_nifty.ms.MSReadApp/String/readonly/False/
#     \~English Application class
# @param[in] param/row_start row_start/0/Integer/readwrite/False/
#     \~English first row to read
# @param[in] param/row_end row_end/None/Integer/readwrite/False/
#     \~English last row to read
# @param[in] param/pol_start pol_start/0/Integer/readwrite/False/
#     \~English first pol to read
# @param[in] param/pol_end pol_end/None/Integer/readwrite/False/
#     \~English last pol to read
# @param[in] port/ms ms/PathBasedDrop/
#     \~English PathBasedDrop to a Measurement Set
# @param[out] port/uvw uvw/ndarray/
#     \~English Port containing UVWs as a numpy ndarray
# @param[out] port/freq freq/ndarray/
#     \~English Port containing frequencies as a numpy ndarray
# @param[out] port/vis vis/ndarray/
#     \~English Port containing visibilities as a numpy ndarray
# @param[out] port/weight_spectrum weight_spectrum/ndarray/
#     \~English Port containing weight spectrum as a numpy ndarray
# @param[out] port/flag flag/ndarray/
#     \~English Port containing flags as a numpy ndarray
# @param[out] port/weight weight/ndarray/
#     \~English Port containing weights as a numpy ndarray
# @par EAGLE_END
class MSReadApp(BarrierAppDROP):
    component_meta = dlg_component('MSReadApp', 'MeasurementSet Read App',
                                   [dlg_batch_input('binary/*', [])],
                                   [dlg_batch_output('binary/*', [])],
                                   [dlg_streaming_input('binary/*')])
    row_start = dlg_int_param('row_start', 0)
    row_end = dlg_int_param('row_end', None)
    pol_start = dlg_int_param('pol_start', 0)
    pol_end = dlg_int_param('pol_end', None)

    def run(self):
        if len(self.inputs) < 1:
            raise DaliugeException(f"MSReadApp has {len(self.inputs)} input drops but requires at least 1")
        self.ms_path = self.inputs[0].path
        assert os.path.exists(self.ms_path)
        assert casacore.tables.tableexists(self.ms_path)
        msm = casacore.tables.table(self.ms_path, readonly=True)
        mssw = casacore.tables.table(msm.getkeyword("SPECTRAL_WINDOW"), readonly=True)

        if self.row_end == None:
            self.row_end = -1
        row_range = (self.row_start, self.row_end)
        
        # (baseline, channels, pols)
        tensor_slice = (slice(0, None), slice(0, None), slice(self.pol_start, self.pol_end))

        # table, name, dtype, slicer
        portOptions = [
            PortOptions(msm,  "UVW",                                                "float64",    row_range,   tensor_slice[0]),
            PortOptions(mssw, "CHAN_FREQ",                                          "float64",    (0, -1),     tensor_slice[1]),
            PortOptions(msm,  "REPLACEMASKED(DATA[FLAG||ANTENNA1==ANTENNA2], 0)",   "complex128", row_range,   tensor_slice),
            PortOptions(msm,  "REPLACEMASKED(WEIGHT_SPECTRUM[FLAG], 0)",            "float64",    row_range,   tensor_slice),
            PortOptions(msm,  "FLAG",                                               "bool",       row_range,   tensor_slice),
            PortOptions(msm,  "WEIGHT",                                             "float64",    row_range,   tensor_slice[0]),
        ]

        for i in range(len(portOptions)):
            if len(self.outputs) >= i + 1:
                outputDrop = self.outputs[i]
                opt = portOptions[i]
                data = opt.table.query(columns=f"{opt.name} as COL", offset=opt.rows[0], limit=opt.rows[1])\
                    .getcol("COL")[opt.slicer]\
                    .squeeze()\
                    .astype(opt.dtype)
                numpy_to_drop(data, outputDrop)


##
# @brief MSCopyUpdateApp
# @details Copies an input measurement set and updates the specified table.
# @par EAGLE_START
# @param category PythonApp
# @param[in] param/appclass appclass/daliuge_component_nifty.ms.MSCopyUpdateApp/String/readonly/False/
#     \~English Application class
# @param[in] param/start_row start_row/0/Integer/readwrite/False/
#     \~English start row to update tables from
# @param[in] param/start_row start_row//Integer/readwrite/False/
#     \~English number of table rows to update
# @param[in] port/ms ms/PathBasedDrop/
#     \~English PathBasedDrop of a Measurement Set
# @param[in] port/vis vis/ndarray/
#     \~English Port containing visibilities as a numpy ndarray
# @param[out] port/ms ms/PathbasedDrop/
#     \~English output measurement set
# @par EAGLE_END
class MSCopyUpdateApp(BarrierAppDROP):
    component_meta = dlg_component('MSCopyUpdateApp', 'MeasurementSet Copy and Update App',
                                   [dlg_batch_input('binary/*', [])],
                                   [dlg_batch_output('binary/*', [])],
                                   [dlg_streaming_input('binary/*')])
    start_row = dlg_int_param('start_row', 0)
    num_rows = dlg_int_param('num_rows', None)

    def run(self):
        self.ms_path = self.inputs[0].path
        assert os.path.exists(self.ms_path)
        assert casacore.tables.tableexists(self.ms_path)
        self.copyOutputs()
        self.updateOutputs()

    def copyOutputs(self):
        #self.copyRecursive(self.inputs[0])
        for outputDrop in self.outputs:
            cmd = f"cp -r {self.inputs[0].path} {outputDrop.path}"
            os.system(cmd)
        

    def updateOutputs(self):
        for outputDrop in self.outputs:
            msm = casacore.tables.table(outputDrop.path, readonly=False)  # main table
            mssw = casacore.tables.table(msm.getkeyword("SPECTRAL_WINDOW"), readonly=True)

            portOptions = [
                (msm, "DATA"),
                #(msm, "UVW"),
                #(mssw, "CHAN_FREQ"),
                #(msm, "WEIGHT")
            ]
            port_offset = 1
            for i in range(len(self.inputs) - port_offset):
                inputDrop = self.inputs[i+port_offset]
                table = portOptions[i][0]
                name = portOptions[i][1]
                data = drop_to_numpy(inputDrop)
                num_rows = data.shape[0] if self.num_rows is None else self.num_rows
                table.col(name).putcol(data, startrow=self.start_row, nrow=num_rows)

    def copyRecursive(self, inputDrop):
        if isinstance(inputDrop, ContainerDROP):
            for child in inputDrop.children:
                self.copyRecursive(child)
        else:
            for outputDrop in self.outputs:
                droputils.copyDropContents(inputDrop, outputDrop)


##
# @brief MSUpdateApp
# @details Updates the specified ms tables.
# @par EAGLE_START
# @param category PythonApp
# @param[in] param/appclass appclass/daliuge_component_nifty.ms.MsUpdateApp/String/readonly/False/
#     \~English Application class
# @param[in] port/ms ms/PathBasedDrop/
#     \~English PathBasedDrop of a Measurement Set
# @param[in] port/vis vis/ndarray/
#     \~English Port containing visibilities as a numpy ndarray
# @par EAGLE_END
class MSUpdateApp(BarrierAppDROP):
    component_meta = dlg_component('MSUpdateApp', 'MeasurementSet Update App',
                                   [dlg_batch_input('binary/*', [])],
                                   [dlg_batch_output('binary/*', [])],
                                   [dlg_streaming_input('binary/*')])

    def run(self):
        self.ms_path = self.inputs[0].path
        assert os.path.exists(self.ms_path)
        assert casacore.tables.tableexists(self.ms_path)
        self.updateOutputs()

    def updateOutputs(self):
        msm = casacore.tables.table(self.inputs[0].path, readonly=False)  # main table
        mssw = casacore.tables.table(msm.getkeyword("SPECTRAL_WINDOW"), readonly=True)

        portOptions = [
            (msm, "DATA"),
            #(msm, "UVW"),
            #(mssw, "CHAN_FREQ"),
            #(msm, "WEIGHT")
        ]
        port_offset = 1
        for i in range(len(self.inputs) - port_offset):
            inputDrop = self.inputs[i+port_offset]
            table = portOptions[i][0]
            name = portOptions[i][1]
            data = drop_to_numpy(inputDrop)
            table.col(name).putcol(data)
