import re
import os
import math
from tkinter.ttk import Combobox
import traceback

from datetime import timedelta
from timeit import default_timer as timer

from tkinter import BOTH, Frame, Label, Spinbox, Tk, Canvas, StringVar
import pandas as pd
from raceplotly.plots import barplot
from PIL import Image, ImageTk

frames_folder = "frames"
os.makedirs(frames_folder, exist_ok=True)
# Contains a dataset .scv filepath mapped to the frames for that visualization.
dataset_filepath_to_frames_map = dict()

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

# Contains all the data for a dataset, including filepath to the csv and what the column keys and labels should be.
class DatasetData:
	def __init__(self, dataset_file_path : str, item_column : str, value_column : str, time_column : str, item_label : str, value_label : str, frame_duration = 1):
		self.dataset_file_path = dataset_file_path
		self.item_column = item_column
		self.value_column = value_column
		self.time_column = time_column
		self.item_label = item_label
		self.value_label = value_label
		self.frame_duration = frame_duration

dataset_data_array : list[DatasetData] = [
	DatasetData("FAOSTAT_data.csv", "Item", "Value", "Year", "Top 10 Crops", "Production Quantity (tonnes)", 1), 
	DatasetData("covid.csv", "AL", "AL", "date", "AL", "Deaths"),
]

# Taken From 3/5/2023 5:39 PM: https://stackoverflow.com/a/11150413
# Essentially sorts based on numbers, which is important for our frame file iteration.
def natural_sort(l): 
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)] 
    return sorted(l, key=alphanum_key)

def generate_dataset_frames_folder(dataset_data : DatasetData):
	return dataset_data.dataset_file_path.split(".")[0]

def generate_frames(dataset_data : DatasetData):
	try:
		df = pd.read_csv(dataset_data.dataset_file_path)

		# Initialize dictionary key for the current dataset file path to an empty array.
		dataset_filepath_to_frames_map[dataset_data.dataset_file_path] = []

		bar_chart_race = barplot(df, item_column=dataset_data.item_column, value_column=dataset_data.value_column, time_column=dataset_data.time_column)
		bar_chart_race_plot = bar_chart_race.plot(item_label = dataset_data.item_label, value_label = dataset_data.value_label, frame_duration = dataset_data.frame_duration)

		print("Writing " + str(len(bar_chart_race_plot.frames)) + " frames to disk for the dataset '" + dataset_data.dataset_file_path + "'...")
		# Taken From 3/5/2023 4:03 PM: https://stackoverflow.com/a/73788157
		# For every frame of the Plotly chart...
		for slider_position, frame in enumerate(bar_chart_race_plot.frames):
			# ...update the plot with the current frame data.
			bar_chart_race_plot.update(data=frame.data)
			# Move the slider to the position linked with the current frame.
			bar_chart_race_plot.layout.sliders[0].update(active=slider_position)

			dataset_frames_folder_path = frames_folder + os.sep + generate_dataset_frames_folder(dataset_data)
			# Create the directory structure for the images to be stored in.
			os.makedirs(dataset_frames_folder_path, exist_ok=True)

			# Write the current Plotly frame to disk.
			file_path = dataset_frames_folder_path + os.sep + "frame_" + str(len(dataset_filepath_to_frames_map[dataset_data.dataset_file_path])) + ".png"
			bar_chart_race_plot.write_image(file=file_path, format="png")
			# Append the exported image file path to the frames list for the current dataset key.
			dataset_filepath_to_frames_map[dataset_data.dataset_file_path].append(file_path)
			print("Added frame " + str(len(dataset_filepath_to_frames_map[dataset_data.dataset_file_path])) + " of " + str(len(bar_chart_race_plot.frames)))
	except Exception:
		print("Got invalid dataset data from DatasetData '" + str(dataset_data.dataset_file_path) + "'. Exception: ")
		traceback.print_exc()

