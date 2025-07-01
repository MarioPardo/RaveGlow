
import numpy as np

class AudioAnalyzer:

     # Bands for FFT
    lows_bands = (0, 180)
    mids_bands = (200, 2000)
    highs_bands = (4000, 20000)

    

    def __init__(self,numbands):
        self.numbands = numbands
        self.logarithmic_bands = self.calculate_logarithmic_bands(44100, numbands)

        print("Frequency Bands")
        print(self.logarithmic_bands)
        pass
   

    def calculate_logarithmic_bands(self, sample_rate, num_bands=10):
        """
        Calculate logarithmic frequency bands based on the sample rate.

        Args:
            sample_rate (int): Sample rate of the audio in Hz.
            num_bands (int): Number of logarithmic bands to create.

        Returns:
            list: List of tuples representing frequency ranges for each band.
        """
        min_freq = 20
        max_freq = sample_rate / 2
        band_width = (max_freq / min_freq) ** (1 / num_bands)
        bands = []
        prev_high_freq = min_freq
        for i in range(num_bands):
            low_freq = round(prev_high_freq)
            high_freq = round(min_freq * (band_width ** (i + 1)))
            bands.append((low_freq, high_freq))
            prev_high_freq = high_freq

        return bands


        
    
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
    
    


    def get_fft_band_energies(self, samples, sample_rate):
        """
        Perform FFT on the input samples and return average magnitudes for
        the specified frequency bands.

        Args:
            samples (np.ndarray): 1D array of audio samples.
            sample_rate (int): Sample rate of the audio in Hz.
            bands (list of tuples): List of (low_freq, high_freq) tuples defining frequency bands.

        Returns:
            list: Average magnitudes for each frequency band.
        """
        bands = self.logarithmic_bands

        # Perform FFT
        fft_result = np.fft.fft(samples)
        magnitudes = np.abs(fft_result)
        freqs = np.fft.fftfreq(len(samples), d=1/sample_rate)

        # Use only the positive frequencies
        half_n = len(samples) // 2
        freqs = freqs[:half_n]
        magnitudes = magnitudes[:half_n]

        # Compute average magnitudes for each band
        band_energies = []
        for low_freq, high_freq in bands:
            band_mask = (freqs >= low_freq) & (freqs < high_freq)
            avg_magnitude = np.mean(magnitudes[band_mask]) if np.any(band_mask) else 0
            band_energies.append(avg_magnitude)

        return band_energies


