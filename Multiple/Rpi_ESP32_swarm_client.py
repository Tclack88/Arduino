# UDP connection with ESP32 as server interacting with Rpi (client). Used in conjunction with Rpi_ESP32_UDP_transmit_server.ino
import multiprocessing as mp
from math import floor
import RPi.GPIO as GPIO
import socket
import subprocess
import time
import random
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
import time

ip_cmd = "hostname -I | awk '{print $1}'"
myIP = (subprocess.check_output(ip_cmd,shell=True)).decode().strip() # used to find cidr_block
cidr_block = '.'.join(myIP.split('.')[:3])+'.0/24' # subnet for NMAP (no more hardcoding IPs)
print(f"my IP: {myIP}")
print(f"cidr block: {cidr_block}")

button = 16
red = 5
yellow = 6
green = 13
white = 12

GPIO.cleanup() # reset any pins (eg turn of LEDs from previous errors)
GPIO.setmode(GPIO.BCM)
GPIO.setup(button,GPIO.IN) # input pin for detecting button press
GPIO.setup(white,GPIO.OUT)
GPIO.setup(red,GPIO.OUT) 
GPIO.setup(yellow,GPIO.OUT)
GPIO.setup(green,GPIO.OUT)


STATE = mp.Value('i',0)
press = mp.Value('b',GPIO.input(button))
ID = mp.Value('i',0) # start red just to avoid '0' as non-existant value
val = mp.Value('d',0.0)

manager = mp.Manager()
esp_list = manager.list() # allow list to be accesible by parent and separate process
resp_ips = manager.dict() # ip addresses from responses (for logging)
data = manager.list() # hold all data collected since last button press
ESP_port = 12005

highest_voltage = 0
blink_timer = time.time()*1000


## Plotting stuff starts #####################################################
maxt = 30 # maximum show 30 samples

colormap =  {1:'#F74B31',2:'#FAFC4C',3:'#27F549'}
ryg = ['#F74B31','#FAFC4C','#27F549']
cmap = ListedColormap(ryg)
norm = BoundaryNorm([0.5, 1.5, 2.5, 3.5], cmap.N)

class Plotter(object):
    def __init__(self, ax1, ax2, STATE, ID , val, maxt=30, dt=1):
        self.ax1 = ax1
        self.ax2 = ax2
        self.maxt = maxt
        self.dt = dt
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
        self.STATE = STATE
        self.ID = ID
        self.val = val

    def update(self, dat):
        if dat is None:
            return self.line, self.scatter
        # step1: Animate (and save the data)
        t, y, c = dat # time, value (voltage), color
        self.tdata = np.append(self.tdata, t)
        self.ydata = np.append(self.ydata, y)
        self.cdata = np.append(self.cdata, c)
        self.ydata = self.ydata[self.tdata > (t - self.maxt) ] # lessons learned; order is important! reducing t before y messes it up
        self.cdata = self.cdata[self.tdata > (t - self.maxt) ]
        self.tdata = self.tdata[self.tdata > (t - self.maxt) ]
        self.ax1.set_xlim(self.tdata[0],self.tdata[0]+self.maxt) # scrolling
        self.line.set_data(self.tdata,self.ydata)
        self.line.set_markerfacecolor('w') # blue default coloring for
        self.line.set_markeredgecolor('w') # "empty" receives, change to white
        # step2: change the colors:
        #self.line.set_markerfacecolor(colormap[c]) # This doesn't work, it changes all colors every line
        #self.line.set_color(colormap[c]) # same issue as above, but includes the lines
        if len(self.tdata > 1):
            left_points = np.asarray(list(zip(self.tdata[:-1],self.ydata[:-1]))).reshape(-1,1,2)
            right_points = np.asarray(list(zip(self.tdata[1:],self.ydata[1:]))).reshape(-1,1,2)
            #print(left_points)
            #print(right_points)
            #segments = np.vstack([left_points,right_points]).T.reshape(-1,1,2)
            #print(segments)
            #print()
            segments = np.concatenate([left_points,right_points],axis=1)
            self.line_collection.set_segments(segments)
            self.line_collection.set_array(self.cdata[1:])
            self.line_collection.set_linewidth(2)

        self.scatter.set_offsets(np.vstack([self.tdata,self.ydata]).T)
        self.scatter.set_facecolors([colormap.get(c,"none") for c in self.cdata])

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
            if self.STATE.value == 1:
                time.sleep(self.dt) # necessary?
                #time.sleep(1)
                self.time += 1
                current_val = self.val.value#*3.3/4095
                current_ID = self.ID.value
                yield self.time, current_val, current_ID

            else:
                time.sleep(.1) # neccessary?
                yield None
            #time.sleep(self.dt) # necessary?

## Plotting stuff ends #######################################################

### helper functions #####

def save_data():
    timestamp = '_'.join(time.ctime().split(' '))
    sums = {1:0,2:0,3:0}
    for esp, volt, duration in data:
       sums[esp] += duration 
    with open(f'./log/data_{timestamp}','w') as f:
        f.write(f"\n\t\t (1) red ({resp_ips.get(1,'N/A')}):\t {sums[1]} s\n \
                (2) yellow ({resp_ips.get(2,'N/A')}):\t  {sums[2]} s\n \
                (3) green ({resp_ips.get(3,'N/A')}):\t  {sums[3]} s\n\nraw:\n")
        f.write(','.join([str(dat) for dat in data])+"\n")

