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

import time
import numpy as np
from matplotlib import pyplot as plt
from dataclasses import dataclass, astuple
from typing import Optional, Tuple

from daliuge_component_nifty.ms import drop_to_numpy

from dlg import droputils, utils
from dlg.drop import BarrierAppDROP, BranchAppDrop, ContainerDROP
from dlg.meta import dlg_float_param, dlg_string_param
from dlg.meta import dlg_bool_param, dlg_int_param
from dlg.meta import dlg_component, dlg_batch_input
from dlg.meta import dlg_batch_output, dlg_streaming_input
from dlg.meta import (dlg_batch_input, dlg_batch_output, dlg_component,
                      dlg_float_param, dlg_int_param, dlg_streaming_input,
                      dlg_string_param, dlg_bool_param)

from dlg.apps.pyfunc import serialize_data, deserialize_data

logger = logging.getLogger(__name__)


##
# @brief ImagePlotApp
# @details Updates the specified ms tables.
# @par EAGLE_START
# @param category PythonApp
# @param[in] param/appclass appclass/daliuge_component_nifty.plot.ImagePlotApp/String/readonly/False/
#     \~English Application class
# @param[in] param/title title/image/String/readwrite/False/
# @param[in] port/image image/ndarray/
#     \~English Port containing visibilities as a numpy ndarray
# @param[out] port/png png/png/
#     \~English Port containing coloured PNG image
# @par EAGLE_END
class ImagePlotApp(BarrierAppDROP):
    component_meta = dlg_component('ImagePlotApp', '2D Array Plot App',
                                   [dlg_batch_input('binary/*', [])],
                                   [dlg_batch_output('binary/*', [])],
                                   [dlg_streaming_input('binary/*')])
    title = dlg_string_param("title", "image")

    def run(self):
        plt.gray()
        plt.imshow(drop_to_numpy(self.inputs[0]))
        plt.colorbar()
        plt.title(self.title)
        plt.savefig(self.outputs[0], format='png')
        plt.close()
