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
colormap =  {1:'#F74B31',2:'#FAFC4C',3:'#27F549'}

ryg = ['#F74B31','#FAFC4C','#27F549']
cmap = ListedColormap(ryg)
norm = BoundaryNorm([0.5, 1.5, 2.5, 3.5], cmap.N)

#vals = [round(random.random()*3.3,2) for _ in range(30)]
#x_range = range(30)
#colors = [random.choice([1,2,3]) for _ in range(30)]


class Plotter(object):
	def __init__(self, ax1, ax2, maxt=30, dt=0.1):
		self.ax1 = ax1
		self.ax2 = ax2
		self.dt = dt
		self.maxt = maxt
		self.time = 0
		self.tdata = np.array([])
		self.ydata = np.array([])
		self.cdata = np.array([])
		self.line = Line2D(self.tdata,self.ydata)
		self.line.set_marker("o")
		self.ax1.add_line(self.line)
		self.ax1.set_xlim(0,maxt)
		self.ax1.set_ylim(0,3.3)
		# ax1 line coloring: 
		self.line_collection = LineCollection([], cmap=cmap, norm=norm)
		self.ax1.add_collection(self.line_collection)
		# ax2 point coloring:
		self.scatter = self.ax1.scatter(self.tdata,self.ydata,s=60,zorder=10) # higher zorder places this on TOP!

	def update(self, data):
		# step1: Animate (and save the data)
		t, y, c = data # time, value (voltage), color
		self.tdata = np.append(self.tdata, t)
		self.ydata = np.append(self.ydata, y)
		self.cdata = np.append(self.cdata, c)
		self.ydata = self.ydata[self.tdata > (t - self.maxt) ] # lessons learned; order is important! reducing t before y messes it up
		self.cdata = self.cdata[self.tdata > (t - self.maxt) ]
		self.tdata = self.tdata[self.tdata > (t - self.maxt) ]
		self.ax1.set_xlim(self.tdata[0],self.tdata[0]+self.maxt) # scrolling
		self.line.set_data(self.tdata,self.ydata)
		# step2: change the colors:
		#self.line.set_markerfacecolor(colormap[c]) # This doesn't work, it changes all colors every line
		#self.line.set_color(colormap[c]) # same issue as above, but includes the lines
		if len(self.tdata > 1):
			left_points = np.asarray(list(zip(self.tdata[:-1],self.ydata[:-1]))).reshape(-1,1,2)
			#print(left_points)
			right_points = np.asarray(list(zip(self.tdata[1:],self.ydata[1:]))).reshape(-1,1,2)
			#print(right_points)
			#segments = np.vstack([left_points,right_points]).T.reshape(-1,1,2)
			#print(segments)
			#print()
			segments = np.concatenate([left_points,right_points],axis=1)
			#print(segments)
			self.line_collection.set_segments(segments)
			self.line_collection.set_array(self.cdata[1:])
			self.line_collection.set_linewidth(2)

		self.scatter.set_offsets(np.vstack([self.tdata,self.ydata]).T)
		self.scatter.set_facecolors([colormap[c] for c in self.cdata])

		# bar chart
		self.ax2.cla()
		self.ax2.bar([1,2,3],[np.count_nonzero(self.cdata==1),
				np.count_nonzero(self.cdata==2),
				np.count_nonzero(self.cdata==3)],
				color=ryg)

		self.ax2.set_xticks([1,2,3])
		self.ax2.set_xticklabels(['red','yellow','green'])
		self.ax2.set_ylabel("counts (of last 30)")

		return self.line, self.scatter
	
	def generator(self):
		while True:
			time.sleep(self.dt)
			self.time += 1
			val = round(random.random()*3.3,2)
			color = random.choice([1,2,3])
			yield self.time, val, color


if __name__ == '__main__':
	dt = 0.05 # probably unnecessary as it will just change from the generator
	fig, (ax1, ax2) = plt.subplots(nrows=2,ncols=1)
	plt.style.use("bmh")
	plotter = Plotter(ax1, ax2, maxt=maxt, dt=dt)
	ani = animation.FuncAnimation(fig, plotter.update, plotter.generator, interval=dt, blit=False)

	ax1.set_xticks([])
	ax1.set_xticklabels([])
	ax1.set_ylabel("voltage measured (V)")
	plt.show()

input("press <ENTER> to exit")
