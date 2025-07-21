
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
    
    


    def get_fft_band_energies(self, samples, sample_rate, low_pass_cutoff):
        """
        Perform FFT on the input samples and return average magnitudes for
        the specified frequency bands, with an optional low-pass filter cutoff.

        Args:
            samples (np.ndarray): 1D array of audio samples.
            sample_rate (int): Sample rate of the audio in Hz.
            low_pass_cutoff (float, optional): Frequency in Hz to apply a low-pass filter. 
                               Frequencies above this value will be ignored.

        Returns:
            list: Average magnitudes for each frequency band.
        """
        bands = self.logarithmic_bands

        # Perform FFT
        samples = samples * np.hanning(len(samples))  # Apply a Hanning window
        fft_result = np.fft.fft(samples)
        magnitudes = np.abs(fft_result)
        magnitudes = np.log1p(magnitudes)
        freqs = np.fft.fftfreq(len(samples), d=1/sample_rate)

        # Use only the positive frequencies
        half_n = len(samples) // 2
        freqs = freqs[:half_n]
        magnitudes = magnitudes[:half_n]

        # Apply low-pass filter if specified
        if low_pass_cutoff is not None:
            low_pass_mask = freqs <= low_pass_cutoff
            freqs = freqs[low_pass_mask]
            magnitudes = magnitudes[low_pass_mask]

        # Compute average magnitudes for each band
        band_energies = []
        for low_freq, high_freq in bands:
            band_mask = (freqs >= low_freq) & (freqs < high_freq)
            avg_magnitude = np.mean(magnitudes[band_mask]) if np.any(band_mask) else 0
            band_energies.append(avg_magnitude)

        return band_energies


    def EMA(self, newvals, emabuffer, alpha):

        for i in range(0, len(emabuffer)):
            emabuffer[i] = alpha * newvals[i] + (1 - alpha) * emabuffer[i - 1]
        return emabuffer

    def find_energy(self,audiosamples_inbins):
        return np.sum(np.square(audiosamples_inbins), axis=0)  
    

    def smooth_energy_buffer(self, buffer, alpha=0.5):
        buffer_type = type(buffer)  # Preserve the original type
        buffer = np.array(buffer, dtype=np.float32)  # Ensure it supports slicing
        smoothed = [buffer[0]]
        
        for val in buffer[1:]:
            smoothed.append(alpha * val + (1 - alpha) * smoothed[-1])
        
        smoothed = np.array(smoothed)
        return buffer_type(smoothed) if buffer_type is not np.ndarray else smoothed



    def estimate_bpm(self, energy_buffer, frame_duration=0.02, min_bpm=120, max_bpm=190):
        """
        Estimate BPM from energy buffer using autocorrelation.

        Parameters:
            energy_buffer (List[float]): A list of energy values, one per frame.
            frame_duration (float): Duration of each frame in seconds (e.g., 0.02 for 20ms).
            min_bpm (int): Minimum BPM to search for.
            max_bpm (int): Maximum BPM to search for.

        Returns:
            float: Estimated BPM.
        """
        if len(energy_buffer) < 2:
            return None  # Not enough data

        # Perform autocorrelation
        autocorr = np.correlate(energy_buffer, energy_buffer, mode='full')
        autocorr = autocorr[len(autocorr)//2:]  # Keep only positive lags
        autocorr /= np.max(autocorr)

        # Convert BPM range to lag range
        min_lag = int(60 / max_bpm / frame_duration)
        max_lag = int(60 / min_bpm / frame_duration)

        if max_lag >= len(autocorr):
            max_lag = len(autocorr) - 1

        # Only consider valid BPM lags
        search_region = autocorr[min_lag:max_lag]
        if len(search_region) == 0:
            return None

        # Print table of lag, BPM, score
        print(f"{'Lag':>5} | {'BPM':>6} | {'Score':>7}")
        print("-" * 25)
        for i, score in enumerate(search_region):
            lag = i + min_lag
            bpm = 60.0 / (lag * frame_duration)
            print(f"{lag:>5} | {bpm:6.2f} | {score:7.4f}")

        best_lag = np.argmax(search_region) + min_lag
        estimated_bpm = 60.0 / (best_lag * frame_duration)

        print("\nBest Lag:", best_lag)
        print("Estimated BPM:", f"{estimated_bpm:.2f}")

        return estimated_bpm


