from numpy import random
import numpy as np
from scipy.signal import bessel, filtfilt
from scipy.interpolate import pchip_interpolate as _interpolate

def signalAttenuate(signal, sigma) -> np.ndarray:
    # signal is a list of float values (sanitized)
    noise = random.normal(0, sigma, len(signal))
    return signal+noise

def applyBessel(signal,order,cutoff_frequency,sampling_rate) -> tuple[bool,np.ndarray|str]:
    Wn = (2 * cutoff_frequency) / sampling_rate
    # Check filter validity
    try:
        z,p,k = bessel(order,Wn,output='zpk')
        if np.any(np.abs(p) > 0.975):
            raise ValueError("The filter is numerically unstable. Please reduce Filter Poles and/or increase the cutoff frequency.")
    except Exception as e:
        return False, str(e)

    try:
        b,a = bessel(order,Wn)
    except Exception as e:
        return False, str(e) + f" | {Wn=}"
    pad = 3*order
    if len(signal)<pad:
        return False, "Generated signal is too short. Please increase Transition Time and/or Sampling Rate."
    try:
        filtered_signal = filtfilt(b,a,signal,padlen=pad)
    except Exception as e:
        return False, str(e) + f" | {a=} {b=} {pad=}"
    return True, filtered_signal

def interpolate(signal,T,sampling_rate,x_max):
    # calculated = (2*x_max)/(len(signal)-1)
    dt = 1/sampling_rate
    x_old = np.linspace(0,T,len(signal),endpoint=True)
    x_new = np.arange(0,T,dt)
    y = _interpolate(x_old,signal,x_new)
    return y, x_new, x_old