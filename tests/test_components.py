import pytest
import numpy as np

from dlg.exceptions import DaliugeException
from daliuge_component_nifty import MS2DirtyApp, CudaMS2DirtyApp, CudaDirty2MSApp
from daliuge_component_nifty.ms import MSReadApp, numpy_to_drop
from dlg.drop import InMemoryDROP

given = pytest.mark.parametrize


def test_MS2DirtyApp_exceptions():
    app = MS2DirtyApp("a", "a")

    with pytest.raises(DaliugeException) as e:
        app.run()


def test_MS2DirtyApp():
    app = MS2DirtyApp("a", "a")

    # Test data dimensions.
    num_rows = 16
    num_chan = 1
    image_size = 64

    # Create the frequency axis.
    freq_start_hz = 299792458.0
    freq_inc_hz = 1.0
    freq = np.linspace(freq_start_hz,
                        freq_start_hz + (num_chan - 1) * freq_inc_hz,
                        num_chan)

    # Allocate input arrays.
    vis = np.zeros((num_rows, num_chan), dtype=np.complex128)
    weight_spectrum = np.ones((num_rows, num_chan), dtype=np.float64)
    uvw = np.zeros((num_rows, 3), dtype=np.float64)

    # Generate synthetic data.
    for i in range(num_rows):
        vis[i, 0] = 1 + 1j*(i + 1) / 10
        uvw[i, 0] = (float(i) * image_size) / num_rows - image_size // 2
        uvw[i, 1] = (float(i) * image_size) / num_rows - image_size // 2
        uvw[i, 2] = 1.0
    
    uvw_drop = InMemoryDROP("uvw", "uvw")
    numpy_to_drop(uvw, uvw_drop)
    app.addInput(uvw_drop)

    freq_drop = InMemoryDROP("freq", "freq")
    numpy_to_drop(freq, freq_drop)
    app.addInput(freq_drop)

    vis_drop = InMemoryDROP("vis", "vis")
    numpy_to_drop(vis, vis_drop)
    app.addInput(vis_drop)

    weight_spectrum_drop = InMemoryDROP("weight_spectrum", "weight_spectrum")
    numpy_to_drop(weight_spectrum, weight_spectrum_drop)
    app.addInput(weight_spectrum_drop)
    app.addOutput(InMemoryDROP("image", "image"))

    app.run()


def test_CudaMS2DirtyApp_exceptions():
    app = CudaMS2DirtyApp("a", "a")

    with pytest.raises(DaliugeException) as e:
        app.run()


def test_CudaMS2DirtyApp():
    app = CudaMS2DirtyApp("a", "a")

    # Test data dimensions.
    num_rows = 16
    num_chan = 1
    image_size = 64

    # Create the frequency axis.
    freq_start_hz = 299792458.0
    freq_inc_hz = 1.0
    freq = np.linspace(freq_start_hz,
                       freq_start_hz + (num_chan - 1) * freq_inc_hz,
                       num_chan)

    # Allocate input arrays.
    vis = np.zeros((num_rows, num_chan), dtype=np.complex128)
    weight_spectrum = np.ones((num_rows, num_chan), dtype=np.float64)
    uvw = np.zeros((num_rows, 3), dtype=np.float64)

    # Generate synthetic data.
    for i in range(num_rows):
        vis[i, 0] = 1 + 1j*(i + 1) / 10
        uvw[i, 0] = (float(i) * image_size) / num_rows - image_size // 2
        uvw[i, 1] = (float(i) * image_size) / num_rows - image_size // 2
        uvw[i, 2] = 1.0
    
    uvw_drop = InMemoryDROP("uvw", "uvw")
    numpy_to_drop(uvw, uvw_drop)
    app.addInput(uvw_drop)

    freq_drop = InMemoryDROP("freq", "freq")
    numpy_to_drop(freq, freq_drop)
    app.addInput(freq_drop)

    vis_drop = InMemoryDROP("vis", "vis")
    numpy_to_drop(vis, vis_drop)
    app.addInput(vis_drop)

    weight_spectrum_drop = InMemoryDROP("weight_spectrum", "weight_spectrum")
    numpy_to_drop(weight_spectrum, weight_spectrum_drop)
    app.addInput(weight_spectrum_drop)

    app.addOutput(InMemoryDROP("image", "image"))

    app.run()
