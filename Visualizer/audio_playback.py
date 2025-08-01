import pygame
from pydub import AudioSegment
import numpy as np
from typing import Tuple
from collections import deque
import librosa




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
        self.audiowindow_duration_ms = 20

        self.stream = None

        #Storing audio info
        self.raw_samples = []

    

    # --- Playback Methods ---
    def load_audio(self, file_path):
        """Load an audio file for playback and waveform access."""
        self.current_file = file_path
        pygame.mixer.music.load(file_path)
        self.audio_segment = AudioSegment.from_file(file_path)

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
    
    def get_playback_position(self):
        """Get the current playback position in seconds."""
        return pygame.mixer.music.get_pos() / 1000.0 if self.current_file else 0


    def get_latest_samples_window(self, audio_segment, sample_rate):
        """Get the latest window of raw audio samples (in sync with music playback)."""
        if self.current_file is None or audio_segment is None:
            return None

        windowduration_ms = self.audiowindow_duration_ms # how many milliseconds of audio to grab

        # Get current position from pygame in milliseconds
        self.current_position = pygame.mixer.music.get_pos()

        # Compute start and end times in milliseconds
        start_time_ms = self.current_position
        end_time_ms = self.current_position + windowduration_ms

        # Clip to available range
        if end_time_ms > len(audio_segment):
            end_time_ms = len(audio_segment)
        if start_time_ms >= end_time_ms:
            return np.zeros(int((windowduration_ms / 1000.0) * sample_rate))  # silence fallback

        # Extract the audio segment for the window
        window_segment = audio_segment[start_time_ms:end_time_ms]

        # Convert the audio segment to raw samples
        samples = np.array(window_segment.get_array_of_samples())
        if audio_segment.channels == 2:
            samples = samples.reshape((-1, 2)).mean(axis=1)

        return samples
    
    def get_last_x_seconds(self, seconds):
        """Get the last X seconds of audio samples."""
        if self.current_file is None or self.audio_segment is None:
            return None

        total_length_ms = len(self.audio_segment)
        start_time_ms = max(0, total_length_ms - (seconds * 1000))
        end_time_ms = total_length_ms

        # Extract the audio segment for the last X seconds
        segment = self.audio_segment[start_time_ms:end_time_ms]

        # Convert the audio segment to raw samples
        samples = np.array(segment.get_array_of_samples())
        if segment.channels == 2:
            samples = samples.reshape((-1, 2)).mean(axis=1)

        return samples 


    def def_addblank_startpadding(self,data, samplerate, seconds):
        """Add blank padding to the start of the audio data."""
        num_samples = int(seconds * samplerate)
        blank_padding = np.zeros(num_samples)
        data = np.concatenate((blank_padding, data))
        return data
    

