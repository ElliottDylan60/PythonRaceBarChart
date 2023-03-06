import math
from tkinter import BOTH, BOTTOM, HORIZONTAL, LEFT, RIGHT, VERTICAL, X, Y, Frame, Label, Scrollbar, Spinbox, Tk, Canvas
import tkinter
import pandas as pd
from raceplotly.plots import barplot
from PIL import Image, ImageTk
import os
import re
from timeit import default_timer as timer
from datetime import timedelta

frames_folder = "frames"
frames = []

# Taken From 3/5/2023 5:39 PM: https://stackoverflow.com/a/11150413
def natural_sort(l): 
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)] 
    return sorted(l, key=alphanum_key)

def generate_frames():
	df = pd.read_csv('https://raw.githubusercontent.com/lc5415/raceplotly/main/example/dataset/FAOSTAT_data.csv')

	my_raceplot = barplot(df,  item_column='Item', value_column='Value', time_column='Year')
	my_raceplot_plot = my_raceplot.plot(item_label = 'Top 10 crops', value_label = 'Production quantity (tonnes)', frame_duration = 1)

	print("Writing " + str(len(my_raceplot_plot.frames)) + " frames to disk...")
	os.makedirs(frames_folder, exist_ok=True)

	print("Saving Images...")
	# Taken From 3/5/2023 4:03 PM: https://stackoverflow.com/a/73788157
	# generate images for each step in animation
	for s, fr in enumerate(my_raceplot_plot.frames):
		# set main traces to appropriate traces within plotly frame
		my_raceplot_plot.update(data=fr.data)
		# move slider to correct place
		my_raceplot_plot.layout.sliders[0].update(active=s)
		# generate image of current state
		file_name = frames_folder + os.sep + "frame" + str(len(frames)) + ".png"
		my_raceplot_plot.write_image(file=file_name, format="png")
		frames.append(file_name)
		print("Added frame " + str(len(frames)) + " of " + str(len(my_raceplot_plot.frames)))

if os.path.exists(frames_folder):
	for file_name in os.listdir(frames_folder):
		frames.append(frames_folder + os.sep + file_name)
	# frames = sorted(frames)
	frames = natural_sort(frames)

if len(frames) <= 0:
	generate_frames()

def juxtapose(canvas : Canvas, frames : list[str], x_step_offset = 100, y_step_offset = -100, opacity_step_offset : int | None = None, minimum_opacity = 60):
	print("Juxtaposing")
	canvas.images = []

	current_x_offset = len(frames) * x_step_offset
	current_y_offset = len(frames) * y_step_offset
	current_opacity_offset = -255

	frame = Image.open(frames[0])
	frame_size = frame.size
	frame.close()

	if opacity_step_offset == None:
		opacity_step_offset = int(math.ceil(float(-255 / len(frames))))

	base_image_width = abs(frame_size[0] * len(frames))
	base_image_height = abs(frame_size[1] * len(frames))
	base_image = Image.new("RGBA", (base_image_width, base_image_height))
	for image_file_path_index in reversed(range(len(frames))):
		image_file_path = frames[image_file_path_index]
		print("Image: " + image_file_path)

		# Taken From 3/4/2023 4:06 PM: https://stackoverflow.com/a/765829
		image = Image.open(image_file_path)
		image = image.convert("RGBA")
		pixel_data = image.load()

		width, height = image.size
		for y in range(height):
			for x in range(width):
				pixel_color_rgba = pixel_data[x, y]

				# Make all white pixels in the image transparent.
				if pixel_color_rgba == (255, 255, 255, 255):
					pixel_data[x, y] = (255, 255, 255, 0)
				elif image_file_path_index != 0:
					pixel_data[x, y] = (pixel_color_rgba[0], pixel_color_rgba[1], pixel_color_rgba[2], max(min(pixel_color_rgba[3] + current_opacity_offset, 255), minimum_opacity))

		base_image.paste(image, (current_x_offset, current_y_offset + frame_size[1]), image)

		current_x_offset -= x_step_offset
		current_y_offset -= y_step_offset
		current_opacity_offset -= opacity_step_offset

	# base_image.save("juxtaposed.png")
	photo_image = ImageTk.PhotoImage(image=base_image)
	# TODO: These are magic numbers because I cannot wrap my head around what this is even doing or why it function the way it does.
	# canvas.create_image(100, -200, image=photo_image, anchor="nw")
	canvas.create_image(1920 / 2 + 100, 1080 / 2, image=photo_image, anchor="center")
	# canvas.create_image(0, 1080 / 2 + 500, image=photo_image, anchor="sw")
	canvas.images.append(photo_image)

