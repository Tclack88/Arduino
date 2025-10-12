# Collects acceleration and gyroscope acceleration data (from mpu6050 module) 
# for time specified and saves each collection to a specified csv
from mpu6050 import mpu6050 # pip install mpu6050-raspberrypi
import time

mpu = mpu6050(0x68) # default address of module (verify with `i2cdetect -y 1` from command line. apt install i2c-tools if necessary)
outfile = "data.csv"
collection_time = 10

start = time.perf_counter()

with open(outfile,'w') as f:
    while time.perf_counter() - start < collection_time:
        accel_data = mpu.get_accel_data()
        gyro_data = mpu.get_gyro_data()
        
        line = f"{accel_data['x']},{accel_data['y']},{accel_data['z']},{gyro_data['x']},{gyro_data['y']},{gyro_data['z']}\n"
        f.write(line)
        time.sleep(.1)
