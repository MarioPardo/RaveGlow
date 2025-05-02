import tkinter as tk
from tkinter import filedialog
from audio_playback import AudioPlayer  # Import the AudioPlayer class

class AudioVisualizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Rave Glow")
        self.root.geometry("600x400")

        # Create an instance of AudioPlayer
        self.audio_player = AudioPlayer()

        # UI Elements
        self.create_widgets()

    def create_widgets(self):
        # --- Buttons ---
        self.select_button = tk.Button(self.root, text="Select Audio File", command=self.select_file)
        self.select_button.pack(pady=10)

        self.play_button = tk.Button(self.root, text="Play", command=self.toggle_play_pause, state=tk.DISABLED)
        self.play_button.pack(pady=10)

        self.stop_button = tk.Button(self.root, text="Stop", command=self.stop_audio, state=tk.DISABLED)
        self.stop_button.pack(pady=10)

        # --- Waveform Canvas (blank for now) ---
        self.canvas = tk.Canvas(self.root, width=580, height=200, bg="black")
        self.canvas.pack(pady=20)

    def select_file(self):
        """Open file dialog to select an MP3 file."""
        file_path = filedialog.askopenfilename(
            filetypes=[("MP3 Files", "*.mp3"), ("All Files", "*.*")]
        )

        if file_path:
            self.audio_player.load_audio(file_path)  # Load the audio file
            self.play_button.config(state=tk.NORMAL)
            self.play_button.config(text="Play")
            self.is_playing = False

    def toggle_play_pause(self):
        """Toggle play/pause for the audio."""
        self.audio_player.toggle_play_pause()
        
        # Update the button text based on current playback state
        if self.audio_player.is_playing:
            self.play_button.config(text="Pause")
            self.stop_button.config(state=tk.NORMAL)
        else:
            self.play_button.config(text="Play")

    def stop_audio(self):
        """Stop the audio and reset the position."""
        self.audio_player.stop()
        self.play_button.config(text="Play")  # Reset play button text
        self.stop_button.config(state=tk.DISABLED)  # Disable Stop button when stopped

# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = AudioVisualizerApp(root)
    root.mainloop()
