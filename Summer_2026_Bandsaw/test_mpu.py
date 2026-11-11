# Worked code
import time
from mpu6050 import mpu6050

# Initialize the MPU6050 sensor
MPU_ADDR = 0x68  # Address of the MPU6050 (use 0x69 if AD0 is high)
sensor = mpu6050(MPU_ADDR)

while True:
    try:
        # Get accelerometer, gyroscope, and temperature data
        accel_data = sensor.get_accel_data()
        gyro_data = sensor.get_gyro_data()
        temp_data = sensor.get_temp()

        # Print the data
        print(f"Accelerometer Data: {accel_data}")
        print(f"Gyroscope Data: {gyro_data}")
        print(f"Temperature: {temp_data} °C")

        # Wait before taking another reading (to control the frequency)
        time.sleep(0.5)

    except KeyboardInterrupt:
        print("Program interrupted. Exiting...")
        break



