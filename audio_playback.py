import pygame

# Initialize Pygame mixer once
pygame.mixer.init()

class AudioPlayer:
    def __init__(self):
        self.is_playing = False
        self.current_file = None
        self.current_position = 0


    def load_audio(self, file_path):
        """Load an audio file."""
        self.current_file = file_path
        pygame.mixer.music.load(file_path)

    def play(self):
        """Play the loaded audio."""
        if self.current_file:
            pygame.mixer.music.play(loops=0, start=self.current_position)
            self.is_playing = True

    def pause(self):
        """Pause the audio."""
        self.current_position = pygame.mixer.music.get_pos() / 1000.0  # Get current position in seconds
        pygame.mixer.music.pause()
        self.is_playing = False

    def stop(self):
        """Stop the audio."""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.current_position = 0

    def toggle_play_pause(self):
        """Toggle play/pause state."""
        if self.is_playing:
            self.pause()
        else:
            self.play()
