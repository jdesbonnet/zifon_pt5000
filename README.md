# zifon_pt5000
Documentation of the radio protocol used by the Zifon PT5000 camera gimbal and other useful information pertaining to this device.

> [!IMPORTANT]  
> This is preliminary information which may change as I gain more experience with this device. 

## Background

I purchased this device for a research and development project which required a platform which allowed a camera and sensors to be mounted on a tripod and rotated around 360° and tilted up/down.

## Summary of findings

### Status

As of 2025-04-22 I can successfully 'snoop' on packets sent from the remote control unit to the gimbal and vice versa while on the default channel 2. I can decode the joystick deflection on the remote control unit and the current gimbal angles from the gimbal unit. 

I have a Micropyton script running an a Raspberry Pi Pico 2W with connected nRF24L01+ module that can control both axes (pan and tilt) of the gimbal. This happens (out of necessity) with the remote control unit switched off. If attempting to control the gimbal by script with the remote control unit switched on, the two radios interfere with each other and the motion is 'jerky'.

However I have not been able to query gimbal angles while the remote control is off. Previous success in getting gimbal angles relied on passively snooping on gimbal to remote control traffic. I believe the gimbal sends gimbal angles back in a 'ack with payload' to the joystick commands. I have not (yet) been sucessfull in configuring the radio to receive these ack packets.  

My goal is a to implement a set of commands that can do either relative moves on pan/tilt to an exact number of degrees, or tell the gimbal to pan/tilt to an absolute heading / elevation angle.


### Radio settings
The radio protocol is based on the nRF24L01+ radio module (it's actually a Si24R1 which is a clone). It defaults to frequency channel 80 (2.480GHz). The 5 byte address is 0x52560c0702 (transmitted as little endian with 0x02 first). The symbol rate is 1Mbps, packet payload length is 10 bytes (excluding 9 bit header). 2 byte checksums are used.

### Radio packets 

> [!NOTE]
> Note: depending on which nRF24L01 library you use, you may have to deal with the 9 bit (yes, 9 bits!!) nRF24L01+ header yourself. That will involve stripping the first byte and shifting everything by one bit.

|                                | 0    | 1    | 2    | 3    | 4     | 5     | 6    | 7     | 8     | 9     |
|--------------------------------|------|------|------|------|-------|-------|------|-------|-------|-------|
|Gimbal to controller (angles)   | 0x02 | 0x37 | ?    | ?    | aza0  | aza1  | aza2 | ela0  | ela1  | ela2  |
|Controller to gimbal (ping?)    | 0x02 | 0x00 | 0x00 | 0x00 | 0x00  | 0x00  | 0x00 | 0x00  | 0x00  | 0x00  |
|Controller to gimbal (joystick) | 0x02 | 0x3f | 0x08 | 0x08 | jxm   | jym   | jxd  | jyd   | ?     | ?     |
|Controller to gimbal (photo key)| 0x02 | 0x19 | 0x08 | 0x08 | 0x00  | 0x00  | 0x00 | 0x00  | 0x00  | 0x00  |

Table of packet types. All packets 10 bytes of payload (index 0 - 9).

aza{n}: azimuth angle where azimuth_degrees = 360 * (aza0 + aza1 * 256 + aza2 * 65536) / 262144 ;
ela{n}: elevation angle where elevation_degrees = 360 * (aza0 + aza1 * 256 + aza2 * 65536) / 262144 ;
jxm: joystick x-axis deflection magnitude (1 - 8) ;
jxd: joystick x-axis direction of deflection: 0x17 for joystick left or 0x15 for joystick right or ;
jym: joystick y-axis deflection magnitude (1 - 8) ;
jyd: joystick y-axis direction of deflection: 0x13 for joystick down or 0x11 for joystick up ;

### Channels

The PT5000 implements the concept of channels, allowing multiple gimbals and remote controls to operate in the same space. 
The PT5000 comes preconfigured to use channel 2. It is unclear how this is implemented. The documenation here assumes
that the gimbal is set to channel 2.

I had assumed byte index 0 of all the packets was the virtual channel number and that all packets would be transmitted
on the same frequency with the same address. However experiments have ruled this out. It's something else (possibly involving
different addresses, and maybe frequencies).

### Transmitting packets to control the gimbal

This has been implemented in Micropyhon on a Raspberry Pi Pico 2W. The caveat is that I can only send command packets one way. I have not yet been able to readback the gimbal angles. 

## Remote control hardware and software

This section is coming soon. It will include a nRF24L01+ to Raspberry Pi Pico 2 microcontroller hookup guide and a micropython script to listen and control the device. This should be easily extendable to any computer or microcontroller with a SPI bus eg a full Raspberry Pi (1 - 5), Arduino etc. (Actually you can probably get away without a SPI peripheral and bit-bang the SPI protocol with GPIO lines).

