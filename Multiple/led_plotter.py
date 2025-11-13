import random
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
import time


maxt = 30 # maximum show 30 samples

random.seed(5)
colormap =  {1:'r',2:'y',3:'g'}

cmap = ListedColormap(['r','y','g'])
norm = BoundaryNorm([0.5, 1.5, 2.5, 3.5], cmap.N)

#vals = [round(random.random()*3.3,2) for _ in range(30)]
#x_range = range(30)
#colors = [random.choice([1,2,3]) for _ in range(30)]


class Plotter(object):
	def __init__(self, ax, maxt=30, dt=0.1):
		self.ax = ax
		self.dt = dt
		self.maxt = maxt
		self.time = 0
		self.tdata = np.array([])
		self.ydata = np.array([])
		self.cdata = np.array([])
		self.line = Line2D(self.tdata,self.ydata)
		self.line.set_marker("o")
		self.ax.add_line(self.line)
		self.ax.set_xlim(0,maxt)
		self.ax.set_ylim(0,3.3)
		# line coloring: 
		self.line_collection = LineCollection([], cmap=cmap, norm=norm)
		self.ax.add_collection(self.line_collection)

	def update(self, data):
		# step1: Animate (and save the data)
		t, y, c = data # time, value (voltage), color
		self.tdata = np.append(self.tdata, t)
		self.ydata = np.append(self.ydata, y)
		self.cdata = np.append(self.cdata, c)
		self.ydata = self.ydata[self.tdata > (t - self.maxt) ] # lessons learned; order is important! reducing t before y messes it up
		self.cdata = self.cdata[self.tdata > (t - self.maxt) ]
		self.tdata = self.tdata[self.tdata > (t - self.maxt) ]
		self.ax.set_xlim(self.tdata[0],self.tdata[0]+self.maxt) # scrolling
		self.line.set_data(self.tdata,self.ydata)
		# step2: change the colors:
		#self.line.set_markerfacecolor(colormap[c]) # This doesn't work, it changes all colors every line
		#self.line.set_color(colormap[c]) # same issue as above, but includes the lines
	
		return self.line,
	
	def generator(self):
		while True:
			time.sleep(self.dt)
			self.time += 1
			val = round(random.random()*3.3,2)
			color = random.choice([1,2,3])
			yield self.time, val, color


if __name__ == '__main__':
	dt = 0.05 # probably unnecessary as it will just change from the generator
	fig, ax = plt.subplots()

	plotter = Plotter(ax, maxt=maxt, dt=dt)
	ani = animation.FuncAnimation(fig, plotter.update, plotter.generator, interval=dt*1002., blit=True)

	#plt.figure()
	ax.set_xticks([])
	ax.set_xticklabels([])
	plt.show()

input("press <ENTER> to exit")
