from scipy.io import wavfile

from eq import create_filter, process_signal

Fs = 96000
order = 2**10 + 1

freqs = [
    0,
    16,
    20,
    25,
    31,
    40,
    50,
    63,
    80,
    100,
    125,
    160,
    200,
    250,
    315,
    400,
    500,
    630,
    800,
    1000,
    1250,
    1600,
    2000,
    2500,
    3150,
    4000,
    5000,
    6300,
    8000,
    10000,
    12500,
    16000,
    20000,
    25000,
    Fs / 2,
]

gains = [
    -100,
    -100,
    -100,
    -100,
    -100,
    -100,
    -100,
    -100,
    -100,
    -100,
    -100,
    -100,
    -100,
    -100,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
]

b = create_filter(freqs, gains, Fs, order)
Fs, sinal = wavfile.read('signal.wav')
output = process_signal(sinal, b, 512)
wavfile.write('output.wav', Fs, output)
