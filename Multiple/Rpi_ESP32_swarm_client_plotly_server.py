# UDP connection with ESP32 as server interacting with Rpi (client). Used in conjunction with Rpi_ESP32_UDP_transmit_server.ino
import multiprocessing as mp
from math import floor
import RPi.GPIO as GPIO
import socket
import subprocess
import time
import random
import threading
import plotly_app 

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
dt = 30

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
matrix_data = manager.list() # hold values for the stupid LED matrix

web_data = manager.list()
web_state = manager.dict({'running':False,'status':'Ready'})

plotly_app.data_buffer = web_data
plotly_app.system_state = web_state

ESP_port = 12005
highest_voltage = 0
blink_timer = time.time()*1000


colormap =  {1:'#F74B31',2:'#FAFC4C',3:'#27F549'}

## Plotting stuff ends #######################################################

### helper functions #####
def save_data():
    # save data and reset isp list if no longer sending
    timestamp = '_'.join(time.ctime().split(' '))
    sums = {1:0,2:0,3:0}
    for esp, volt, duration in data:
       sums[esp] += duration 
    with open(f'./log/data_{timestamp}','w') as f:
        if resp_ips.get(1,0):
            f.write(f"\n\t\t (1) red ({resp_ips[1]}):\t {sums[1]} s\n")
        if resp_ips.get(2,0):
            f.write(f"\n\t\t (2) yellow ({resp_ips[2]}):\t {sums[2]} s\n")
        if resp_ips.get(3,0):
            f.write(f"\n\t\t (3) greeen ({resp_ips[3]}):\t {sums[3]} s\n")
        f.write("\n\nraw:" + ','.join([str(dat) for dat in data])+"\n")
    for k in resp_ips.keys(): # dynamically remove any ESP that left network
        if k not in esp_list:
            resp_ips.pop(k)

def cast(voltage): # for led matrix_data, cast to binary string
    val = round(voltage*8/3.3)
    bin_string = ('1'*val).ljust(8,'0')
    return bin_string

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
                web_state['running'] = True
                web_state['status'] = 'Recording Data'
            elif STATE.value == 1:
                STATE.value = 0
                web_state['running'] = False
                web_state['status'] = 'Stopped'
            elif STATE.value == 2:
                STATE.value = 0
                web_state['running'] = False
                web_state['status'] = 'Stopped'
        time.sleep(.2)
    else:
        time.sleep(.1)

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
    count = 0
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
                    current_time = time.time() - starttime
                    data.append((ID.value,val.value,current_time))
                    # append data for plotly
                    web_data.append({'timestamp': starttime+current_time, 'id':ID.value, 'value':val.value,'ip':addr[0]})
                    if len(web_data) > dt:
                        web_data[:] = web_data[-dt:]

                    count += 1
                    if count%4 == 0:
                        last4 = data[-1][1]+data[-2][1]+data[-2][1]+data[-3][1]
                        if len(matrix_data) >= 8:
                            matrix_data.pop(0)
                        matrix_data.append(cast(last4/4))
                    starttime = time.time()

            except Exception as e:
                STATE.value = 2
                ID.value = 5
                send_message('E') # send cancel to ESP32 because error
                print(f"FAILURE: {e}")
                save_data()
                web_state['running'] = False
                web_state['status'] = 'Error'

            if STATE.value == 0:
                send_message('E') # tell ESP32 to stop sending data
                ID.value = 5
                save_data()
                web_state['running'] = False
                web_state['status'] = 'Stopped'

def led_matrix():
    from luma.led_matrix.device import max7219
    from luma.core.interface.serial import spi,noop
    from luma.core.render import canvas
    serial = spi(port=0, device=0, gpio=noop())
    device = max7219(serial,width=8,height=8)

    def set_rows():
        with canvas(device) as draw:
            for row, binary in enumerate(matrix_data):
                for col, bit in enumerate(binary):
                    if bit == '1':
                        draw.point((col, row), fill='white')
    while True:
        set_rows()
        time.sleep(.5)

##### START ###########
LED_process = mp.Process(target=light_LED, args=(ID,val,))
button_process = mp.Process(target=check_button_press)
blink_process = mp.Process(target=blink_white, args=(STATE,))
update_esp_process = mp.Process(target=update_esps,)
network_receiver_process = mp.Process(target=network_receiver,
                                      args=(STATE,ID,val,esp_list))
matrix_process = mp.Process(target=led_matrix)

LED_process.start()
button_process.start()
blink_process.start()
update_esp_process.start()
network_receiver_process.start()
matrix_process.start()

server_thread = threading.Thread(
        target=plotly_app.run_server, 
        kwargs={'host':'0.0.0.0','port':8050,'debug':False},
        daemon=True
        )
server_thread.start()

try:
    while True:
        time.sleep(1) # keep server_thread alive
except KeyboardInterrupt:
    GPIO.cleanup()
    print("stopped")
