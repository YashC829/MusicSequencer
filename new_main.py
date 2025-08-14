'''
next steps:
enable multiple notes to play at same time
make clicking note for sound or add less delayed 
enable user to adjust note pitch by sliding left and right
'''

import tkinter as tk
import numpy as np
import sounddevice as sd

# Constants
DURATION = 2  # seconds the tone plays
SAMPLE_RATE = 44100
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 400
LINE_Y = 200
MIN_FREQ = 130.81  # C3
MAX_FREQ = 1046.50  # C6

adding_notes = False  # add mode toggle
deleting_notes = False # delete mode toggle

dots = []  # List of (dot_id, frequency, tone)

# Generate a tone for a given frequency
def generate_tone(frequency):
    t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), False)
    tone = 0.5 * np.sin(2 * np.pi * frequency * t)
    return tone

# Map x-position to frequency in the range C3–C6
def map_x_to_freq(x):
    # pitch is on a logarithmic scale
    x = max(50, min(CANVAS_WIDTH - 50, x))
    norm_x = (x - 50) / (CANVAS_WIDTH - 100)
    log_min = np.log2(MIN_FREQ)
    log_max = np.log2(MAX_FREQ)
    freq = 2 ** (log_min + norm_x * (log_max - log_min))
    return freq

# GUI setup
window = tk.Tk()
window.title("Note Line Editor")
canvas = tk.Canvas(window, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="white")
canvas.pack()

# Draw black horizontal line
canvas.create_line(50, LINE_Y, CANVAS_WIDTH - 50, LINE_Y, width=2, fill="black")
# Draw vertical lines dividing the center line into thirds
section_width = (CANVAS_WIDTH - 100) / 3  # Subtracting margins (50 on each side)
for i in range(1, 3):  # Draw at 1/3 and 2/3 positions
    x = 50 + i * section_width
    canvas.create_line(x, 0, x, CANVAS_HEIGHT, fill="lightgray", dash=(4, 2))

# Toggle add-note mode
def toggle_add_mode():
    global adding_notes
    adding_notes = not adding_notes
    if adding_notes:
        plus_button.config(text="✅ Done Adding")
    else:
        plus_button.config(text="➕ Add Notes")

plus_button = tk.Button(window, text="➕ Add Notes", command=toggle_add_mode)
plus_button.place(x=10, y=10)

def toggle_delete_mode():
    global deleting_notes, adding_notes
    deleting_notes = not deleting_notes

    if deleting_notes:
        delete_button.config(text="✅ Done Deleting")
        adding_notes = False
        plus_button.config(text="➕ Add Notes")  # Reset add mode if active
    else:
        delete_button.config(text="🗑 Delete Notes")

delete_button = tk.Button(window, text="🗑 Delete Notes", command=toggle_delete_mode)
delete_button.place(x=150, y=10)  # Adjust position next to add button

# Canvas click handler (adds note if in add mode)
def on_canvas_click(event):
    if not adding_notes:
        return

    x = event.x
    y = LINE_Y
    radius = 6
    freq = map_x_to_freq(x)
    tone = generate_tone(freq)
    dot_id = canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="blue")

   # rectangular pop up appears when right click on note
    def show_frequency_popup(event, dot_id=dot_id, freq=freq):
        # Get dot center position
        x1, y1, x2, y2 = canvas.coords(dot_id)
        dot_center_x = (x1 + x2) / 2
        dot_center_y = (y1 + y2) / 2

        # Create text first so we can measure it
        text_id = canvas.create_text(
            dot_center_x,
            dot_center_y + 20,
            text=f"{freq:.2f} Hz",
            fill="black",
            font=("Arial", 15, "bold")
        )

        # Get bounding box of text to create a rectangle background
        bbox = canvas.bbox(text_id)  # (x1, y1, x2, y2)
        rect_id = canvas.create_rectangle(
            bbox[0] - 4, bbox[1] - 2, bbox[2] + 4, bbox[3] + 2,
            fill="lightyellow", outline="black"
        )

        # Raise text above rectangle
        canvas.tag_raise(text_id, rect_id)

        # Store IDs so we can delete them later
        popup_items = (rect_id, text_id)

        # Function to remove popup
        def remove_popup(e=None):
            for item in popup_items:
                canvas.delete(item)

        # Remove popup on next click anywhere
        canvas.bind("<Button-1>", remove_popup, add="+")
        canvas.bind("<Button-3>", remove_popup, add="+")  # right click elsewhere

    canvas.tag_bind(dot_id, "<Button-2>", show_frequency_popup) # mac: right click two fingers on trackpad
    canvas.tag_bind(dot_id, "<Button-3>", show_frequency_popup) 
    

    # Click on dot → play tone + highlight
    def on_dot_click(event, dot_id=dot_id, tone=tone):
        global deleting_notes
        if deleting_notes:
        # Remove from canvas
            canvas.delete(dot_id)
            # Remove from dots list
            for i, (d_id, _, _) in enumerate(dots):
                if d_id == dot_id:
                    dots.pop(i)
                    break
            return
    
        canvas.itemconfig(dot_id, fill="red")

        #sd.play(tone, SAMPLE_RATE)
        #play current and all other tones
        active_tones = [tone]
        # Get currently red (active) dots and their tones
        for other_id, _, other_tone in dots:
            if canvas.itemcget(other_id, "fill") == "red" and other_id != dot_id:
                active_tones.append(other_tone)

        # Mix tones
        mixed = np.sum(active_tones, axis=0)
        mixed /= np.max(np.abs(mixed))  # Normalize to avoid clipping

        sd.play(mixed, SAMPLE_RATE)

        canvas.after(int(DURATION * 1000), lambda: canvas.itemconfig(dot_id, fill="blue"))

    canvas.tag_bind(dot_id, "<Button-1>", on_dot_click)
    dots.append((dot_id, freq, tone))

# Bind canvas click
canvas.bind("<Button-1>", on_canvas_click)

window.mainloop()
