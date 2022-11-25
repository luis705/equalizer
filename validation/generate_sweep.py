import numpy as np
from scipy.io import wavfile
from scipy.signal import chirp

sampleRate = 96000
frequency = 440
length = 30

t = np.linspace(0, length, sampleRate * length)  #  Produces a 5 second Audio-File
y = chirp(t, 20, 30, 20000, method='logarithmic')

wavfile.write('validation/chirp.wav', sampleRate, y)
