import matplotlib.pyplot as plt
import numpy as np
import pywt
from scipy.signal import spectrogram

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import spectrogram

def plot_all(data, rate):
    # Create time vector
    time = np.arange(0, len(data)) / rate

    # Compute the spectrogram using the Discrete-Time Fourier Transform (DTFT)
    frequencies, times, Sxx = spectrogram(data, fs=rate, nperseg=256, noverlap=128)

    # Compute the Fourier transform for the frequency spectrum plot
    fft_data = np.fft.fft(data)
    frequencies_fft = np.fft.fftfreq(len(fft_data), d=1/rate)
    amplitudes_fft = np.abs(fft_data)

    # Plotting the results
    fig, ax = plt.subplots(3, 2, gridspec_kw={'width_ratios': [4, 1], 'height_ratios': [1, 3, 1]}, figsize=(14, 10))

    # Time-domain signal (bottom left)
    ax[2, 0].plot(time, data)
    ax[2, 0].set_title('Time Domain Signal')
    ax[2, 0].set_xlabel('Time [s]')
    ax[2, 0].set_ylabel('Normalized Amplitude')

    # Spectrogram (middle left)
    im = ax[1, 0].pcolormesh(times, frequencies, 10 * np.log10(Sxx), shading='gouraud', cmap='jet')
    ax[1, 0].set_title('Spectrogram (DTFT)')
    ax[1, 0].set_xlabel('Time [s]')
    ax[1, 0].set_ylabel('Frequency [Hz]')
    fig.colorbar(im, ax=ax[1, 0], label='Power/Frequency (dB/Hz)')

    # Fourier Amplitude Spectrum (right)
    ax[1, 1].plot(amplitudes_fft[:len(amplitudes_fft)//2], frequencies_fft[:len(frequencies_fft)//2])
    ax[1, 1].set_title('Fourier Amplitude Spectrum')
    ax[1, 1].set_ylabel('Frequency [Hz]')
    ax[1, 1].set_yscale('log')
    ax[1, 1].set_xlabel('Amplitude')

    # Empty plot (bottom right)
    ax[2, 1].axis('off')

    # Hide top-left subplot
    ax[0, 0].axis('off')

    plt.tight_layout()
    plt.show()

    return fig