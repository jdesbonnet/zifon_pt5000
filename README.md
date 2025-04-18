# zifon_pt5000
Documentation of the radio protocol used by the Zifon PT5000 camera gimbal and other useful information pertaining to this device.

This is preliminary information which may change as I gain more experience with this device. 

## Background

I purchased this device for a research and development project which required a platform which allowed a camera and sensors to be mounted on a tripod and rotated around 360° and tilted up/down.

## Summary of findings

### Radio settings
The radio protocol is based on the nRF24L01+ radio module (it's actually a Si24R1 which is a clone). It defaults to frequency channel 80 (2.480GHz). The address is 5 byte address 0x52560c0702 (transmitted as little endian with 0x02 first). Symbol rate is 1Mbps, packet payload length 16 bytes (excluding 9 bit header). 2 byte checksums are used.

### Packet payload 

Note: byte index 0 means the first byte of the payload, index 1 the second etc.

Common to both gimbal and remote control: Byte index 0 I *think* this is the channel number which is configureable on the remote control and gimbal. Byte index 1 is the transmitting device: value of 0x37 is the gimbal transmitting to the remote control, a value of 0x3f is the remote control transmitting to the gimbal.

Gimbal to remote control packet:  bytes index 4 to 6 (3 bytes) : 24bit azimuth angle. Multiply by ( 360 / 262144 ) to get azimuth in degrees. Payload bytes index 7 - 9 (3 bytes): 24 bit elevation axis angle.  Multiply by ( 360 / 262144 ) to get elevation axis in degrees. Note: this is not the elevation relative to the horizontal.  0 degrees is one stop of the tilt axis, so that needs to be adjusted to get elevation relative to the horizontal.  The other bytes are still to be determined but the battery status must be in there (probably the last two bytes).

Remote control to gimbal packet:  Byte index 4 is the joystick left-right deflection (absolute) and byte 5 is up-down joystick deflection (absolute). I think allowed values are 0 - 8?. Byte 6 encodes if there is any deflection (bit4) and the sign (direction) of the deflection (bit2). Byte 7 is similar for the joystick up/down axis. There is a lot more to this TBD.
