# UDP connection with ESP32 as server interacting with Rpi (client). Used in conjunction with Rpi_ESP32_UDP_transmit_server.ino
import multiprocessing as mp
from math import floor
import RPi.GPIO as GPIO
import socket
import time

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

button_process = mp.Process(target=check_button_press)
blink_process = mp.Process(target=blink_white, args=(STATE,))
button_process.start()
blink_process.start()


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

ESP_ip = '192.168.1.108' # changes
#ESP_ip = '192.168.43.199' # changes
ESP_port = 12005

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP
server_socket.settimeout(10.0)

def send_message():
    message = time.ctime() # simple date stamp for time of request
    server_socket.sendto(message.encode('utf-8'), (ESP_ip, ESP_port) )

while True:
    while STATE.value == 0 or STATE.value == 2:
        time.sleep(.1) # idle or error, stay here
    send_message() # leaving idle, send message to ESP32 to initiate UDP
    while (STATE.value == 1): #receiving UDP messages
        try:
            resp_message, addr = server_socket.recvfrom(1024)
            val = float(resp_message.decode('utf-8'))
            if val < 0: # -1 received back to indicate/confirm END
                print("END")
                light_LED(5) #5 is outside range of 0-3, so it will turn off
            else:
                print(f"sucessful receipt of message from {addr[0]}. message: {resp_message} (type:{type(resp_message)})")
                light_LED(val)

        except Exception as e:
            STATE.value = 2
            light_LED(5) # turn off RGB LEDs
            send_message() # send cancel to ESP32 because error
            print(f"FAILURE: {e}")

        if STATE.value == 0:
            light_LED(5) # turn of RGB LEDs
            send_message() # tell ESP32 to stop sending data

