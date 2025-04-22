# zifon_pt5000
Documentation of the radio protocol used by the Zifon PT5000 camera gimbal and other useful information pertaining to this device.

> [!IMPORTANT]  
> This is preliminary information which may change as I gain more experience with this device. 

## Background

I purchased this device for a research and development project which required a platform which allowed a camera and sensors to be mounted on a tripod and rotated around 360° and tilted up/down.

## Summary of findings

### Status

As of 2025-04-22 I can successfully 'snoop' on packets sent from the remote control unit to the gimbal and vice versa while on the default channel 2. I can decode joystick deflection on the remote control unit and the current gimbal angles from the gimbal unit. 

I now have a Micropyton script that can control both axes of the gimbal. However I havn't been able to command the gimbal while simultaneously reading the gimbal angles. This is down to my limited understanding of the detailed operation of the nRF24L01+ radio, EnhancedShockBurst mode etc.

### Radio settings
The radio protocol is based on the nRF24L01+ radio module (it's actually a Si24R1 which is a clone). It defaults to frequency channel 80 (2.480GHz). The 5 byte address is 0x52560c0702 (transmitted as little endian with 0x02 first). The symbol rate is 1Mbps, packet payload length is 10 bytes (excluding 9 bit header). 2 byte checksums are used.

### Packet payload 

> [!NOTE]
> Note: depending on which nRF24L01 library you use, you may have to deal with the 9 bit (yes, 9 bits!!) nRF24L01+ header yourself. That will involve stripping the first byte and shifting everything by one bit.

Table of packet types.

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

Channels:

The PT5000 comes preconfigured to use channel 2. I had assumed byte index 0 of all the packets was the virtual channel number, but changing 
channels on the gimal and controller meant I could not sniff packets any more. I tried changing the nRF24L01 frequency channel, but I still could not
pick up any packets on channels other than 2. So it's currently unclear to me how the channel mechanism works. So for the moment I'm stuck with
default channel 2.



### Transmitting packets to control the gimbal

This seems to be more complex than I had hoped.  Retransmitting the remote control to gimbal packets will work only if the remote control unit is also switched on. So I think that means the nRF24L01 auto-ack system must be enabled. Also the motion is rough - I think the gimbal needs to recieve joystick commands in rapid succession or the stepper motor stutters. Either the remote control is interfering (the manual notes that operating two remotes at the same time will result in rough motor operation) or the micropython loop sending the packet isn't iterating fast enough.

## Remote control hardware and software

This section is coming soon. It will include a nRF24L01+ to Raspberry Pi Pico 2 microcontroller hookup guide and a micropython script to listen and control the device. This should be easily extendable to any computer or microcontroller with a SPI bus eg a full Raspberry Pi (1 - 5), Arduino etc. (Actually you can probably get away without a SPI peripheral and bit-bang the SPI protocol with GPIO lines).

