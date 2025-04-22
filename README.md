# zifon_pt5000
Documentation of the radio protocol used by the Zifon PT5000 camera gimbal and other useful information pertaining to this device.

This is preliminary information which may change as I gain more experience with this device. 

## Background

I purchased this device for a research and development project which required a platform which allowed a camera and sensors to be mounted on a tripod and rotated around 360° and tilted up/down.

## Summary of findings

### Status

As of 2025-04-21 I can successfully 'snoop' on packets sent from the remote control unit to the gimbal and vice versa. I can decode joystick deflection on the remote control unit and the current gimbal angles from the gimbal unit. 

I've also had limited success controlling the gimbal (my main issue is lack of understanding of the details of the nRF24L01+ and that the Micropython 'official' nRF24L01 seems to have limited support for the advanced features of the nRF24L01+).

### Radio settings
The radio protocol is based on the nRF24L01+ radio module (it's actually a Si24R1 which is a clone). It defaults to frequency channel 80 (2.480GHz). The 5 byte address is 0x52560c0702 (transmitted as little endian with 0x02 first). The symbol rate is 1Mbps, packet payload length is 10 bytes (excluding 9 bit header). 2 byte checksums are used.

### Packet payload 

> [!NOTE]  
> Byte index 0 means the first byte of the payload, index 1 the second etc.

> [!NOTE]
> Note: depending on which nRF24L01 library you use, you may have to deal with the 9 bit (yes, 9 bits!!) nRF24L01+ header yourself. That will involve stripping the first byte and shifting everything by one bit.

Common to both gimbal and remote control: Byte index 0 I *think* is the virtual channel number which is configurable on the remote control and gimbal. Byte index 1 is the transmitting device: value of 0x37 is the gimbal transmitting to the remote control, a value of 0x3f is the remote control transmitting to the gimbal.

Gimbal to remote control packet:  bytes index 4 to 6 (3 bytes, little endian) : 24bit azimuth angle. Multiply by ( 360 / 262144 ) to get azimuth in degrees. Payload bytes index 7 - 9 (3 bytes, little endian): 24 bit elevation axis angle.  Multiply by ( 360 / 262144 ) to get elevation axis in degrees. Note: this is not the elevation relative to the horizontal.  0 degrees is one stop of the tilt axis, so that needs to be adjusted to get elevation relative to the horizontal.  The other bytes are still to be determined but the battery status must be in there (probably the last two bytes).

Remote control to gimbal packet:  Byte index 4 is the joystick left-right deflection (absolute) and byte 5 is up-down joystick deflection (absolute). I think allowed values are 0 - 8?. Byte 6 encodes if there is any deflection (bit4) and the sign (direction) of the deflection (bit2). Byte 7 is similar for the joystick up/down axis. There is a lot more to this TBD.

In addition to the above two packet types, the remote control unit sends many what I assume are 'ping' packets with byte index 1 set to 0x00. The purpose of these packets is still not fully understood.

|                                | 0  | 1    | 2    | 3    | 4     | 5     | 6    | 7        | 8        | 9    |
|--------------------------------|----|------|------|------|-------|-------|------|----------|----------|------|
|Gimbal to controller (joystick) | ch | 0x37 | ?    | ?    | aza0  | aza1  | aza2 | ela0     | ela1     | ela2 |
|Gimbal to controller (ping)     | ch | 0x00 | 0x00 | 0x00 | 0x00  | 0x00  | 0x00 | 0x00     | 0x00     | 0x00 |
|Controller to gimbal            | ch | 0x3f | ?    | ?    | jsx?  | jsx?  | ?    | jsy?     | jsy?     | ?    |

ch: channel number (default 2); 
aza{n}: azimuth angle where azimuth_degrees = 360 * (aza0 + aza1 * 256 + aza2 * 65536) / 262144 ;
ela{n}: elevation angle where elevation_degrees = 360 * (aza0 + aza1 * 256 + aza2 * 65536) / 262144 ;
jsx: joystick x-axis (left-right) ;
jsy: joystick y-axis (down-up) ; 



### Transmitting packets to control the gimbal

This seems to be more complex than I had hoped.  Retransmitting the remote control to gimbal packets will work only if the remote control unit is also switched on. So I think that means the nRF24L01 auto-ack system must be enabled. Also the motion is rough - I think the gimbal needs to recieve joystick commands in rapid succession or the stepper motor stutters. Either the remote control is interfering (the manual notes that operating two remotes at the same time will result in rough motor operation) or the micropython loop sending the packet isn't iterating fast enough.

## Remote control hardware and software

This section is coming soon. It will include a nRF24L01+ to Raspberry Pi Pico 2 microcontroller hookup guide and a micropython script to listen and control the device. This should be easily extendable to any computer or microcontroller with a SPI bus eg a full Raspberry Pi (1 - 5), Arduino etc. (Actually you can probably get away without a SPI peripheral and bit-bang the SPI protocol with GPIO lines).

