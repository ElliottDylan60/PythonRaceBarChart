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

# generate images for each step in animation
frames = []
for s, fr in enumerate(my_raceplot_plot.frames):
	# set main traces to appropriate traces within plotly frame
	my_raceplot_plot.update(data=fr.data)
	# move slider to correct place
	my_raceplot_plot.layout.sliders[0].update(active=s)
	# generate image of current state
	# frames.append(Image.open(io.BytesIO(my_raceplot_plot.to_image(format="png"))))
	# frames.append(my_raceplot_plot.to_image(format="png"))

	file_name = frames_folder + os.sep + "frame" + str(len(frames)) + ".png"
	my_raceplot_plot.write_image(file=file_name, format="png")
	frames.append(file_name)

# create animated GIF
# frames[0].save("test.gif", save_all=True, append_images=frames[1:], optimize=True, duration=500, loop=0)

max_frames = 2
if __name__ == "__main__":
	window = Tk()
	window.title("Bar Chart Race Juxtaposition")
		
	canvas = Canvas(window, width=1600, height=900, bg='lightGrey')
	canvas.images = []
	canvas.pack()
	for image_file_path in frames:
		# can.create_image(150, 150, image=ImageTk.PhotoImage(data=io.BytesIO(image)), format="png")
		# can.create_image(150, 150, image=PhotoImage(data=io.BytesIO(image)), format="png")
		# canvas.create_image(0, 0, image=PhotoImage(data=image, format="png"))

		# Taken From 3/4/2023 4:06 PM: https://stackoverflow.com/a/765829
		img = Image.open(image_file_path)
		img = img.convert("RGBA")

		pixdata = img.load()

		width, height = img.size
		for y in range(height):
			for x in range(width):
				if pixdata[x, y] == (255, 255, 255, 255):
					pixdata[x, y] = (255, 255, 255, 0)
				# pixdata[x, y] = (255, 255, 255, random.randint(0, 255))
				# pixdata[x, y] = (255, 255, 255, 255)
				# pixdata[x, y] = (pixdata[x, y][0], pixdata[x, y][1], pixdata[x, y][2], random.randint(0, 255))

		photo_image = ImageTk.PhotoImage(img)
		# canvas.create_image(random.randint(400, 1200), random.randint(400, 1200), image=photo_image)
		canvas.create_image(random.randint(400, 500), random.randint(400, 500), image=photo_image)
		canvas.images.append(photo_image)

		if len(canvas.images) >= max_frames:
			break

	window.mainloop()