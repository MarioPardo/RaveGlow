import numpy as np

class AudioAnalyzer:

    def __init__(self):
        self.lows_data = [None,None]
        self.mids_data = [None,None]
        self.highs_data = [None,None]
        pass

    def compute_fft(self, samples, sample_rate):
        """Compute FFT and return frequency bins and their corresponding magnitudes."""
        n = len(samples)
        fft_result = np.fft.rfft(samples)
        magnitudes = np.abs(fft_result)
        freqs = np.fft.rfftfreq(n, d=1/sample_rate)

        #
        self.get_highs(freqs, magnitudes)
        self.get_mids(freqs, magnitudes)
        self.get_lows(freqs, magnitudes)

        return freqs, magnitudes

    def get_lows(self, freqs, mags):
        """Return the magnitude of low frequencies (e.g. 20–250 Hz)."""
        mask = (freqs >= 20) & (freqs <= 250)
        self.lows_data = [freqs[mask], mags[mask]]
        return freqs[mask], mags[mask]

    def get_mids(self, freqs, mags):
        """Return the magnitude of mid frequencies (e.g. 250–2000 Hz)."""
        mask = (freqs > 250) & (freqs <= 2000)
        self.mids_data = [freqs[mask], mags[mask]]
        return freqs[mask], mags[mask]

    def get_highs(self, freqs, mags):
        """Return the magnitude of high frequencies (e.g. 2000–20000 Hz)."""
        mask = (freqs > 2000) & (freqs <= 20000)
        self.highs_data = [freqs[mask], mags[mask]]
        return freqs[mask], mags[mask]