def create_canvas(root : Tk, width : int, height : int):
	canvas = Canvas(root, width=width, height=height, bg='white')
	canvas.images = []
	canvas.pack(fill=BOTH, expand=True)

	return canvas

window = None
canvas = None

global_frames_to_render = None
global_increment_frames = None
current_frame_list = []
time_since_last_juxtapose = None
def juxtapose_next(window : Tk, canvas : Canvas, frames_to_render = 3, increment_frames : int | None = None, override_cooldown_timer = False):
	global time_since_last_juxtapose

	if override_cooldown_timer or time_since_last_juxtapose == None or timedelta(seconds=timer() - time_since_last_juxtapose).seconds <= 1:
		global current_frame_list
		actual_increment_frames = frames_to_render if increment_frames == None else increment_frames
		
		canvas.delete("all")

		if len(current_frame_list) < frames_to_render:
			current_frame_list.extend(frames)

		juxtapose(canvas, current_frame_list[:frames_to_render], 10, -10, minimum_opacity=100)

		for _ in range(actual_increment_frames):
			if len(current_frame_list) <= 0:
				break
			current_frame_list.pop(0)

	time_since_last_juxtapose = timer()
	return window.after(1000, juxtapose_next, window, canvas, int(global_frames_to_render.get()), int(global_increment_frames.get()))

juxtaposition_frame_amount_spin_box : tkinter.StringVar = None

def spinbox_changed():
	juxtapose_next(window, canvas, int(global_frames_to_render.get()), int(global_increment_frames.get()), True)
	juxtaposition_frame_amount_spin_box.to = int(global_frames_to_render.get())
	# Should force the increment frames spinbox to be from 1 to the value of global_frames_to_render, but doesn't work for some reason.
	global_increment_frames.set(int(global_frames_to_render.get()))
	juxtaposition_frame_amount_spin_box.pack()
	
def main():
	global window, canvas
	global global_frames_to_render, global_increment_frames
	global juxtaposition_frame_amount_spin_box

	window = Tk()
	window.title("Bar Chart Race Juxtaposition")
	window.geometry("1600x900")

	global_frames_to_render = tkinter.StringVar(value=3)
	global_increment_frames = tkinter.StringVar(value=3)

	juxtaposition_frame_amount_label = Label(window, text ="Number of Frames to Show", font = "50") 
	juxtaposition_frame_amount_label.pack()

	juxtaposition_frame_amount_spin_box = Spinbox(window, from_ = 1, to=len(frames), textvariable=global_frames_to_render, command=spinbox_changed)   
	juxtaposition_frame_amount_spin_box.pack()

	juxtaposition_frame_increment_label = Label(window, text ="Frame Cycle Amount", font = "50") 
	juxtaposition_frame_increment_label.pack()

	juxtaposition_frame_amount_spin_box = Spinbox(window, from_ = 1, to=len(frames), textvariable=global_increment_frames, command=spinbox_changed)   
	juxtaposition_frame_amount_spin_box.pack()

	canvas = create_canvas(window, 1920, 1080)
	juxtapose_next(window, canvas, int(global_frames_to_render.get()), int(global_increment_frames.get()))

	window.mainloop()

if __name__ == "__main__":
	main()