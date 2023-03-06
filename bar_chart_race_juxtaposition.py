import random
from tkinter import Tk, Canvas
import pandas as pd
from raceplotly.plots import barplot
from PIL import Image, ImageTk
import os

df = pd.read_csv('https://raw.githubusercontent.com/lc5415/raceplotly/main/example/dataset/FAOSTAT_data.csv')

my_raceplot = barplot(df,  item_column='Item', value_column='Value', time_column='Year')
my_raceplot_plot = my_raceplot.plot(item_label = 'Top 10 crops', value_label = 'Production quantity (tonnes)', frame_duration = 1)

print("Frames: " + str(len(my_raceplot_plot.frames)))

frames_folder = "frames"
os.makedirs(frames_folder, exist_ok=True)

# Taken From 3/5/2023 4:03 PM: https://stackoverflow.com/a/73788157
# generate images for each step in animation
frames = []
for s, fr in enumerate(my_raceplot_plot.frames):
	# set main traces to appropriate traces within plotly frame
	my_raceplot_plot.update(data=fr.data)
	# move slider to correct place
	my_raceplot_plot.layout.sliders[0].update(active=s)
	# generate image of current state
	file_name = frames_folder + os.sep + "frame" + str(len(frames)) + ".png"
	my_raceplot_plot.write_image(file=file_name, format="png")
	frames.append(file_name)

# create animated GIF
# frames[0].save("test.gif", save_all=True, append_images=frames[1:], optimize=True, duration=500, loop=0)

def juxtapose(canvas : Canvas, frames : list[str], x_step_offset = 100, y_step_offset = -100, opacity_step_offset = -100):
	current_x_offset = 0
	current_y_offset = 0
	current_opacity_offset = 0

	for image_file_path_index in range(len(frames)):
	# for image_file_path_index in reversed(range(len(frames))):
		image_file_path = frames[image_file_path_index]

		# Taken From 3/4/2023 4:06 PM: https://stackoverflow.com/a/765829
		img = Image.open(image_file_path)
		img = img.convert("RGBA")

		pixdata = img.load()

		width, height = img.size
		# if image_file_path_index != 0:
		for y in range(height):
			for x in range(width):
				pixel_color_rgba = pixdata[x, y]

				# Make all white pixels in the image transparent.
				if pixel_color_rgba == (255, 255, 255, 255):
					pixdata[x, y] = (255, 255, 255, 0)
				else:
					pixdata[x, y] = (pixel_color_rgba[0], pixel_color_rgba[1], pixel_color_rgba[2], min(pixel_color_rgba[3] + current_opacity_offset, 255))

		photo_image = ImageTk.PhotoImage(img)
		canvas.create_image(current_x_offset + (width / 2), current_y_offset + (height / 2), image=photo_image)
		canvas.images.append(photo_image)

		current_x_offset += x_step_offset
		current_y_offset += y_step_offset
		current_opacity_offset += opacity_step_offset

max_frames = 2
if __name__ == "__main__":
	window = Tk()
	window.title("Bar Chart Race Juxtaposition")
		
	# canvas = Canvas(window, width=1600, height=900, bg='lightGrey')
	canvas = Canvas(window, width=1600, height=900, bg='white')
	canvas.images = []
	canvas.pack()

	juxtapose(canvas, frames[:3])

	window.mainloop()