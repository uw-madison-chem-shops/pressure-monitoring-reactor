import smbus
import time

address = 0x63

bus = smbus.SMBus(1)

bus.write_byte_data(address, 0xC0, 0x00)

time.sleep(0.5)

data = bytearray()

bus.write_byte(address, 0xC1)
time.sleep(0.5)

data = bus.read_i2c_block_data(address, 2)

print data[0]
print data[1]

if((data[0] & 0x80) == 0x80):
    data[0] = data[0] &0x7F
    temp = 1024 - (data[0] * 16 + data[1]/16)
    temp = (temp * 1.8)+32
    print temp
else:
    temp = data[0] * 16 + data[1] / 16
    temp = (temp * 1.8)+32
    print temp
