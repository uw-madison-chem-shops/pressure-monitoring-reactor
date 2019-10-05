import smbus
import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Slider


bus = smbus.SMBus(1)

# some change


#MCP3426, MCP3427 & MCP3428 addresses are controlled by address lines A0 and A1
# each address line can be low (GND), high (VCC) or floating (FLT)
MCP3428_DEFAULT_ADDRESS			= 0x68
MCP3428_CONF_A0GND_A1GND		= 0x68
MCP3428_CONF_A0GND_A1FLT		= 0x69
MCP3428_CONF_A0GND_A1VCC		= 0x6A
MCP3428_CONF_A0FLT_A1GND		= 0x6B
MCP3428_CONF_A0VCC_A1GND		= 0x6C
MCP3428_CONF_A0VCC_A1FLT		= 0x6D
MCP3428_CONF_A0VCC_A1VCC		= 0x6E
MCP3428_CONF_A0FLT_A1VCC		= 0x6F

# /RDY bit definition
MCP3428_CONF_NO_EFFECT			= 0x00
MCP3428_CONF_RDY			= 0x80

# Conversion mode definitions
MCP3428_CONF_MODE_ONESHOT		= 0x00
MCP3428_CONF_MODE_CONTINUOUS		= 0x10

# Channel definitions
#MCP3425 have only the one channel
#MCP3426 & MCP3427 have two channels and treat 3 & 4 as repeats of 1 & 2 respectively
#MCP3428 have all four channels
MCP3428_CONF_CHANNEL_1			= 0x00
MCP3428_CHANNEL_2			= 0x20
MCP3428_CHANNEL_3			= 0x40
MCP3428_CHANNEL_4			= 0x60


# Sample size definitions - these also affect the sampling rate
# 12-bit has a max sample rate of 240sps
# 14-bit has a max sample rate of  60sps
# 16-bit has a max sample rate of  15sps
MCP3428_CONF_SIZE_12BIT			= 0x00
MCP3428_CONF_SIZE_14BIT			= 0x04
MCP3428_CONF_SIZE_16BIT			= 0x08
MCP3428_CONF_SIZE_18BIT			= 0x0C

# Programmable Gain definitions
MCP3428_CONF_GAIN_1X			= 0x00
MCP3428_CONF_GAIN_2X			= 0x01
MCP3428_CONF_GAIN_4X			= 0x02
MCP3428_CONF_GAIN_8X			= 0x03

#Default values for the sensor
ready = MCP3428_CONF_RDY
channel = MCP3428_CONF_CHANNEL_1
mode = MCP3428_CONF_MODE_CONTINUOUS
rate = MCP3428_CONF_SIZE_12BIT
gain = MCP3428_CONF_GAIN_1X
VRef = 2.048 # 2.048 Volts


# Power on and prepare for general usage.
def initialise():
# Default :Channel 1,Sample Rate 15SPS(16- bit),Gain x1 Selected
	
	setRate(ready)
	setChannel(channel)
	setMode(mode)
	setSample(rate)
	setGain(gain)


# Set Ready Bit 
#In read mode ,it indicates the output register has been updated with a new conversion.
#In one-shot Conversion mode,writing Initiates a new conversion.
def setRate(ready) :

    	bus.write_byte(MCP3428_DEFAULT_ADDRESS, ready)
    	

#Set Channel Selection
#C1-C0: Channel Selection Bits
#00 = Select Channel 1 (Default)
#01 = Select Channel 2
#10 = Select Channel 3 
#11 = Select Channel 4 
def setChannel(channel) :
	
	bus.write_byte(MCP3428_DEFAULT_ADDRESS,channel)
	
    
#Set Conversion Mode
#1= Continous Conversion Mode
#0 = One-shot Conversion Mode
def setMode(mode) :

	bus.write_byte(MCP3428_DEFAULT_ADDRESS,mode)
	
#Set Sample rate selection bit
# 00 : 240 SPS-12 bits
# 01 : 60 SPS 14 bits
# 10 : 15 SPS 16 bits
def setSample(rate) :

	bus.write_byte(MCP3428_DEFAULT_ADDRESS,rate)
	
#Set the PGA gain
# 00 : 1 V/V
# 01 : 2 V/V
# 10 : 4 V/V
# 11 : 8 V/V
def setGain(gain) :

	bus.write_byte(MCP3428_DEFAULT_ADDRESS,gain)    
   
#Get the measurement for the ADC values  from the register
#using the General Calling method

def getadcread() :
    data = bus.read_i2c_block_data(MCP3428_DEFAULT_ADDRESS,0x00,2)
    value = ((data[0] << 8) | data[1])
    if (value >= 32768):
        value = 65536 - value
    return value
	
# The output code is proportional to the voltage difference b/w two analog points
#Checking the conversion value
#Conversion of the raw data into 
# Shows the output codes of input level using 16-bit conversion mode

def getconvert():
    code = getadcread() 
    return code * (20 / 909.)
    #setSample(rate)
    N = 12 # resolution,number of bits
    voltage = (2 * VRef* code)/ (2**N)
    return voltage


if __name__ == '__main__':
    # initialize the device
    initialise()

    # prepare animated figure
    fig = plt.figure()
    gs = gridspec.GridSpec(2, 1, height_ratios=[10, 1])
    ax = plt.subplot(gs[0])
    hl, = plt.plot([0, 0], [1, 1])
    plt.ylim(0, 150)
    xi = []
    yi = []
    def update_line(y):
        xi.append(time.time())
        yi.append(y)
        hl.set_xdata(xi)
        hl.set_ydata(yi)
        plt.draw()
        plt.ylim(min(yi), max(yi))
        plt.xlim(min(xi), max(xi))
    def data_gen():
        while True:
            vs = []
            for _ in range(100):
                vs.append(getconvert())
            current = np.average(vs)
            current -= 4.
            current *= 150 / 16.
            yield current
    ani = animation.FuncAnimation(fig, update_line, data_gen, interval=100)
    plt.show()