def juxtapose(canvas : Canvas, frames : list[str], x_step_offset = 100, y_step_offset = -100, opacity_step_offset : int | None = None, minimum_opacity = 60):
	# Clear the canvas's stored PhotoImage's. This is required to keep the image alive and prevent it from being garbage collected, a quirk of Tkinter.
	canvas.images = []
	print("Juxtaposing...")

	# Need to work backwards from the furthest, last element back towards the first element to ensure that the images are stacked correctly (painter's algorithm).
	current_x_offset = (len(frames) - 1) * x_step_offset
	current_y_offset = (len(frames) - 1) * y_step_offset
	current_opacity_offset = -255

	frame = Image.open(frames[0])
	first_frame_width, first_frame_height = frame.size
	frame.close()

	if opacity_step_offset == None:
		opacity_step_offset = int(math.ceil(float(-255 / len(frames))))

	# Create a canvas image which will allow all juxtaposed frames to be properly written, calculated by taking the first frame size and adding the x_step_offset, then multiply for every frame to be written. As stated above, this needs to be iterated backwards to render the images correctly (painter's algorithm).
	# TODO: This size is both potentially an over-estimation and a under-estimation, as the first frame might be smaller than subsequent frames and the offset only consume half of the actual distance due to the frame being offset from the center.
	new_canvas_image = Image.new("RGBA", (len(frames) * (first_frame_width + abs(x_step_offset)), len(frames) * first_frame_height + abs(y_step_offset)))
	for image_file_path_index in reversed(range(len(frames))):
		image_file_path = frames[image_file_path_index]
		print("Juxtaposing Image at Path: '" + image_file_path + "'")

		# Taken From 3/4/2023 4:06 PM: https://stackoverflow.com/a/765829
		image = Image.open(image_file_path)
		image = image.convert("RGBA")
		pixel_data = image.load()

		current_image_width, current_image_height = image.size
		# Iterate every pixel in the current image.
		for y in range(current_image_height):
			for x in range(current_image_width):
				pixel_color_rgba = pixel_data[x, y]

				# Make all white pixels in the image transparent.
				if pixel_color_rgba == (255, 255, 255, 255):
					pixel_data[x, y] = (255, 255, 255, 0)
				elif image_file_path_index != 0:
					# If this isn't the first image we are showing (the one closest to 0, 0), modify it's opacity to be the current pixel's opacity offset by the current opacity offset, constrained to between the minimum_opacity value and 255.
					pixel_data[x, y] = (pixel_color_rgba[0], pixel_color_rgba[1], pixel_color_rgba[2], max(min(pixel_color_rgba[3] + current_opacity_offset, 255), minimum_opacity))

		# Paste the juxtaposed image to the canvas image.
		new_canvas_image.paste(image, (current_x_offset, current_y_offset + current_image_height), image)

		current_x_offset -= x_step_offset
		current_y_offset -= y_step_offset
		current_opacity_offset -= opacity_step_offset

	# Create a Tkinter PhotoImage from the canvas image constructed from the juxtaposed images above.
	photo_image = ImageTk.PhotoImage(image=new_canvas_image)

	# Need to offset by the amount of height the vertical control bar takes up.
	# TODO: Should pull this offset from the vertical control box element rather than hardcoding this.
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
	
	# Clear the display canvas of all image data.
	canvas.delete("all")

	# If the current frame list has too little frames for how many we want to render, append to the back of the list the entire plot frame list.
	if len(current_frame_list) < frames_to_render:
		current_frame_list.extend(current_dataset_frames())

	# Juxtapose a slice of the current_frame_list, taking up to frames_to_render elements.
	juxtapose(canvas, current_frame_list[:frames_to_render], x_offset, y_offset, minimum_opacity=100)

	# Remove all of the frames we rendered.
	for _ in range(actual_increment_frames):
		if len(current_frame_list) <= 0:
			break
		current_frame_list.pop(0)