##### multiprocess functions ######
def light_LED(ID, val):
    global highest_voltage
    global blink_timer
    # toggles RGB light of ID. Any value outside
    # (eg. 5) will just turn all off
    while True:
        if val.value > highest_voltage:
            highest_voltage = val.value # keep track for blink rate
        now = time.time()*1000
        IDs = {1:red,2:yellow,3:green}
        remaining_IDS = [1,2,3] 
        if ID.value in remaining_IDS:
            # strategy: toggle then remove the ID of transmitting ESP
            # then all others get turned off
            remaining_IDS.remove(ID.value)
            if ( (now - blink_timer) >= 500*(highest_voltage - val.value) ): # *500 to approximate blink rate on ESP32
                GPIO.output(IDs[ID.value], not GPIO.input(IDs[ID.value])) # toggle
                blink_timer = now # reset blink timer
        for rID in remaining_IDS:
            GPIO.output(IDs[rID],False)

def check_button_press():
    # state 0: nothing. 1: receiving data. 2: error
    global STATE
    while True:
        press = GPIO.input(button)
        if press:
            if STATE.value == 0:
                STATE.value = 1
            elif STATE.value == 1:
                STATE.value = 0
            elif STATE.value == 2:
                STATE.value = 0
        time.sleep(.2)
    else:
        time.sleep(.1)

"""
# attempt to make more robust
def check_button_press(channel):
    # state 0: nothing. 1: receiving data. 2: error
    global STATE
    if STATE.value == 0:
        STATE.value = 1
    elif STATE.value == 1:
        STATE.value = 0
    elif STATE.value == 2:
        STATE.value = 0

GPIO.add_event_detect(button, GPIO.RISING, callback=check_button_press, bouncetime=100)

try: 
    GPIO.add_event_detect(button, GPIO.RISING, callback=check_button_press, bouncetime=100)
    print("successful event_detect")
except Exception as e:
    print(f"another error: {e}")
"""

def blink_white(STATE):
    # Controls the white pin. This definition is the process control.
    # Blinks for errors. Solid if transmitting/receiving. Off if idle
    while True:
        if STATE.value == 2:
            GPIO.output(white,True)
            time.sleep(.5)
            GPIO.output(white,False)
            time.sleep(.5)
        elif STATE.value == 1:
            GPIO.output(white,True)
        else:
            GPIO.output(white,False)

def update_esps():
    while True: # System call to nmap to find/update all ESP32s in network
        try:
            command = f"nmap -sn {cidr_block} | grep esp32 | grep -E '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' -o"
            res = (subprocess.check_output(command,shell=True)).decode().strip()
            ESP32s = res.split('\n')
            esp_list[:] = ESP32s
            time.sleep(1)
            print(ESP32s)
        except Exception as e:
            print(f"failure in updating ESP list - {e}")

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP
server_socket.settimeout(10.0)

def send_message(cmd):
    # send 'C' (continue/commence) or 'E' (end), followed by number of
    # ESP32 IP adresses followed by each ip address
    esps = ' '.join(sorted(esp_list))  # append cmd "C"/"E" and ESP list
    message = cmd + f" {len(esp_list)}  " + esps
    for ESP_ip in esp_list:
        server_socket.sendto(message.encode('utf-8'), (ESP_ip, ESP_port) )

def network_receiver(STATE, ID, val, esp_list):
    while True:
        while STATE.value == 0 or STATE.value == 2:
            time.sleep(.1) # idle or error, stay here
        starttime = time.time() # start time for current gathering
        data[:] = [] # refresh data
        send_message('C') # 'C': continue/commence. leaving idle, send message to ESP32 to initiate UDP
        while (STATE.value == 1): #receiving UDP messages
            send_message('C') # 'C': continue/commence. leaving idle, send message to ESP32 to initiate UDP
            try:
                resp_message, addr = server_socket.recvfrom(1024)
                str_id, str_val = (resp_message.decode('utf-8')).split() 
                ID.value = int(str_id)
                val.value = float(str_val)
                resp_ips[ID.value] = addr[0]
                if val.value < 0: # -1 received back to indicate/confirm END
                    print("END")
                    save_data()
                else:
                    data.append((ID.value,val.value,time.time() - starttime))
                    starttime = time.time()

            except Exception as e:
                STATE.value = 2
                ID.value = 5
                send_message('E') # send cancel to ESP32 because error
                print(f"FAILURE: {e}")
                save_data()

            if STATE.value == 0:
                send_message('E') # tell ESP32 to stop sending data
                ID.value = 5
                save_data()

##### START ###########
LED_process = mp.Process(target=light_LED, args=(ID,val,))
button_process = mp.Process(target=check_button_press)
blink_process = mp.Process(target=blink_white, args=(STATE,))
update_esp_process = mp.Process(target=update_esps,)
network_receiver_process = mp.Process(target=network_receiver,
                                      args=(STATE,ID,val,esp_list))

LED_process.start()
button_process.start()
blink_process.start()
update_esp_process.start()

#network_receiver_process.daemon = True
network_receiver_process.start()


dt = 1 # probably unnecessary as it will just change from the generator
fig, (ax1, ax2) = plt.subplots(nrows=2,ncols=1)
plt.style.use("bmh")
plotter = Plotter(ax1, ax2, STATE=STATE, ID=ID, val=val, maxt=maxt, dt=dt)
ani = animation.FuncAnimation(fig, plotter.update, plotter.generator, blit=False)

ax1.set_xticks([])
ax1.set_xticklabels([])
ax1.set_ylabel("voltage measured (V)")
plt.show()
