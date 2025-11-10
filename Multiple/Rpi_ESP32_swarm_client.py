# UDP connection with ESP32 as server interacting with Rpi (client). Used in conjunction with Rpi_ESP32_UDP_transmit_server.ino
import multiprocessing as mp
from math import floor
import RPi.GPIO as GPIO
import socket
import subprocess
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
ID = mp.Value('i',0)
val = mp.Value('d',0)

manager = mp.Manager()
esp_list = manager.list() # allow list to be accesible by parent and separate process
ESP_port = 12005

highest_voltage = 0
blink_timer = time.time()*1000

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
            time.sleep(.3)
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

LED_process = mp.Process(target=light_LED, args=(ID,val,))
button_process = mp.Process(target=check_button_press)
blink_process = mp.Process(target=blink_white, args=(STATE,))
update_esp_process = mp.Process(target=update_esps,)

LED_process.start()
button_process.start()
blink_process.start()
update_esp_process.start()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP
server_socket.settimeout(10.0)

def send_message(cmd):
    # send 'C' (continue/commence) or 'E' (end), followed by number of
    # ESP32 IP adresses followed by each ip address
    esps = ' '.join(sorted(esp_list))  # append cmd "C"/"E" and ESP list
    message = cmd + f" {len(esp_list)}  " + esps
    for ESP_ip in esp_list:
        server_socket.sendto(message.encode('utf-8'), (ESP_ip, ESP_port) )

while True:
    while STATE.value == 0 or STATE.value == 2:
        time.sleep(.1) # idle or error, stay here
    send_message('C') # 'C': continue/commence. leaving idle, send message to ESP32 to initiate UDP
    while (STATE.value == 1): #receiving UDP messages
        send_message('C') # 'C': continue/commence. leaving idle, send message to ESP32 to initiate UDP
        try:
            resp_message, addr = server_socket.recvfrom(1024)
            str_id, str_val = (resp_message.decode('utf-8')).split() 
            ID.value = int(str_id)
            val.value = float(str_val)
            if val.value < 0: # -1 received back to indicate/confirm END
                print("END")

        except Exception as e:
            STATE.value = 2
            ID.value = 5
            send_message('E') # send cancel to ESP32 because error
            print(f"FAILURE: {e}")

        if STATE.value == 0:
            send_message('E') # tell ESP32 to stop sending data
            ID.value = 5
