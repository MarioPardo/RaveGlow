
import numpy as np

class AudioAnalyzer:

     # Bands for FFT
    lows_bands = (0, 180)
    mids_bands = (200, 2000)
    highs_bands = (4000, 20000)

    def __init__(self):
        pass
   
    
    def downsample_data(self,data, samplerate, barlength_ms):
        """Downsample the waveform data for visualization."""
        samples_per_bar = int(samplerate * (barlength_ms / 1000.0))
        num_bars = len(data) // samples_per_bar

        downsampled_data = []
        for i in range(num_bars):
            start = i * samples_per_bar
            end = start + samples_per_bar
            bar = data[start:end]

            #how we determine bar, mean for now
            downsampled_sample = np.median(bar)
            downsampled_data.append(downsampled_sample)

        return downsampled_data
    
    def split_into_ms_chunks(self,data, samplerate, chunk_length_ms):
        """Split the waveform data into chunks of specified length in milliseconds."""
        samples_per_chunk = int(samplerate * (chunk_length_ms / 1000.0))
        num_chunks = len(data) // samples_per_chunk

        chunks = []
        for i in range(num_chunks):
            start = i * samples_per_chunk
            end = start + samples_per_chunk
            chunk = data[start:end]
            chunks.append(chunk)

        return chunks
    
    





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
    

    import numpy as np

    def get_fft_band_energies(self, samples, sample_rate):
        """
        Perform FFT on the input samples and return average magnitudes for
        low, mid, and high frequency bands.

        Args:
            samples (np.ndarray): 1D array of audio samples.
            sample_rate (int): Sample rate of the audio in Hz.

        Returns:
            tuple: (avg_low, avg_mid, avg_high) magnitudes
        """

        # Perform FFT
        fft_result = np.fft.fft(samples)
        magnitudes = np.abs(fft_result)
        freqs = np.fft.fftfreq(len(samples), d=1/sample_rate)

        # Use only the positive frequencies
        half_n = len(samples) // 2
        freqs = freqs[:half_n]
        magnitudes = magnitudes[:half_n]

        # Define band ranges
        lows_bands = (0, 180)
        mids_bands = (200, 2000)
        highs_bands = (4000, 20000)

        # Mask for each band
        low_mask = (freqs >= lows_bands[0]) & (freqs < lows_bands[1])
        mid_mask = (freqs >= mids_bands[0]) & (freqs < mids_bands[1])
        high_mask = (freqs >= highs_bands[0]) & (freqs < highs_bands[1])

        # Compute average magnitudes
        avg_low = np.mean(magnitudes[low_mask]) if np.any(low_mask) else 0
        avg_mid = np.mean(magnitudes[mid_mask]) if np.any(mid_mask) else 0
        avg_high = np.mean(magnitudes[high_mask]) if np.any(high_mask) else 0

        return avg_low, avg_mid, avg_high


