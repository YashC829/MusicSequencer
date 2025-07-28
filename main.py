#first file
import tkinter as tk
import numpy as np
import sounddevice as sd

# Constants
DURATION = 0.3  # seconds
SAMPLE_RATE = 44100
CANVAS_WIDTH = 800

# Frequency range (C3 to C6)
MIN_FREQ = 130.81  # Hz (C3)
MAX_FREQ = 1046.50  # Hz (C6)

def play_tone(frequency):
    """Generate and play a sine wave at the given frequency."""
    t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), False)
    tone = 0.5 * np.sin(2 * np.pi * frequency * t)
    sd.play(tone, SAMPLE_RATE)
    sd.wait()

# GUI setup
window = tk.Tk()
window.title("Note Line")
canvas = tk.Canvas(window, width=CANVAS_WIDTH, height=400, bg="white")
canvas.pack()

line_y = 200 #black line in center of screen
canvas.create_line(50, line_y, CANVAS_WIDTH - 50, line_y, width=2, fill="black")

dots = []

def map_x_to_freq(x):
    """Map x (canvas position) to frequency linearly between MIN_FREQ and MAX_FREQ."""
    x = max(50, min(CANVAS_WIDTH - 50, x))  # clamp to avoid out-of-bounds
    norm_x = (x - 50) / (CANVAS_WIDTH - 100)  # normalized between 0 and 1
    freq = MIN_FREQ + norm_x * (MAX_FREQ - MIN_FREQ)
    return freq

def add_dot(event):
    x = event.x
    y = line_y
    dot_radius = 6
    dot = canvas.create_oval(x-dot_radius, y-dot_radius, x+dot_radius, y+dot_radius, fill="blue")
    
    freq = map_x_to_freq(x)

    def on_dot_click(event, f=freq):
        play_tone(f)
    
    canvas.tag_bind(dot, "<Button-1>", on_dot_click)
    dots.append((dot, freq))

# Click canvas to add dot
canvas.bind("<Button-1>", add_dot)

window.mainloop()
