import pygame
from pydub import AudioSegment
import numpy as np




# Initialize Pygame mixer once
pygame.mixer.init()

class AudioPlayerStream:
    def __init__(self, sample_rate=44100, chunk_size=1024):
        # Playback state
        self.current_file = None
        self.current_position = 0
        self.audio_segment = None

        # Stream settings (for future live input support)
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.stream = None

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


    def get_current_window(self, duration_ms=33):
        """Return the current audio window (last `duration_ms` ms) as a NumPy array."""
        if self.audio_segment is None:
            return np.zeros(duration_ms)

        current_time_ms = pygame.mixer.music.get_pos()
        if current_time_ms == -1:
            return np.zeros(duration_ms)

        start = max(current_time_ms - duration_ms, 0)
        window = self.audio_segment[start:current_time_ms]
        samples = np.array(window.get_array_of_samples())

        if window.channels == 2:
            samples = samples.reshape((-1, 2)).mean(axis=1)  # Convert to mono

        return samples

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
