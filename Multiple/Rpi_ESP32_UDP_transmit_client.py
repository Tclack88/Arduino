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
receiving = 0 # 0 or 1. keep track if pressed or not
blinking = mp.Value('b',0) # boolean for white LED blinking error

GPIO.cleanup() # reset any pins (eg turn of LEDs from previous errors)
GPIO.setmode(GPIO.BCM)
GPIO.setup(button,GPIO.IN) # input pin for detecting button press
GPIO.setup(white,GPIO.OUT)
GPIO.setup(red,GPIO.OUT) 
GPIO.setup(yellow,GPIO.OUT)
GPIO.setup(green,GPIO.OUT)


"""
# TEST for button and lights
count = 0
print("starting")
while count < 10:
    if GPIO.input(button) != 0:
        count += 1
        if count == 2:
            GPIO.output(white,True)
        if count == 3:
            GPIO.output(red,True)
        if count == 6:
            GPIO.output(yellow,True)
        if count == 9:
            GPIO.output(green,True)
        time.sleep(0.3)
        print(GPIO.input(button),count)

print("finishing")
GPIO.cleanup()
"""
def blink_white(blinking):
    while True:
        print(blinking.value)
        if blinking.value:
            if GPIO.input(button) != 0:
                blinking.value = 0
                print("breaking out of blinking")
        GPIO.output(white,True)
        time.sleep(.5)
        GPIO.output(white,False)
        time.sleep(.5)

    else:
        time.sleep(.1)

blink_process = mp.Process(target=blink_white, args=(blinking,))
blink_process.start()


def light_LED(val):
    GPIO.output(red,False)
    GPIO.output(yellow,False)
    GPIO.output(green,False)
    if floor(val) == 3:
        GPIO.output(green,True)
    elif floor(val) == 2:
        GPIO.output(yellow,True)
    else:
        GPIO.output(red,True)

ESP_ip = '192.168.1.108' # changes
#ESP_ip = '192.168.43.199' # changes
ESP_port = 12005

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP
server_socket.settimeout(10.0)

while True:
    if receiving == 0 and blinking.value == 0: # "off" not primed to receive
        while GPIO.input(button) == 0:
            GPIO.output(white,receiving)
            time.sleep(.1)
    time.sleep(.3)
    receiving = 1
    GPIO.output(white,receiving)
   
    message = time.ctime() # simple date stamp for time of request
    server_socket.sendto(message.encode('utf-8'), (ESP_ip, ESP_port) )
    while (receiving):
        receiving = (receiving + GPIO.input(button)) % 2 #check for button press to cancel after loop ends
        GPIO.output(white,receiving)
        if not receiving:
            receiving = 0
            break
        print(f"receiving: {receiving}")
        try:
            resp_message, addr = server_socket.recvfrom(1024)
            val = float(resp_message.decode('utf-8'))
            if val < 0:
                print("END")
                receiving = 0 
                print(f"receiving: {receiving}")
            else:
                print(f"sucessful receipt of message from {addr[0]}. message: {resp_message} (type:{type(resp_message)})")
                light_LED(val)

        except Exception as e:
            blinking.value = 1
            receiving = 0
            print(f"FAILURE: {e}")
