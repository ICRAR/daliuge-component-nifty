import pytest
import numpy as np

from dlg.exceptions import DaliugeException
from daliuge_component_nifty import MS2DirtyApp, CudaMS2DirtyApp, CudaDirty2MSApp
from daliuge_component_nifty.ms import MSReadApp
from dlg.drop import InMemoryDROP, FileDROP

given = pytest.mark.parametrize


def test_MSReadApp_exceptions():
    app = MSReadApp("a", "a")

    with pytest.raises(DaliugeException) as e:
        app.run()


def test_MSReadApp():
    app = MSReadApp("a", "a")
    
    ms_drop = FileDROP("ms", "ms")
    ms_drop.filepath = "/tmp/.dlg/workspace/mwa-split.ms"
    ms_drop.initialize()
    print(ms_drop.path)
    app.addInput(ms_drop)

    uvw_drop = InMemoryDROP("uvw", "uvw")
    app.addOutput(uvw_drop)

    freq_drop = InMemoryDROP("freq", "freq")
    app.addOutput(freq_drop)

    vis_drop = InMemoryDROP("vis", "vis")
    app.addOutput(vis_drop)

    weight_spectrum_drop = InMemoryDROP("weight_spectrum", "weight_spectrum")
    app.addOutput(weight_spectrum_drop)

    app.run()
