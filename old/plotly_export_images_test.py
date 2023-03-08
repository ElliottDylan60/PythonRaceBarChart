# import bar_chart_race as bcr
# import pandas as pd
# from tkinter import *
# from tkinterhtml import HtmlFrame
import io
import pandas as pd
from raceplotly.plots import barplot
import gif
import PIL

df = pd.read_csv('https://raw.githubusercontent.com/lc5415/raceplotly/main/example/dataset/FAOSTAT_data.csv')

# @gif.frame
# def plot(i):
# 	# d = df[df['year'] == i]
# 	# d = df[df['Year'] == i + 1961]
# 	d = df[df['Year'] == str(i + 1961)]
# 	print(str(d))
# 	my_raceplot = barplot(d,  item_column='Item', value_column='Value', time_column='Year')
# 	my_raceplot_plot = my_raceplot.plot(item_label = 'Top 10 crops', value_label = 'Production quantity (tonnes)', frame_duration = 800)
# 	return my_raceplot_plot

# Construct list of frames
# frames = []
# for i in range(10):
#     frame = plot(i)
#     frames.append(frame)

# Save gif from frames with a specific duration for each frame in ms
# gif.save(frames, 'example.gif', duration=100)

# my_raceplot = barplot(data,  item_column='Item', value_column='Value', time_column='Year')
# my_raceplot_plot = my_raceplot.plot(item_label = 'Top 10 crops', value_label = 'Production quantity (tonnes)', frame_duration = 800)
# my_raceplot_plot.show()

my_raceplot = barplot(df,  item_column='Item', value_column='Value', time_column='Year')
my_raceplot_plot = my_raceplot.plot(item_label = 'Top 10 crops', value_label = 'Production quantity (tonnes)', frame_duration = 1)

print("Frames: " + str(len(my_raceplot_plot.frames)))

# generate images for each step in animation
frames = []
for s, fr in enumerate(my_raceplot_plot.frames):
    # set main traces to appropriate traces within plotly frame
    my_raceplot_plot.update(data=fr.data)
    # move slider to correct place
    my_raceplot_plot.layout.sliders[0].update(active=s)
    # generate image of current state
    frames.append(PIL.Image.open(io.BytesIO(my_raceplot_plot.to_image(format="png"))))
    # frames.append(my_raceplot_plot.to_image(format="png"))

# print(str(frames))

# create animated GIF
frames[0].save(
        "test.gif",
        save_all=True,
        append_images=frames[1:],
        optimize=True,
        duration=500,
        loop=0,
    )

# my_raceplot_plot.show()