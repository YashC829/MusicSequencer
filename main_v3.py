import tkinter as tk
import numpy as np
import sounddevice as sd

# Constants
DURATION = 0.5  # seconds the tone plays
SAMPLE_RATE = 44100
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 400
LINE_Y = 200
MIN_FREQ = 130.81  # C3
MAX_FREQ = 1046.50  # C6

# Modes
adding_notes = False
deleting_notes = False
dragging_dot = None

dots = []  # List of (dot_id, frequency, tone)

# Generate a tone for a given frequency
def generate_tone(frequency):
    t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), False)
    tone = 0.5 * np.sin(2 * np.pi * frequency * t)
    return tone

# Map x-position to frequency (logarithmic)
def map_x_to_freq(x):
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

# Draw horizontal line
canvas.create_line(50, LINE_Y, CANVAS_WIDTH - 50, LINE_Y, width=2, fill="black")

# Draw vertical thirds
section_width = (CANVAS_WIDTH - 100) / 3
for i in range(1, 3):
    x = 50 + i * section_width
    canvas.create_line(x, 0, x, CANVAS_HEIGHT, fill="lightgray", dash=(4, 2))

# Add Notes button
def toggle_add_mode():
    global adding_notes, deleting_notes
    adding_notes = not adding_notes
    if adding_notes:
        plus_button.config(text="✅ Done Adding Notes")
        deleting_notes = False
        delete_button.config(text="🗑 Delete Notes")
    else:
        plus_button.config(text="➕ Add Notes")

plus_button = tk.Button(window, text="➕ Add Notes", command=toggle_add_mode)
plus_button.place(x=10, y=10)

# Delete Notes button
def toggle_delete_mode():
    global deleting_notes, adding_notes
    deleting_notes = not deleting_notes
    if deleting_notes:
        delete_button.config(text="✅ Done Deleting")
        adding_notes = False
        plus_button.config(text="➕ Add Notes")
    else:
        delete_button.config(text="🗑 Delete Notes")

delete_button = tk.Button(window, text="🗑 Delete Notes", command=toggle_delete_mode)
delete_button.place(x=150, y=10)

# Create frequency popup on right-click
def show_frequency_popup(event, dot_id, freq):
    x1, y1, x2, y2 = canvas.coords(dot_id)
    dot_center_x = (x1 + x2) / 2
    dot_center_y = (y1 + y2) / 2

    text_id = canvas.create_text(
        dot_center_x,
        dot_center_y + 20,
        text=f"{freq:.2f} Hz",
        fill="black",
        font=("Arial", 10, "bold")
    )
    bbox = canvas.bbox(text_id)
    rect_id = canvas.create_rectangle(
        bbox[0] - 4, bbox[1] - 2, bbox[2] + 4, bbox[3] + 2,
        fill="lightyellow", outline="black"
    )
    canvas.tag_raise(text_id, rect_id)

    def remove_popup(e=None):
        canvas.delete(rect_id)
        canvas.delete(text_id)
        canvas.unbind("<Button-1>", remove_popup)
        canvas.unbind("<Button-2>", remove_popup)
        canvas.unbind("<Button-3>", remove_popup)

    canvas.bind("<Button-1>", remove_popup)
    canvas.bind("<Button-2>", remove_popup)
    canvas.bind("<Button-3>", remove_popup)

# Drag functions
def start_drag(event, dot_id):
    global dragging_dot
    if adding_notes or deleting_notes:
        return
    dragging_dot = dot_id

def drag_dot(event):
    global dragging_dot
    if dragging_dot is None:
        return
    x = max(50, min(CANVAS_WIDTH - 50, event.x))
    y = LINE_Y
    radius = 6
    canvas.coords(dragging_dot, x - radius, y - radius, x + radius, y + radius)

    # Update frequency and tone
    for i, (d_id, _, _) in enumerate(dots):
        if d_id == dragging_dot:
            new_freq = map_x_to_freq(x)
            new_tone = generate_tone(new_freq)
            dots[i] = (d_id, new_freq, new_tone)
            break

def stop_drag(event):
    global dragging_dot
    dragging_dot = None

canvas.bind("<B1-Motion>", drag_dot)
canvas.bind("<ButtonRelease-1>", stop_drag)

# Play note on right click
def play_note_and_popup(event, dot_id):
    # Play note
    freq = None
    tone = None
    for d_id, f, t in dots:
        if d_id == dot_id:
            freq = f
            tone = t
            break
    if tone is None:
        return

    canvas.itemconfig(dot_id, fill="red")

    # Mix active notes
    active_tones = [tone]
    for other_id, _, other_tone in dots:
        if canvas.itemcget(other_id, "fill") == "red" and other_id != dot_id:
            active_tones.append(other_tone)

    mixed = np.sum(active_tones, axis=0)
    mixed /= np.max(np.abs(mixed))

    sd.play(mixed, SAMPLE_RATE)
    canvas.after(int(DURATION * 1000), lambda: canvas.itemconfig(dot_id, fill="blue"))

    # Show frequency popup
    show_frequency_popup(event, dot_id, freq)

# Canvas click to add notes
def on_canvas_click(event):
    if not adding_notes:
        return

    x = event.x
    y = LINE_Y
    radius = 6
    freq = map_x_to_freq(x)
    tone = generate_tone(freq)
    dot_id = canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="blue")
    dots.append((dot_id, freq, tone))

    # Bind dragging start (left click)
    canvas.tag_bind(dot_id, "<Button-1>", lambda e, d_id=dot_id: start_drag(e, d_id))

    # Bind right-click to play and popup
    canvas.tag_bind(dot_id, "<Button-2>", lambda e, d_id=dot_id: play_note_and_popup(e, d_id))
    canvas.tag_bind(dot_id, "<Button-3>", lambda e, d_id=dot_id: play_note_and_popup(e, d_id))

    # Bind delete functionality
    def on_delete(event, d_id=dot_id):
        global dots
        if deleting_notes:
            canvas.delete(d_id)
            dots = [item for item in dots if item[0] != d_id]

    canvas.tag_bind(dot_id, "<Button-1>", on_delete, add="+")  # delete triggers only in delete mode

canvas.bind("<Button-1>", on_canvas_click)

window.mainloop()
