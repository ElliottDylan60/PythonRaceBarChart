import re
import os
import math

from datetime import timedelta
from timeit import default_timer as timer

from tkinter import BOTH, Frame, Label, Spinbox, Tk, Canvas, StringVar
import pandas as pd
from raceplotly.plots import barplot
from PIL import Image, ImageTk

frames_folder = "frames"
frames = []

window = None
canvas = None

global_frames_to_render = None
global_increment_frames = None
global_x_offset = None
global_y_offset = None
global_animation_interval = None

juxtaposition_increment_frames_spin_box : StringVar = None

current_frame_list = []
time_since_last_juxtapose = None
current_juxtapose_timer = None

spinbox_width = 5
current_column = 0

# Taken From 3/5/2023 5:39 PM: https://stackoverflow.com/a/11150413
def natural_sort(l): 
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)] 
    return sorted(l, key=alphanum_key)

def generate_frames():
	df = pd.read_csv('https://raw.githubusercontent.com/lc5415/raceplotly/main/example/dataset/FAOSTAT_data.csv')

	bar_chart_race = barplot(df,  item_column='Item', value_column='Value', time_column='Year')
	bar_chart_race_plot = bar_chart_race.plot(item_label = 'Top 10 crops', value_label = 'Production quantity (tonnes)', frame_duration = 1)

	print("Writing " + str(len(bar_chart_race_plot.frames)) + " frames to disk...")
	os.makedirs(frames_folder, exist_ok=True)

	print("Saving Images...")
	# Taken From 3/5/2023 4:03 PM: https://stackoverflow.com/a/73788157
	# For every frame of the Plotly chart...
	for slider_position, frame in enumerate(bar_chart_race_plot.frames):
		# ...update the plot with the current frame data.
		bar_chart_race_plot.update(data=frame.data)
		# Move the slider to the position linked with the current frame.
		bar_chart_race_plot.layout.sliders[0].update(active=slider_position)
		# Write the current Plotly frame to disk.
		file_name = frames_folder + os.sep + "frame" + str(len(frames)) + ".png"
		bar_chart_race_plot.write_image(file=file_name, format="png")
		# Append the exported image file path to the frames list.
		frames.append(file_name)
		print("Added frame " + str(len(frames)) + " of " + str(len(bar_chart_race_plot.frames)))

def juxtapose(canvas : Canvas, frames : list[str], x_step_offset = 100, y_step_offset = -100, opacity_step_offset : int | None = None, minimum_opacity = 60):
	print("Juxtaposing...")
	canvas.images = []

	# Need to work backwards from the furthest, last element back towards the first element to ensure that the images are stacked correctly (painter's algorithm).
	current_x_offset = (len(frames) - 1) * x_step_offset
	current_y_offset = (len(frames) - 1) * y_step_offset
	current_opacity_offset = -255

	frame = Image.open(frames[0])
	first_frame_width, first_frame_height = frame.size
	frame.close()

	if opacity_step_offset == None:
		opacity_step_offset = int(math.ceil(float(-255 / len(frames))))

	# Create a canvas image which will allow all juxtaposed frames to be properly written, calculated by taking the first frame size and adding the x_step_offset, then multiply for every frame to be written.
	# TODO: This is both potentially an overestimation and a underestimation, as the first frame might be smaller than subsequent frames and the offset only consume half of the actual distance due to the frame being offset from the center.
	new_canvas_image = Image.new("RGBA", (len(frames) * (first_frame_width + abs(x_step_offset)), len(frames) * first_frame_height + abs(y_step_offset)))
	for image_file_path_index in reversed(range(len(frames))):
		image_file_path = frames[image_file_path_index]
		print("Juxtaposing Image at Path: '" + image_file_path + "'")

		# Taken From 3/4/2023 4:06 PM: https://stackoverflow.com/a/765829
		image = Image.open(image_file_path)
		image = image.convert("RGBA")
		pixel_data = image.load()

		current_image_width, current_image_height = image.size
		for y in range(current_image_height):
			for x in range(current_image_width):
				pixel_color_rgba = pixel_data[x, y]

				# Make all white pixels in the image transparent.
				if pixel_color_rgba == (255, 255, 255, 255):
					pixel_data[x, y] = (255, 255, 255, 0)
				elif image_file_path_index != 0:
					pixel_data[x, y] = (pixel_color_rgba[0], pixel_color_rgba[1], pixel_color_rgba[2], max(min(pixel_color_rgba[3] + current_opacity_offset, 255), minimum_opacity))

		new_canvas_image.paste(image, (current_x_offset, current_y_offset + current_image_height), image)

		current_x_offset -= x_step_offset
		current_y_offset -= y_step_offset
		current_opacity_offset -= opacity_step_offset

	photo_image = ImageTk.PhotoImage(image=new_canvas_image)
	# Need to offset by the amount of height the vertical control bar takes up.
	# TODO: Should pull this from the vertical control box element rather than hardcoding this.
	canvas.create_image(0, -50, image=photo_image, anchor="nw")
	canvas.images.append(photo_image)

def create_canvas(root : Tk, width : int, height : int):
	canvas = Canvas(root, width=width, height=height, bg='white')
	canvas.images = []
	canvas.pack(fill=BOTH, expand=True)

	return canvas

