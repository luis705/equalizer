import numpy as np
from scipy import signal


def create_filter(freqs, gains, fs, order):
    gains = np.power(10.0, (np.divide(gains, 20)))
    return signal.firwin2(order, freqs, gains, fs=fs)


def process_signal(input, filter, gain):
    return signal.convolve(input, filter, mode='same') * gain
