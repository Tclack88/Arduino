import smbus
import subprocess
import time


bus = smbus.SMBus(1)

#I2C address of connected device
i2c_address = 0x77
i2c_cmd = 0x66

message = subprocess.check_output('curl -4 ifconfig.me', shell=True).strip()

print(f'message: {message}')

#bytes_message = message.encode('utf-8')
#bytes_message = bytearray(message,'utf-8')
bytes_message = [c for c in message]
print(bytes_message)

while(1):
    bus.write_i2c_block_data(i2c_address, 0x0, bytes_message) 
    time.sleep(3)
