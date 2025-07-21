import tkinter as tk
from tkinter import filedialog
from audio_playback import AudioPlayerStream 
from audio_analysis import AudioAnalyzer
import numpy as np

from enum import Enum
from collections import deque

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
        self.num_freq_bands = 8
        self.max_height_bars = 15

        # Visualizer Processing Params
        self.vis_EMA_buffer =[0 for _ in range(self.num_freq_bands)]
        self.EMA_alpha = 0.75

        self.low_pass_cutoff = 15000

        self.audio_player = AudioPlayerStream()
        self.audio_analyzer = AudioAnalyzer(numbands = self.num_freq_bands)

        #BPM Analysis
        self.bpm = 0
        self.seconds_to_store = 15
        self.numframes_store = int(self.seconds_to_store * (1000 / self.audio_player.audiowindow_duration_ms))
        self.energy_frame_counter = 0
        self.ema_energy_buffer = deque(maxlen=self.numframes_store)

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
        self.grid_canvas = tk.Canvas(self.root, width=grid_canvas_width, height=grid_canvas_height, bg="black")
        self.grid_canvas.pack(pady=10)

        self.DrawVisualizer(None)

        #BPM Counter
        # --- BPM Counter ---

        bpm_frame = tk.Frame(self.root)
        bpm_frame.pack(pady=5)

        self.bpm_label = tk.Label(bpm_frame, text="BPM:")
        self.bpm_label.pack(side=tk.LEFT, padx=5)

        self.bpm_value_label = tk.Label(bpm_frame, text="0")  # Default BPM value
        self.bpm_value_label.pack(side=tk.LEFT, padx=5)

        self.bpm_color_box = tk.Canvas(bpm_frame, width=20, height=20, bg="grey", highlightthickness=1, highlightbackground="black")
        self.bpm_color_box.pack(side=tk.LEFT, padx=5)

        # --- Manual Settings for Visualizer ---

        # --- EMA Alpha Slider ---
        self.alpha_label = tk.Label(self.root, text="EMA Alpha:")
        self.alpha_label.pack(pady=5)
        self.alpha_slider = tk.Scale(self.root, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL, command=lambda value: setattr(self, 'EMA_alpha', float(value)))
        self.alpha_slider.set(self.EMA_alpha)  # Default value
        self.alpha_slider.pack(pady=5)

            # --- Low-Pass Filter Slider ---
        self.low_pass_label = tk.Label(self.root, text="Low-Pass Filter Cutoff (Hz):")
        self.low_pass_label.pack(pady=5)
        self.low_pass_slider = tk.Scale(self.root, from_=20, to=20000, resolution=10, orient=tk.HORIZONTAL, command=lambda value: setattr(self, 'low_pass_cutoff', float(value)))
        self.low_pass_slider.set(self.low_pass_cutoff)  # Default cutoff frequency
        self.low_pass_slider.pack(pady=5)

    def update_ema_alpha(self, value):
        self.ema_alpha = float(value)
    
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
                for j in range(band_height):
                    color = self.findRectableColor((band_height-j), self.max_height_bars)
                    self.grid_canvas.create_rectangle(x, y + j * self.bin_height, x + self.bin_width, y + (j + 1) * self.bin_height, fill=color)
        

        # Draw the grid lines
        for i in range(self.num_freq_bands + 1):  # Vertical lines
            x = i * self.bin_width
            self.grid_canvas.create_line(x, 0, x, grid_canvas_height, fill="white")

        for j in range(self.max_height_bars + 1):  # Horizontal lines
            y = j * self.bin_height
            self.grid_canvas.create_line(0, y, grid_canvas_width, y, fill="white")


    def findRectableColor(self, value, max_value):
        if value >= 0.8 * max_value:
            return "red"
        elif value >= 0.6 * max_value:
            return "orange"
        elif value >= 0.4 * max_value:
            return "yellow"
        else:
            return "green"


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

    def scale_bar_heights(self, mag):
        
        return [min(int(m), self.max_height_bars) for m in mag]

    
    def scale_with_exponent(self,magnitudes, exp=2.0):
        normalization_const = 16 #TODO store in better place, bound to change
        normalized = magnitudes / np.abs(normalization_const)
        scaled = np.power(normalized, exp)
        scaled = np.array(scaled)
        return np.clip((scaled * self.max_height_bars).astype(int), 0, self.max_height_bars)    


    def update_visualizer(self):
        """Periodic update function called by Tkinter's main loop."""
        if not self.visualizer_running:
            return
    

        # Get audio samples
        raw_window_data = self.audio_player.get_latest_samples_window(self.audio_player.audio_segment,self.audio_player.sample_rate)
        if raw_window_data is None or len(raw_window_data) == 0:
            self.root.after(20, self.update_visualizer) 
            return
        
        
        # Analyze the audio data
        freq_bands = self.audio_analyzer.get_fft_band_energies(raw_window_data, self.audio_player.sample_rate, self.low_pass_cutoff)
        self.vis_EMA_buffer = self.audio_analyzer.EMA(freq_bands, self.vis_EMA_buffer, self.EMA_alpha)
        normalized_bands = self.scale_with_exponent(self.vis_EMA_buffer)
    
        #BPM
        buffer_energy = (self.audio_analyzer.find_energy(self.vis_EMA_buffer))
        self.ema_energy_buffer.append(buffer_energy)


        #self.ema_energy_buffer = self.audio_analyzer.smooth_energy_buffer(self.ema_energy_buffer)
        self.energy_frame_counter += 1

        # Update every time we refill buffer
        if self.energy_frame_counter >= self.numframes_store:
            self.bpm = self.audio_analyzer.estimate_bpm(self.ema_energy_buffer)
            if(self.bpm is not None):
                self.bpm_value_label.config(text=str(int(self.bpm)))

            self.energy_frame_counter = 0

        self.DrawVisualizer(normalized_bands)

        self.root.after(20, self.update_visualizer)

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
