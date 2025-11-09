# UDP connection with ESP32 as server interacting with Rpi (client). Used in conjunction with Rpi_ESP32_UDP_transmit_server.ino
import multiprocessing as mp
from math import floor
import RPi.GPIO as GPIO
import socket
import subprocess
import time

ip_cmd = "hostname -I | awk '{print $1}'"
myIP = (subprocess.check_output(ip_cmd,shell=True)).decode().strip()
cidr_block = '.'.join(myIP.split('.')[:3])+'.0/24'
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


"""
def light_LED(val):
    # changes the RGB lights. Any value outside
    # (eg. 5) will just turn all off
    GPIO.output(red,False)
    GPIO.output(yellow,False)
    GPIO.output(green,False)
    if floor(val) == 3:
        GPIO.output(green,True)
    elif floor(val) == 2:
        GPIO.output(yellow,True)
    elif floor(val) == 1:
        GPIO.output(red,True)
"""
#Testing, for maybe toggling led according to value read
highest_voltage = 0
blink_timer = time.time()*1000
# Also must change all light_LED to include ID,val as args (or like 5,0 for the endings). Problem with this approach now is the every 1 second sending time  from the ESP32 side
def light_LED(ID, val):
    global highest_voltage
    global blink_timer
    # toggles RGB light of ID. Any value outside
    # (eg. 5) will just turn all off
    while True:
        if val.value > highest_voltage:
            highest_voltage = val.value
        now = time.time()*1000
        IDs = {1:red,2:yellow,3:green}
        remaining_IDS = [1,2,3]
        #print(f"\tID: {ID.value}\t remaining: {remaining_IDS}")
        if ID.value in remaining_IDS:
            print(f"\t id is in ids\tnow: {now}\tblink_timer: {blink_timer} (diff={now-blink_timer}")
            remaining_IDS.remove(ID.value)
            if ( (now - blink_timer) >= 100*(highest_voltage - val.value) ):
                print(f"changing color {IDs[ID.value]} to {not GPIO.input(IDs[ID.value])}")
                GPIO.output(IDs[ID.value], not GPIO.input(IDs[ID.value])) # toggle
                blink_timer = now
        for rID in remaining_IDS:
            GPIO.output(IDs[rID],False)

def check_button_press():
    # state 0: nothing. 1: receiving data. 2: error
    global STATE
    while True:
        press = GPIO.input(button)
        if press:
            #print("button pressed, toggling state")
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
    # now misnomer. Controls the white pin. This definition is the
    # process control. Blinks for errors. Solid if receiving from UDP
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
    #global esp_list
    while True:
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


#ESP_ip = '192.168.1.108' # changes
#ESP_ip = '192.168.43.199' # changes

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP
server_socket.settimeout(10.0)

def send_message(cmd):
    # send 'C' (continue/commence) or 'E' (end), followed by number of
    # ESP32 IP adresses followed by each ip address
    esps = ' '.join(sorted(esp_list))  # append cmd "C"/"E" and ESP list
    message = cmd + f" {len(esp_list)}  " + esps
    #print("temp debug:", message)
    #print(f"esps: {esp_list}")
    for ESP_ip in esp_list:
        #print(f"sending message: {message} to esp {ESP_ip}")
        server_socket.sendto(message.encode('utf-8'), (ESP_ip, ESP_port) )

while True:
    #print(STATE)
    while STATE.value == 0 or STATE.value == 2:
        time.sleep(.1) # idle or error, stay here
    send_message('C') # 'C': continue/commence. leaving idle, send message to ESP32 to initiate UDP
    while (STATE.value == 1): #receiving UDP messages
        send_message('C') # 'C': continue/commence. leaving idle, send message to ESP32 to initiate UDP
        try:
            resp_message, addr = server_socket.recvfrom(1024)
            print(f"debug: resp_message = {resp_message.decode('utf-8')}")
            str_id, str_val = (resp_message.decode('utf-8')).split() # TODO: ID correspond to R,G,B. Do on ESP32 side also # TODO: ID correspond to R,G,B. Do on ESP32 side also
            ID.value = int(str_id)
            val.value = float(str_val)
            if val.value < 0: # -1 received back to indicate/confirm END
                print("END")
                #light_LED(5) #5 is outside range of 0-3, so it will turn off
            #else:
            #    #print(f"sucessful receipt of message from {addr[0]}. message: {resp_message} (type:{type(resp_message)})")
            #    #light_LED(ID) # 1 lights red, 2 - yellow, 3 - greean, else off

        except Exception as e:
            STATE.value = 2
            ID.value = 5
            #light_LED(5) # turn off RGB LEDs
            send_message('E') # send cancel to ESP32 because error
            print(f"FAILURE: {e}")

        if STATE.value == 0:
            send_message('E') # tell ESP32 to stop sending data
            ID.value = 5
            #light_LED(5) # turn of RGB LEDs
