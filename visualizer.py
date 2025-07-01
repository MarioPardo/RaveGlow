import tkinter as tk
from tkinter import filedialog
from audio_playback import AudioPlayerStream 
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
        self.seconds_on_screen = 10
        self.canvas_width = 580

        self.audio_player = AudioPlayerStream()
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
        
        num_bins_per_freqtype = 10
        max_height_bars = 15

        bin_width = 50
        bin_height = 20

        # Create a canvas for the grid
        grid_canvas_width = num_bins_per_freqtype * bin_width
        grid_canvas_height = max_height_bars * bin_height
        self.grid_canvas = tk.Canvas(self.root, width=grid_canvas_width, height=grid_canvas_height, bg="gray")
        self.grid_canvas.pack(pady=10)

        # Draw the grid lines
        for i in range(num_bins_per_freqtype + 1):  # Vertical lines
            x = i * bin_width
            self.grid_canvas.create_line(x, 0, x, grid_canvas_height, fill="white")

        for j in range(max_height_bars + 1):  # Horizontal lines
            y = j * bin_height
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

    def update_visualizer(self):
        """Periodic update function called by Tkinter's main loop."""
        if not self.visualizer_running:
            return
        
        self.main_visualizer_canvas.delete("all")  # Clear previous frame

        # Get audio samples
        raw_window_data = self.audio_player.get_latest_window(self.audio_player.raw_samples,self.audio_player.sample_rate)
        chunked_data = self.audio_player.audio_analyzer.split_into_ms_chunks(raw_window_data, self.audio_player.sample_rate, self.audio_player.barlength_ms)

        lows = []
        mids = []
        highs = []
        for chunk in chunked_data:
            fft_data = self.audio_player.audio_analyzer.get_fft_band_energies(chunk, self.audio_player.sample_rate)
            lows.append(fft_data[0])
            mids.append(fft_data[1])
            highs.append(fft_data[2])


        window_data = self.audio_player.audio_analyzer.downsample_data(raw_window_data, self.audio_player.sample_rate, self.audio_player.barlength_ms)
    

        if window_data is None or len(window_data) == 0:
            self.root.after(23, self.update_visualizer)  # ~30 FPS
            return
        
        self.DrawBars(self.main_visualizer_canvas, window_data)
        self.DrawCanvasDetails(self.main_visualizer_canvas)

        # Draw highs, mids, and lows
        self.DrawBars(self.highs_visualizer_canvas, highs)  # Highs
        self.DrawCanvasDetails(self.highs_visualizer_canvas)

        self.DrawBars(self.mids_visualizer_canvas, mids)  # Mids
        self.DrawCanvasDetails(self.mids_visualizer_canvas)

        self.DrawBars(self.lows_visualizer_canvas, lows)  # Lows
        self.DrawCanvasDetails(self.lows_visualizer_canvas)


        self.root.after(40, self.update_visualizer)  # ~30 FPS

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

    def DrawBars(cself,canvas, window_data):
        canvas.delete("all")  # Clear previous frame

        # Get canvas dimensions
        width = int(canvas['width'])
        height = int(canvas['height'])
        padding = 10

        graph_width = width - 2 * padding
        graph_height = height - 2 * padding
        num_bars = len(window_data)
        bar_width = graph_width / num_bars if num_bars > 0 else 1

        # Scale data to fit canvas height
        max_val = max(abs(min(window_data)), max(window_data)) or 1
        center_y = height // 2

        for i, value in enumerate(window_data):
            scaled_height = int((value / max_val) * (graph_height / 2))
            x = padding + i * bar_width
            canvas.create_line(
                x, center_y,
                x, center_y - scaled_height,
                fill="cyan"
            )


    def DrawSpectrum(self, canvas, magnitudes):
        canvas.delete("all") 
        width = int(canvas['width'])
        height = int(canvas['height'])

        # Normalize magnitudes
        max_magnitude = np.max(magnitudes) or 1
        magnitudes = magnitudes / (max_magnitude * 1.5)

        # Map magnitudes to canvas width
        num_bins = len(magnitudes)
        step = num_bins / width  # Fractional step to map all bins to canvas width

        for x in range(width):
            # Calculate the corresponding index in the magnitudes array
            idx = int(x * step)
            if idx >= num_bins:
                break

            bar_height = int(magnitudes[idx] * height)
            canvas.create_line(x, height, x, height - bar_height, fill="cyan")

# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = AudioVisualizerApp(root)
    root.mainloop()