def juxtapose_next(canvas : Canvas, frames_to_render = 3, increment_frames : int | None = None, x_offset = 10, y_offset = -10):
	global current_frame_list
	actual_increment_frames = frames_to_render if increment_frames == None else increment_frames
	
	canvas.delete("all")

	if len(current_frame_list) < frames_to_render:
		current_frame_list.extend(frames)

	juxtapose(canvas, current_frame_list[:frames_to_render], x_offset, y_offset, minimum_opacity=100)

	for _ in range(actual_increment_frames):
		if len(current_frame_list) <= 0:
			break
		current_frame_list.pop(0)

def juxtapose_next_global(window : Tk, canvas : Canvas, override_cooldown_timer = False):
	global time_since_last_juxtapose

	global_animation_delay_interval = int(global_animation_interval.get())

	time_difference = timedelta(seconds=timer() - time_since_last_juxtapose).seconds if time_since_last_juxtapose != None else 0
	if override_cooldown_timer or time_since_last_juxtapose == None or time_difference >= global_animation_delay_interval:
		try:
			frames_to_render = int(global_frames_to_render.get())
			increment_frames = int(global_increment_frames.get())
			x_offset = int(global_x_offset.get())
			y_offset = int(global_y_offset.get())

			juxtapose_next(canvas, frames_to_render, increment_frames, x_offset, y_offset)

			time_since_last_juxtapose = timer()
		except:
			pass

	return window.after(1000, juxtapose_next_global, window, canvas)

def spinbox_changed():
	# Limit the increment frames to the maximum of the frames we are rendering at once.
	juxtaposition_increment_frames_spin_box.config(to=int(global_frames_to_render.get()))

def main():
	global window, canvas
	global global_frames_to_render, global_increment_frames, global_x_offset, global_y_offset, global_animation_interval
	global juxtaposition_increment_frames_spin_box
	global frames

	# Check if we need to initialize the plot frame files for the juxtaposition.
	if os.path.exists(frames_folder):
		for file_name in os.listdir(frames_folder):
			frames.append(frames_folder + os.sep + file_name)

		frames = natural_sort(frames)

	# If no frames are in the frames list, generate the frame images for the dataset.
	if len(frames) <= 0:
		generate_frames()

	# Create the main window.
	window = Tk()
	window.title("Bar Chart Race Juxtaposition")
	window.geometry("1600x900")

	# Initialize the global control variables.
	global_frames_to_render = StringVar(value=3)
	global_increment_frames = StringVar(value=3)
	global_x_offset = StringVar(value=10)
	global_y_offset = StringVar(value=-10)
	global_animation_interval = StringVar(value=1)

	controls_frame = Frame()
	controls_frame.pack()

	#
	# Vertical Control Box Elements
	#
	def increment_column():
		global current_column
		previous_column = current_column
		current_column += 1
		return previous_column

	juxtaposition_frame_amount_label = Label(controls_frame, text ="Number of Frames to Show: ", font = "50", anchor="w")
	juxtaposition_frame_amount_label.grid(row=0, column=increment_column())

	juxtaposition_frame_amount_spin_box = Spinbox(controls_frame, width=spinbox_width, from_=1, to=len(frames), textvariable=global_frames_to_render, command=spinbox_changed)
	juxtaposition_frame_amount_spin_box.grid(row=0, column=increment_column())

	juxtaposition_frame_increment_label = Label(controls_frame, text ="Frame Cycle Amount: ", font = "50")
	juxtaposition_frame_increment_label.grid(row=0, column=increment_column())

	juxtaposition_increment_frames_spin_box = Spinbox(controls_frame, width=spinbox_width, from_=1, to=len(frames), textvariable=global_increment_frames, command=spinbox_changed)
	juxtaposition_increment_frames_spin_box.grid(row=0, column=increment_column())

	juxtaposition_x_offset_label = Label(controls_frame, text ="X Offset: ", font = "50")
	juxtaposition_x_offset_label.grid(row=0, column=increment_column())

	juxtaposition_x_offset_spin_box = Spinbox(controls_frame, width=spinbox_width, from_=-250, to=250, textvariable=global_x_offset, command=spinbox_changed)
	juxtaposition_x_offset_spin_box.grid(row=0, column=increment_column())

	juxtaposition_y_offset_label = Label(controls_frame, text ="Y Offset: ", font = "50")
	juxtaposition_y_offset_label.grid(row=0, column=increment_column())

	juxtaposition_y_offset_spin_box = Spinbox(controls_frame, width=spinbox_width, from_=-250, to=250, textvariable=global_y_offset, command=spinbox_changed)
	juxtaposition_y_offset_spin_box.grid(row=0, column=increment_column())

	juxtaposition_y_offset_label = Label(controls_frame, text ="Animation Interval: ", font = "50")
	juxtaposition_y_offset_label.grid(row=0, column=increment_column())

	juxtaposition_animation_interval_spin_box = Spinbox(controls_frame, width=spinbox_width, from_=1, to=60, textvariable=global_animation_interval, command=spinbox_changed)
	juxtaposition_animation_interval_spin_box.grid(row=0, column=increment_column())
	#
	#
	#

	canvas = create_canvas(window, 1920, 1080)

	# Start juxtaposition loop.
	juxtapose_next_global(window, canvas)

	window.mainloop()

if __name__ == "__main__":
	main()