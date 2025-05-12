import pygame
from pydub import AudioSegment
import numpy as np
from typing import Tuple
from collections import deque




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
        self.barlength_ms = 50

        self.stream = None

        #Storing audio info
        self.samples = []
        self.downsampled_samples = []
    

    # --- Playback Methods ---
    def load_audio(self, file_path):
        """Load an audio file for playback and waveform access."""
        self.current_file = file_path
        pygame.mixer.music.load(file_path)
        self.audio_segment = AudioSegment.from_file(file_path)

        self.extract_waveform_data()
        self.def_addblank_startpadding(5)
        self.downsample_data(self.barlength_ms)


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

    def extract_waveform_data(self):
        """Extract waveform data from the loaded audio file."""
        if self.audio_segment is None:
            raise ValueError("No audio file loaded.")
        self.samples = np.array(self.audio_segment.get_array_of_samples())
        if self.audio_segment.channels == 2:
            self.samples = self.samples.reshape((-1, 2)).mean(axis=1)     

    def downsample_data(self,barlength_ms=50):
        """Downsample the waveform data for visualization."""
        self.barlength_ms = barlength_ms
        samples_per_bar = int(self.sample_rate * (barlength_ms / 1000.0))
        num_bars = len(self.samples) // samples_per_bar

        for i in range(num_bars):
            start = i * samples_per_bar
            end = start + samples_per_bar
            bar = self.samples[start:end]

            #how we determine bar, mean for now
            downsampled_sample = np.mean(bar)
            self.downsampled_samples.append(downsampled_sample)

    
    def get_downsampled_audio_window(self, start_ms, end_ms):
        """Get a window of downsampled audio data between start and end times."""
        
        start_index = int(start_ms // self.barlength_ms)
        end_ms_index = int(end_ms // self.barlength_ms)

        return self.downsampled_samples[start_index:end_ms_index]


    def get_latest_window(self, windowduration_s=10):
        """Get the latest window of audio data."""
        if self.current_file is None:
            return None

        # Update the current position
        self.current_position = pygame.mixer.music.get_pos() / 1000.0
        start_time = self.current_position * 1000.0
        end_time = start_time + windowduration_s * 1000.0

        # Get the downsampled audio window
        downsampled_window = self.get_downsampled_audio_window(start_time, end_time)

        # Update the current position
        self.current_position = pygame.mixer.music.get_pos() / 1000.0

        return downsampled_window

    def def_addblank_startpadding(self,seconds):
        """Add blank padding to the start of the audio data."""
        num_samples = int(seconds * self.sample_rate)
        blank_padding = np.zeros(num_samples)
        self.samples = np.concatenate((blank_padding, self.samples))
    


    # --- Stream Methods (for future use with live audio) ---
    # def start_stream(self):
    #     """Start audio capture stream (for live audio processing)."""
    #     import pyaudio
    #     self.stream = pyaudio.PyAudio().open(
    #         format=pyaudio.paInt16,
    #         channels=1,
    #         rate=self.sample_rate,
    #         input=True,
    #         frames_per_buffer=self.chunk_size
    #     )
    #     self.is_playing = True

    # def stop_stream(self):
    #     """Stop and close the audio stream."""
    #     if self.stream:
    #         self.stream.stop_stream()
    #         self.stream.close()
    #         self.is_playing = False

    # def get_audio_data(self):
    #     """Capture a chunk of audio data from the stream."""
    #     if self.is_playing:
    #         data = self.stream.read(self.chunk_size)
    #         return np.frombuffer(data, dtype=np.int16)
    #     return None
