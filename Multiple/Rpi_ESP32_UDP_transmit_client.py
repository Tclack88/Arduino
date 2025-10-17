# UDP connection with ESP32 as server interacting with Rpi (client). Used in conjunction with Rpi_ESP32_UDP_transmit_server.ino
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
ESP_port = 12005

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP

while True:
    #message = input()
    while GPIO.input(button) == 0:
        time.sleep(.1)
    message = "button pressed!"
    #server_socket.bind( (ESP_ip, port) ) # bind() used for specified port. sendto() will work and an "ephemeral" port would be created
    #server_socket.connect( (ESP_ip, ESP_port) )
    
    server_socket.sendto(message.encode('utf-8'), (ESP_ip, ESP_port) )
    try:
        resp_message, addr = server_socket.recvfrom(1024)
        val = float(resp_message.decode('utf-8'))
        print(f"sucessful receipt of message from {addr[0]}. message: {resp_message} (type:{type(resp_message)})")
        light_LED(val)
        #data = s.recv(1024)
        #print(f"sucessful receipt of message: {data.decode('utf-8')}")
        #server_socket.close()

    except Exception as e:
        print(f"FAILURE: {e}")
