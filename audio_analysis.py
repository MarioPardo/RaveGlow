
import numpy as np

class AudioAnalyzer:

     # Bands for FFT
    lows_bands = (0, 180)
    mids_bands = (200, 2000)
    highs_bands = (4000, 20000)

    def __init__(self):
        pass
   

    def FFT(self, samples, sample_rate):
        """Perform Fast Fourier Transform on the audio samples."""
        # Perform FFT
        fft_result = np.fft.fft(samples)
        # Get the magnitude
        magnitudes = np.abs(fft_result)
        # Get the frequency bins
        freqs = np.fft.fftfreq(len(samples), d=1/sample_rate)
        return freqs, magnitudes
    

    def Get_FFT_HighsMidsLows(self, freqs, magnitudes, lowsbands = lows_bands, midsbands = mids_bands, highsbands = highs_bands):
        """Get the high, mid, and low frequency bands."""
        # Get the indices for the frequency bands
        low_indices = np.where((freqs >= lowsbands[0]) & (freqs <= lowsbands[1]))[0]
        mid_indices = np.where((freqs >= midsbands[0]) & (freqs <= midsbands[1]))[0]
        high_indices = np.where((freqs >= highsbands[0]) & (freqs <= highsbands[1]))[0]

        # Calculate the average magnitude for each band
        low_magnitudes = np.mean(magnitudes[low_indices])
        mid_magnitudes= np.mean(magnitudes[mid_indices])
        high_magnitudes = np.mean(magnitudes[high_indices])

        return low_magnitudes, mid_magnitudes, high_magnitudes
    


