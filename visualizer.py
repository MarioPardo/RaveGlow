import tkinter as tk
from tkinter import filedialog
import pygame
import os

class AudioVisualizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Rave Player")
        self.root.geometry("600x400")

        # Initialize Pygame mixer for audio playback
        pygame.mixer.init()

        # Track if we're playing or paused
        self.is_playing = False
        self.current_file = None

        # UI Elements
        self.create_widgets()

    def create_widgets(self):
        # --- Buttons ---
        self.select_button = tk.Button(self.root, text="Select Audio File", command=self.select_file)
        self.select_button.pack(pady=10)

        self.play_button = tk.Button(self.root, text="Play", command=self.toggle_play_pause, state=tk.DISABLED)
        self.play_button.pack(pady=10)

        # --- Waveform Canvas (blank for now) ---
        self.canvas = tk.Canvas(self.root, width=580, height=200, bg="black")
        self.canvas.pack(pady=20)

    def select_file(self):
        # Open file dialog and filter for audio files
        file_path = filedialog.askopenfilename(
            filetypes=[("MP3 Files", "*.mp3"), ("All Files", "*.*")]
        )

        if file_path:
            self.current_file = file_path
            self.load_audio(file_path)
            self.play_button.config(state=tk.NORMAL)
            self.play_button.config(text="Play")
            self.is_playing = False

    def load_audio(self, file_path):
        # Stop anything currently playing
        pygame.mixer.music.stop()
        
        # Load the new file
        pygame.mixer.music.load(file_path)

    def toggle_play_pause(self):
        if not self.current_file:
            return

        if not self.is_playing:
            pygame.mixer.music.play()
            self.is_playing = True
            self.play_button.config(text="Pause")
        else:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.play_button.config(text="Play")

# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = AudioVisualizerApp(root)
    root.mainloop()
