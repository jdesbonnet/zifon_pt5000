

# zifon_pt5000
Documentation of the radio protocol used by the Zifon PT5000 camera gimbal and other useful information pertaining to this device.

> [!IMPORTANT]  
> This is preliminary information which may change as I gain more experience with this device. 

## Background

I purchased this device for a research and development project which required a platform which allowed a camera and sensors to be mounted on a tripod and rotated around 360° and tilted up/down.

## Summary of findings

### Status

As of 2025-04-24 I can successfully 'snoop' on packets sent from the remote control unit to the gimbal and vice versa while on the default channel 2. I can decode the joystick deflection on the remote control unit and the current gimbal angles from the gimbal unit. 

I also have a Micropyton script running an a Raspberry Pi Pico 2W with connected *two* nRF24L01+ radio modules which can command the gimbal to any arbitrary azimuth or elevation angle.
The reason for two radios is that I have not yet been able to configure the nRF24L01+ modules to send a joystick command and receive the angles back. The work-around is to transmit with one radio and listen with another.

### Radio settings
The radio protocol is based on the nRF24L01+ radio module (it's actually a Si24R1 which is a clone). It defaults to frequency channel 80 (2.480GHz). The 5 byte address is 0x52560c0702 (transmitted as little endian with 0x02 first). The symbol rate is 1Mbps, packet payload length is 10 bytes (excluding 9 bit header). 2 byte checksums are used.

### Radio packets 

> [!NOTE]
> Note: depending on which nRF24L01 library you use, you may have to deal with the 9 bit (yes, 9 bits!!) nRF24L01+ header yourself. That will involve stripping the first byte and shifting everything by one bit.

|                                                    | 0    | 1    | 2    | 3    | 4     | 5     | 6    | 7     | 8     | 9     |
|----------------------------------------------------|------|------|------|------|-------|-------|------|-------|-------|-------|
|Gimbal to controller: report gimbal angles          | 0x02 | 0x37 | bat0?| bat1?| aza0  | aza1  | aza2 | ela0  | ela1  | ela2  |
|Controller to gimbal: ping? / nop                   | 0x02 | 0x00 | 0x00 | 0x00 | 0x00  | 0x00  | 0x00 | 0x00  | 0x00  | 0x00  |
|Controller to gimbal: photo key                     | 0x02 | 0x19 | 0x00 | 0x00 | 0x00  | 0x00  | 0x00 | 0x00  | 0x00  | 0x00  |
|Controller to gimbal: V key press                   | 0x02 | 0x1B | 0x00 | 0x00 | 0x00  | 0x00  | 0x00 | 0x00  | 0x00  | 0x00  |
|Controller to gimbal: H key press                   | 0x02 | 0x1D | 0x00 | 0x00 | 0x00  | 0x00  | 0x00 | 0x00  | 0x00  | 0x00  |
|Controller to gimbal: Auto+A key press (goto A)     | 0x02 | 0x29 | 0x00 | 0x00 | 0x00  | 0x00  | 0x00 | 0x00  | 0x00  | 0x00  |
|Controller to gimbal: Auto+B key press (goto B)     | 0x02 | 0x2B | 0x00 | 0x00 | 0x00  | 0x00  | 0x00 | 0x00  | 0x00  | 0x00  |
|Controller to gimbal: Auto+S key press (scan A↔B)   | 0x02 | 0x2D | 0x00 | 0x00 | 0x00  | 0x00  | 0x00 | 0x00  | 0x00  | 0x00  |
|Controller to gimbal: A key press                   | 0x02 | 0x2F | 0x00 | 0x00 | 0x00  | 0x00  | 0x00 | 0x00  | 0x00  | 0x00  |
|Controller to gimbal: B key press                   | 0x02 | 0x31 | 0x00 | 0x00 | 0x00  | 0x00  | 0x00 | 0x00  | 0x00  | 0x00  |
|Controller to gimbal: S key press (stop)            | 0x02 | 0x33 | 0x00 | 0x00 | 0x00  | 0x00  | 0x00 | 0x00  | 0x00  | 0x00  |
|Controller to gimbal: joystick                      | 0x02 | 0x3f | 0x00 | 0x00 | jxm   | jym   | jxd  | jyd   | 0x00  | 0x00  |
|Controller to gimbal: Auto+joystick                 | 0x02 | 0x41 | 0x00 | 0x00 | 0x00  | 0x00  | ajlr | ajdu  | 0x00  | 0x00  |

Table of known packet types. All packets 10 bytes of payload (index 0 - 9).

aza{n}: azimuth angle where azimuth_degrees = 360 * (aza0 + aza1 * 256 + aza2 * 65536) / 262144 ;
ela{n}: elevation angle where elevation_degrees = 360 * (aza0 + aza1 * 256 + aza2 * 65536) / 262144 ;
jxm: joystick x-axis deflection magnitude (1 - 8) ;
jxd: joystick x-axis direction of deflection: 0x17 for joystick left or 0x15 for joystick right or ;
jym: joystick y-axis deflection magnitude (1 - 8) ;
jyd: joystick y-axis direction of deflection: 0x13 for joystick down or 0x11 for joystick up ;

ajlr: 0x25 when auto+joystick_left, 0x23 when auto+joystick_right ;
ajdu: 0x21 when auto+joystick_down, 0x1f when auto+joystick_up ;

The joystick packets must be sent frequently for smooth motion. From experiment a delay of more than 3ms between packets will cause juttery motion.

### Channels

The PT5000 implements the concept of channels, allowing multiple gimbals and remote controls to operate in the same space. 
The PT5000 comes preconfigured to use channel 2. It is unclear how this is implemented. The documenation here assumes
that the gimbal is set to channel 2.

I had assumed byte index 0 of all the packets was the virtual channel number and that all packets would be transmitted
on the same frequency with the same address. However experiments have ruled this out. It's something else (possibly involving
different addresses, and maybe frequencies).

### Transmitting packets to control the gimbal

This has been implemented in Micropyhon on a Raspberry Pi Pico 2W. The caveat is that I currently need to use two nRF24L01+ modules (one to transmit, the other to listen). 

## Remote control hardware and software

See [here](/micropython/README.md) 

