import tkinter as tk
from tkinter import filedialog
from audio_playback import AudioPlayerStream 
from audio_analysis import AudioAnalyzer
import numpy as np

from enum import Enum

class PlaybackState(Enum):
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2

class AudioVisualizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Rave Glow")
        self.root.geometry("600x400")
        self.PlaybackState = PlaybackState.STOPPED
        self.visualizer_running = False

        #Settings
        self.canvas_width = 580
        self.bin_width = 50
        self.bin_height = 20
    

        #Configuratble Params 
        self.num_freq_bands = 10
        self.max_height_bars = 15

        self.audio_player = AudioPlayerStream()
        self.audio_analyzer = AudioAnalyzer(numbands = self.num_freq_bands)
        self.create_widgets()

        


    def create_widgets(self):
        # --- Buttons ---
        self.select_button = tk.Button(self.root, text="Select Audio File", command=self.select_file)
        self.select_button.pack(pady=10)

        self.play_button = tk.Button(self.root, text="Play", command=self.toggle_play_pause, state=tk.DISABLED)
        self.play_button.pack(pady=10)

        self.stop_button = tk.Button(self.root, text="Stop", command=self.stop_audio, state=tk.DISABLED)
        self.stop_button.pack(pady=10)

        # Create a canvas for the grid
        grid_canvas_width = self.num_freq_bands * self.bin_width
        grid_canvas_height = self.max_height_bars * self.bin_height
        self.grid_canvas = tk.Canvas(self.root, width=grid_canvas_width, height=grid_canvas_height, bg="gray")
        self.grid_canvas.pack(pady=10)

        self.DrawVisualizer(None)

    
    def DrawVisualizer(self,bands=None):
        """Draw the visualizer grid on a canvas."""

        self.grid_canvas.delete("all")  # Clear previous grid

        grid_canvas_width = self.num_freq_bands * self.bin_width
        grid_canvas_height = self.max_height_bars * self.bin_height        

        if bands is not None:
            for i, band_height in enumerate(bands):
                x = i * self.bin_width
                y = grid_canvas_height - (band_height * self.bin_height)
                bar_height = band_height * self.bin_height
                self.grid_canvas.create_rectangle(x, y, x + self.bin_width, grid_canvas_height, fill="green")
        

        # Draw the grid lines
        for i in range(self.num_freq_bands + 1):  # Vertical lines
            x = i * self.bin_width
            self.grid_canvas.create_line(x, 0, x, grid_canvas_height, fill="white")

        for j in range(self.max_height_bars + 1):  # Horizontal lines
            y = j * self.bin_height
            self.grid_canvas.create_line(0, y, grid_canvas_width, y, fill="white")





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
        
        # Update the button text based on current playback state
        if self.PlaybackState == PlaybackState.STOPPED: #start playing
            self.play_button.config(text="Pause")
            self.stop_button.config(state=tk.NORMAL)
            self.audio_player.start_playing()
            self.PlaybackState = PlaybackState.PLAYING
            self.start_visualizer_loop()

        elif self.PlaybackState == PlaybackState.PAUSED:
            self.play_button.config(text="Play")
            self.start_visualizer_loop()
            self.audio_player.resume()
            self.PlaybackState = PlaybackState.PLAYING

        elif self.PlaybackState == PlaybackState.PLAYING:
            self.play_button.config(text="Pause")
            self.main_visualizer_canvas.delete("all")
            self.visualizer_running = False
            self.audio_player.pause()
            self.PlaybackState = PlaybackState.PAUSED

        

    def stop_audio(self):
        """Stop the audio and reset the position."""
        self.audio_player.stop()
        self.play_button.config(text="Play")  # Reset play button text
        self.stop_button.config(state=tk.DISABLED)  # Disable Stop button when stopped
        self.visualizer_running = False
        self.PlaybackState = PlaybackState.STOPPED

    def start_visualizer_loop(self):
        """Start the update loop for the visualizer."""
        self.visualizer_running = True
        self.update_visualizer()

    def scale_to_bar_height_log(self,mag, max_mag=1e6, max_height=15):
        db = 20 * np.log10(mag + 1e-5)  # avoid log(0)
        db_max = 30 * np.log10(max_mag)
        return max(0, min(max_height, int((db / db_max) * max_height)))

    def update_visualizer(self):
        """Periodic update function called by Tkinter's main loop."""
        if not self.visualizer_running:
            return
    

        # Get audio samples
        raw_window_data = self.audio_player.get_latest_samples_window(self.audio_player.audio_segment,self.audio_player.sample_rate)
        if raw_window_data is None or len(raw_window_data) == 0:
            self.root.after(23, self.update_visualizer)  # ~30 FPS
            return
        
        # Analyze the audio data
        freq_bands = self.audio_analyzer.get_fft_band_energies(raw_window_data, self.audio_player.sample_rate)
        MAX_EXPECTED_MAX = 100000
        # Normalize the frequency bands to fit within the grid height
        normalized_bands = [self.scale_to_bar_height_log(band) for band in freq_bands]



        self.DrawVisualizer(normalized_bands)

        self.root.after(23, self.update_visualizer)  # ~30 FPS

    def DrawCanvasDetails(self,canvas):
        # Draw a white vertical line through the middle of the canvas
        width = int(canvas['width'])
        height = int(canvas['height'])
        padding = 50
        middle_x = width // 2

        canvas.create_line(
            middle_x, padding,
            middle_x, height - padding,
            fill="white",
            width=2
        )

    

# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = AudioVisualizerApp(root)
    root.mainloop()
