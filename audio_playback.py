import pygame
from pydub import AudioSegment
import numpy as np
from typing import Tuple
from collections import deque

from audio_analysis import AudioAnalyzer


# Initialize Pygame mixer once
pygame.mixer.init()

class AudioPlayerStream:
    def __init__(self, sample_rate=44100, chunk_size=1024):
        # Playback state
        self.current_file = None
        self.current_position = 0
        self.audio_segment = None

        # Audio Settings
        self.sample_rate = 44100
        self.samples_per_ms = self.sample_rate / 1000.0
        self.chunk_size = 1024
        self.barlength_ms = 15

        self.stream = None

        #Storing audio info
        self.raw_samples = []
        self.downsampled_raw_samples = []

        #Storing analyzed audio
        self.freqs, self.audio_segment = None, None
        self.raw_lows_samples = []
        self.raw_mids_samples = []
        self.raw_highs_samples = []

        self.audio_analyzer = AudioAnalyzer()
    

    # --- Playback Methods ---
    def load_audio(self, file_path):
        """Load an audio file for playback and waveform access."""
        self.current_file = file_path
        pygame.mixer.music.load(file_path)
        self.audio_segment = AudioSegment.from_file(file_path)

        self.PerformAnalysis()

    def PerformAnalysis(self):
        """Perform analysis on the loaded audio file."""
        self.raw_samples = self.extract_waveform_data(self.audio_segment)
        self.raw_samples = self.def_addblank_startpadding(self.raw_samples, self.sample_rate, 5)  # Add 1 second of padding at the start
        
        # Get FFT data
        freqs, magnitudes = self.audio_analyzer.FFT(self.raw_samples, self.sample_rate)
        self.raw_lows_samples, self.raw_mids_samples, self.raw_highs_samples = self.audio_analyzer.Get_FFT_HighsMidsLows(freqs, magnitudes)

        #Downsampling for visualization
        self.downsampled_raw_samples = self.audio_analyzer.downsample_data(self.raw_samples, self.sample_rate, self.barlength_ms)


    def start_playing(self):
        """Start playback from the current position."""
        if self.current_file:
            pygame.mixer.music.play()

    def resume(self):
        """Resume playback from the last saved position."""
        pygame.mixer.music.unpause() 

    def pause(self):
        """Pause playback and save current position."""
        self.current_position = pygame.mixer.music.get_pos() / 1000.0
        pygame.mixer.music.pause()

    def stop(self):
        """Stop playback and reset position."""
        pygame.mixer.music.stop()
        self.current_position = 0

    def extract_waveform_data(self,audio_segment):
        """Extract waveform data from the loaded audio file."""
        if audio_segment is None:
            raise ValueError("No audio file loaded.")
        
        samples = np.array(audio_segment.get_array_of_samples())
        if audio_segment.channels == 2:
            samples = samples.reshape((-1, 2)).mean(axis=1)     
        
        return samples
    

        
    def get_downsampled_audio_window(self,datasource, barlength_ms, start_ms, end_ms):
        """Get a window of downsampled audio data between start and end times."""
        
        start_index = int(start_ms // barlength_ms)
        end_ms_index = int(end_ms // barlength_ms)

        return datasource[start_index:end_ms_index]


    def get_latest_downsampled_window(self, datasource, windowduration_s=10):
        """Get the latest window of audio data."""
        if self.current_file is None:
            return None

        # Update the current position
        self.current_position = pygame.mixer.music.get_pos() / 1000.0
        start_time = self.current_position * 1000.0
        end_time = start_time + windowduration_s * 1000.0

        # Get the downsampled audio window
        downsampled_window = self.get_downsampled_audio_window(datasource, self.barlength_ms, start_time, end_time)

        # Update the current position
        self.current_position = pygame.mixer.music.get_pos() / 1000.0

        return downsampled_window

    def get_latest_window2(self, samples, sample_rate):
        """Get the latest window of raw audio samples (in sync with music playback)."""
        if self.current_file is None:
            return None

        windowduration_s = 10  # how many seconds of audio to grab

        # Get current position from pygame in seconds
        self.current_position = pygame.mixer.music.get_pos() / 1000.0
        
        # Compute sample indices
        start_sample = int(self.current_position * sample_rate)
        end_sample = int((self.current_position + windowduration_s) * sample_rate)

        # Clip to available range
        if end_sample > len(samples):
            end_sample = len(samples)
        if start_sample >= end_sample:
            return np.zeros(windowduration_s * sample_rate)  # silence fallback

        # Slice the sample array
        window = samples[start_sample:end_sample]

        return window


    def def_addblank_startpadding(self,data, samplerate, seconds):
        """Add blank padding to the start of the audio data."""
        num_samples = int(seconds * samplerate)
        blank_padding = np.zeros(num_samples)
        data = np.concatenate((blank_padding, data))
        return data
    

