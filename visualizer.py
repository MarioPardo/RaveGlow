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

        self.audio_player = AudioPlayerStream()
        self.audio_analyzer = AudioAnalyzer()
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
        self.main_visualizer_canvas = tk.Canvas(self.root, width=580, height=200, bg="black")
        self.main_visualizer_canvas.pack(pady=20)
    
        # --- Additional Visualizer Canvases ---
        self.highs_label = tk.Label(self.root, text="Highs", bg="black", fg="white")
        self.highs_label.pack(pady=(30, 0))
        self.highs_visualizer_canvas = tk.Canvas(self.root, width=580, height=100, bg="black")
        self.highs_visualizer_canvas.pack(pady=(0, 20))

        self.mids_label = tk.Label(self.root, text="Mids", bg="black", fg="white")
        self.mids_label.pack(pady=(0, 0))
        self.mids_visualizer_canvas = tk.Canvas(self.root, width=580, height=100, bg="black")
        self.mids_visualizer_canvas.pack(pady=(0, 20))

        self.lows_label = tk.Label(self.root, text="Lows", bg="black", fg="white")
        self.lows_label.pack(pady=(0, 0))
        self.lows_visualizer_canvas = tk.Canvas(self.root, width=580, height=100, bg="black")
        self.lows_visualizer_canvas.pack(pady=(0, 20))


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
        self.audio_player.update_audio_window()
        samples = self.audio_player.get_latest_window()[1]

        if samples is None or len(samples) == 0:
            self.root.after(23, self.update_visualizer)  # ~30 FPS
            return
        # Compute FFT and get frequency data
        self.audio_analyzer.compute_fft(samples, self.audio_player.audio_segment.frame_rate)

        self.DrawWaveform(self.main_visualizer_canvas, samples)
        self.DrawSpectrum(self.highs_visualizer_canvas, self.audio_analyzer.highs_data[0], self.audio_analyzer.highs_data[1])
        self.DrawSpectrum(self.mids_visualizer_canvas, self.audio_analyzer.mids_data[0], self.audio_analyzer.mids_data[1])
        self.DrawSpectrum(self.lows_visualizer_canvas, self.audio_analyzer.lows_data[0], self.audio_analyzer.lows_data[1])

        self.root.after(23, self.update_visualizer)  # ~30 FPS


    def DrawWaveform(self, canvas, samples):
        canvas.delete("all")  # Clear previous frame
        # Normalize samples to fit the canvas height
        width = int(canvas['width'])
        height = int(canvas['height'])
        mid_y = height // 2

        # Downsample to match canvas width
        step = max(1, len(samples) // width)
        samples = samples[::step]

        # Normalize to [-1, 1]
        max_amplitude = np.max(np.abs(samples)) or 1
        normalized = samples / max_amplitude

        # Draw waveform as connected lines
        for i in range(1, len(normalized)):
            x1 = i - 1
            y1 = mid_y - int(normalized[i - 1] * (height // 2))
            x2 = i
            y2 = mid_y - int(normalized[i] * (height // 2))
            self.main_visualizer_canvas.create_line(x1, y1, x2, y2, fill='cyan')
    


    def DrawSpectrum(self, canvas, freqs, magnitudes):
        canvas.delete("all") 
        width = int(canvas['width'])
        height = int(canvas['height'])

        # Normalize magnitudes
        max_magnitude = np.max(magnitudes) or 1
        magnitudes = magnitudes / max_magnitude

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
