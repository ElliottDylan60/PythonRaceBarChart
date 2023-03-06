import math
from tkinter import BOTH, BOTTOM, HORIZONTAL, LEFT, RIGHT, VERTICAL, X, Y, Frame, Scrollbar, Tk, Canvas
import pandas as pd
from raceplotly.plots import barplot
from PIL import Image, ImageTk
import os
import re

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

def juxtapose(canvas : Canvas, frames : list[str], x_step_offset = 100, y_step_offset = -100, opacity_step_offset = None):
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

	base_image_width = frame_size[0] * len(frames)
	base_image_height = frame_size[1] * len(frames)
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
					pixel_data[x, y] = (pixel_color_rgba[0], pixel_color_rgba[1], pixel_color_rgba[2], max(min(pixel_color_rgba[3] + current_opacity_offset, 255), 75))

		base_image.paste(image, (current_x_offset, current_y_offset + frame_size[1]), image)

		current_x_offset -= x_step_offset
		current_y_offset -= y_step_offset
		current_opacity_offset -= opacity_step_offset

	# base_image.save("juxtaposed.png")
	photo_image = ImageTk.PhotoImage(image=base_image)
	canvas.create_image(0, 0, image=photo_image, anchor="nw")
	canvas.images.append(photo_image)

def create_canvas(root, width, height):
	# canvas = Canvas(window, width=10000, height=10000, bg='white')
	# canvas.images = []
	# canvas.pack()

	# Taken From 3/5/2023 5:00 PM: https://stackoverflow.com/a/7734187
	frame=Frame(root,width=width,height=height)
	frame.pack(expand=True, fill=BOTH) #.grid(row=0,column=0)
	canvas=Canvas(frame,bg='#FFFFFF',width=width,height=height,scrollregion=(0,0,500,500))
	hbar=Scrollbar(frame,orient=HORIZONTAL)
	hbar.pack(side=BOTTOM,fill=X)
	hbar.config(command=canvas.xview)
	vbar=Scrollbar(frame,orient=VERTICAL)
	vbar.pack(side=RIGHT,fill=Y)
	vbar.config(command=canvas.yview)
	canvas.config(width=width,height=height)
	canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
	canvas.pack(side=LEFT,expand=True,fill=BOTH)

	return canvas

current_frame_list = []
def juxtapose_next(window : Tk, canvas : Canvas, frames_to_render = 3):
	global current_frame_list
	
	canvas.delete("all")

	if len(current_frame_list) < frames_to_render:
		current_frame_list.extend(frames)
		print(str(current_frame_list))

	juxtapose(canvas, current_frame_list[:frames_to_render])

	print("len(current_frame_list): " + str(len(current_frame_list)))
	for _ in range(frames_to_render):
		if len(current_frame_list) <= 0:
			break
		current_frame_list.pop(0)

	window.after(1000, juxtapose_next, window, canvas, frames_to_render)

if __name__ == "__main__":
	window = Tk()
	window.title("Bar Chart Race Juxtaposition")
	window.geometry("1600x900")

	canvas = create_canvas(window, 1920, 1080)

	juxtapose_next(window, canvas, 3)

	window.mainloop()