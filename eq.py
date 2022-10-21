import numpy as np
from scipy import signal


def create_filter(freqs, gains, fs, order):
    gains = np.power(10.0, (np.divide(gains, 20)))
    return signal.firwin2(order, freqs, gains, fs=fs)


def process_signal(input, filter, batch_size, gain):
    output = np.zeros_like(input)
    buffer = np.zeros(batch_size)
    n_batches = input.shape[0] // batch_size
    for batch_n in range(n_batches):
        start = batch_n * batch_size
        end = start + batch_size + 1
        buffer = input[start:end]
        output[start:end] = signal.convolve(buffer, filter, mode='same') * gain
    return output