def juxtapose_next_global(window : Tk, canvas : Canvas, override_cooldown_timer = False):
	global time_since_last_juxtapose

	global_animation_delay_interval = int(global_animation_interval.get())

	time_difference = timedelta(seconds=timer() - time_since_last_juxtapose).seconds if time_since_last_juxtapose != None else 0
	if override_cooldown_timer or time_since_last_juxtapose == None or time_difference >= global_animation_delay_interval:
		# Attempt to parse the global spinbox values. If that doesn't raise an exception, pass those to the juxtapose_next function which will actually juxtapose the frames.
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

def current_dataset_frames():
	return dataset_filepath_to_frames_map[global_dataset_key.get()]

def dataset_changed(*args):
	global current_frame_list

	current_frame_list.clear()

def main():
	global window, canvas
	global global_frames_to_render, global_increment_frames, global_x_offset, global_y_offset, global_animation_interval, global_dataset_key
	global juxtaposition_increment_frames_spin_box
	global dataset_filepath_to_frames_map

	# Check if we need to initialize the plot frame files for the juxtaposition of any of the loaded datasets.
	for dataset_data in dataset_data_array:
		dataset_file_path = dataset_data.dataset_file_path

		# Generate this datasets frame folder in the case it doesn't exist.
		dataset_frames_folder_path = frames_folder + os.sep + generate_dataset_frames_folder(dataset_data)
		os.makedirs(dataset_frames_folder_path, exist_ok=True)

		dataset_frames_folder_files = os.listdir(dataset_frames_folder_path)

		# Initialize the dataset frames to an empty array.
		dataset_filepath_to_frames_map[dataset_data.dataset_file_path] = []

		for file_name in dataset_frames_folder_files:
			# TODO: Check if file is actually an image before appending it to the frame list.
			dataset_filepath_to_frames_map[dataset_file_path].append(dataset_frames_folder_path + os.sep + file_name)

		# Sort by frame number using a natural sort algorithm.
		dataset_filepath_to_frames_map[dataset_file_path] = natural_sort(dataset_filepath_to_frames_map[dataset_file_path])

		# If there were no frames in the dataset frames folder, then we need to generate the frames for this dataset.
		if len(dataset_frames_folder_files) <= 0:
			generate_frames(dataset_data)

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

	# Set the initial dataset key to the first of the dataset_filepath keys list.
	global_dataset_key = StringVar(value=list(dataset_filepath_to_frames_map.keys())[0])
	# Call dataset_changed whenever global_dataset_key is written to.
	global_dataset_key.trace('w', dataset_changed)

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

	juxtaposition_frame_amount_spin_box = Spinbox(controls_frame, width=spinbox_width, from_=1, to=len(current_dataset_frames()), textvariable=global_frames_to_render, command=spinbox_changed)
	juxtaposition_frame_amount_spin_box.grid(row=0, column=increment_column())

	juxtaposition_frame_increment_label = Label(controls_frame, text ="Frame Cycle Amount: ", font = "50")
	juxtaposition_frame_increment_label.grid(row=0, column=increment_column())

	juxtaposition_increment_frames_spin_box = Spinbox(controls_frame, width=spinbox_width, from_=1, to=len(current_dataset_frames()), textvariable=global_increment_frames, command=spinbox_changed)
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

	dataset_combo_box_label = Label(controls_frame, text ="Dataset: ", font = "50")
	dataset_combo_box_label.grid(row=0, column=increment_column())

	dataset_combo_box = Combobox(controls_frame, width=50, textvariable=global_dataset_key)
	dataset_combo_box['values'] = tuple(dataset_filepath_to_frames_map.keys())
	dataset_combo_box.grid(row=0, column=increment_column())
	#
	#
	#

	canvas = create_canvas(window, 1920, 1080)

	# Start juxtaposition loop.
	juxtapose_next_global(window, canvas)

	window.mainloop()

if __name__ == "__main__":
	main()