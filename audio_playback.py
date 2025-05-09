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
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.stream = None

        #Storing audio info
        AudioWindow = Tuple[float, np.ndarray]
        self.window_duration_ms= int(self.chunk_size * 1000 / self.sample_rate)
        self.audio_windows = deque(maxlen=10)

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

    def update_audio_window(self):
        """Update the audio windows deque with the latest window, like in get_current_window.
        Add it with the timestamp."""
        num_samples = int((self.window_duration_ms / 1000) * self.audio_segment.frame_rate)

        if self.audio_segment is None:
            return
        
        current_time_ms = pygame.mixer.music.get_pos() #stopped
        if current_time_ms == -1:
            return

        start = max(current_time_ms - self.window_duration_ms, 0)
        window = self.audio_segment[start:current_time_ms]
        samples = np.array(window.get_array_of_samples())

        if window.channels == 2:
            samples = samples.reshape((-1, 2)).mean(axis=1)  # Convert to mono

        self.audio_windows.append((current_time_ms / 1000.0, samples))


    def get_latest_window(self):
        """Return the current audio windowas a NumPy array."""

        if self.audio_windows:
            return self.audio_windows[-1] 
        else:
            num_samples = int((self.window_duration_ms / 1000) * self.audio_segment.frame_rate)
            return (0.0, np.zeros(num_samples))


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
