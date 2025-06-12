

# zifon_pt5000

<img align="right" width="150" alt="Zifon PT5000 camera gimbal" src="zifon_pt5000.png">

Documentation of the radio protocol used by the Zifon PT5000 camera gimbal and other useful information pertaining to this device.

> [!IMPORTANT]  
> This is preliminary information which may change as I gain more experience with this device. 


## Background

I purchased this device for a research and development project which required a platform which allowed a camera and sensors to be mounted on a tripod and rotated around 360° and tilted up/down.

## Summary of findings

### Status

As of 2025-05-31: Using a python script on a Raspberry Pi I can successfully send pan/tilt/stop commands without any issue. In response to any command (including a no-operation/ping command) the gimbal returns an acknowledgement packet with data which includes the current azimuth/elevation angle and battery state. I'm still having some trouble reliably receving that ack packet, but I can receive it sufficently often to be able to implement a 'pan to azimuth' routine while monitoring the angles in real time and stopping the gimbal at close to the desired angle.

### Radio settings
The radio protocol is based on the nRF24L01+ radio module (it's actually a Si24R1 which is a clone). It defaults to frequency channel 80 (2.480GHz). The 5 byte address is 0x52560c0702 (transmitted as little endian with 0x02 first). The symbol rate is 1Mbps. Packet payload length is 11 bytes. 2 byte checksums are used.

The gimbal is configured to be a PRX device (see nRF24L01+ datasheet section 7.5.2) and the controllers are configured to be PTX devices (see nRF24L01+ datasheet section 7.5.1). PTX devices initiate a transaction by sending a packet. PRX devices react to incoming packets by issuing an acknowledgment. The gimbal (PRX) will never send any radio traffic unless a controller (PTX) initiates it.


### Radio packets (gimbal to controller)
|                                                    | 0    | 1    | 2    | 3    | 4     | 5     | 6    | 7     | 8     | 9     |  10 |
|----------------------------------------------------|------|------|------|------|-------|-------|------|-------|-------|-------|-----|
| Report gimbal status (angles and battery)          | 0x02 | 0x37 | azs  | els  | aza0  | aza1  | aza2 | ela0  | ela1  | ela2  | bat |

This packet is sent by means of an auto-acknowledgment with data in response to any of the commands below.

### Radio packets (controller to gimbal)

|                                                    | 0    | 1    | 2    | 3    | 4     | 5     | 6    | 7     | 8     | 9     |  10 |
|----------------------------------------------------|------|------|------|------|-------|-------|------|-------|-------|-------|-----|
| Ping / nop                                         | 0x02 | 0x00 | 0    | 0    | 0     | 0     | 0    | 0     | 0     | 0     |  0  |
| Elevation micro-increment *                        | 0x02 | 0x11 | 0    | 0    | 0     | 0     | 0    | 0     | 0     | 0     |  0  |
| Elevation micro-decrement *                        | 0x02 | 0x13 | 0    | 0    | 0     | 0     | 0    | 0     | 0     | 0     |  0  |
| Azimuth micro-increment  *                         | 0x02 | 0x15 | 0    | 0    | 0     | 0     | 0    | 0     | 0     | 0     |  0  |
| Azimuth micro-decrement   *                        | 0x02 | 0x17 | 0    | 0    | 0     | 0     | 0    | 0     | 0     | 0     |  0  |
| Photo key press                                    | 0x02 | 0x19 | 0    | 0    | 0     | 0     | 0    | 0     | 0     | 0     |  0  |
| V key press / set el speed                         | 0x02 | 0x1B | azs  | els  | 0     | 0     | 0    | 0     | 0     | 0     |  0  |
| H key press / set az speed                         | 0x02 | 0x1D | azs  | els  | 0     | 0     | 0    | 0     | 0     | 0     |  0  |
|Controller to gimbal: continuous scan up/down/up    | 0x02 | 0x1F | 0    | 0    | 0     | 0     | 0    | 0     | 0     | 0     |  0  |
|Controller to gimbal: continuous scan down/up/down  | 0x02 | 0x21 | 0    | 0    | 0     | 0     | 0    | 0     | 0     | 0     |  0  |
|Controller to gimbal: continuous scan anti-clockwise| 0x02 | 0x23 | 0    | 0    | 0     | 0     | 0    | 0     | 0     | 0     |  0  |
|Controller to gimbal: continuous scan      clockwise| 0x02 | 0x25 | 0    | 0    | 0     | 0     | 0    | 0     | 0     | 0     |  0  |
|Controller to gimbal: Auto+A key press (goto A)     | 0x02 | 0x29 | 0    | 0    | 0     | 0     | 0    | 0     | 0     | 0     |  0  |
|Controller to gimbal: Auto+B key press (goto B)     | 0x02 | 0x2B | 0    | 0    | 0     | 0     | 0    | 0     | 0     | 0     |  0  |
|Controller to gimbal: Auto+S key press (scan A↔B)   | 0x02 | 0x2D | 0    | 0    | 0     | 0     | 0    | 0     | 0     | 0     |  0  |
|Controller to gimbal: A key press                   | 0x02 | 0x2F | 0    | 0    | 0     | 0     | 0    | 0     | 0     | 0     |  0  |
|Controller to gimbal: B key press                   | 0x02 | 0x31 | 0    | 0    | 0     | 0     | 0    | 0     | 0     | 0     |  0  |
|Controller to gimbal: S key press (stop)            | 0x02 | 0x33 | 0    | 0    | 0     | 0     | 0    | 0     | 0     | 0     |  0  |
|Controller to gimbal: joystick                      | 0x02 | 0x3F | 0    | 0    | jxm   | jym   | jxd  | jyd   | 0     | 0     |  0  |
|Controller to gimbal: Auto+joystick                 | 0x02 | 0x41 | 0    | 0    | 0     | 0     | ajlr | ajdu  | 0     | 0     |  0  |
|Controller to gimbal: Set A to current angles       | 0x02 | 0x43 | 0    | 0    | 0     | 0     | 0    | 0     | 0     | 0     |  0  |
|Controller to gimbal: Set B to current angles       | 0x02 | 0x44 | 0    | 0    | 0     | 0     | 0    | 0     | 0     | 0     |  0  |

Table of known packet types. All packets 10 bytes of payload (index 0 - 9).  * Commands discovered by experimentation: not observed being transmitted by the controller.

aza{n}: azimuth angle where azimuth_degrees = 360 * (aza0 + aza1 * 256 + aza2 * 65536) / 262144 ;
ela{n}: elevation angle where elevation_degrees = 360 * (aza0 + aza1 * 256 + aza2 * 65536) / 262144 ;
bat : battery charge level (1 - 4 ?) ;
jxm: joystick x-axis deflection magnitude (1 - 8) ;
jxd: joystick x-axis direction of deflection: 0x17 for joystick left or 0x15 for joystick right or ;
jym: joystick y-axis deflection magnitude (1 - 8) ;
jyd: joystick y-axis direction of deflection: 0x13 for joystick down or 0x11 for joystick up ;
hs : horizontal speed; vs : vertical speed ;

ajlr: 0x25 when auto+joystick_left, 0x23 when auto+joystick_right ;
ajdu: 0x21 when auto+joystick_down, 0x1f when auto+joystick_up ;

The continuous scan commands (0x1f, 0x21, 0x23, 0x25) operate at the currently set gimbal azimuth / elevation speed which can be set by commands 0x1b, 0x1d. It is possible to set speeds while the continuous scan is in operation.

For commands 0x23, 0x25, the direction 'clockwise' means looking from above down on the gimbal.

The gimbal can be movedi by joystick packets (type 0x3f) which must be sent frequently for smooth motion. From experiment, a delay of more than 3ms between packets will cause juttery motion. It's important that no other controller device or script is running at the same time, else they will intefere with each other resulting in juttery motion.

The gimbal supports quite a few commands, but a goto specified aziumuth and elevation angle command does not seem to be there :-(   This would be super useful.


### Channels

The PT5000 implements the concept of channels, allowing multiple gimbals and remote controls to operate in the same space. 
The PT5000 comes preconfigured to use channel 2. It is unclear how this is implemented. The documenation here assumes
that the gimbal is set to channel 2.

I had assumed byte index 0 of all the packets was the virtual channel number and that all packets would be transmitted
on the same frequency with the same address. However experiments have ruled this out. It's something else (possibly involving
different addresses, and maybe frequencies).


## Remote control hardware and software

See [here](/micropython/README.md) for more information.

![Raspberry Pi Pico2W controller diagram](Zifon_PT5000_Pico2W_controller.png)

## Other Zifon gimbal products

A search of the US FCC (Federal Communications Commission) for 'Zifon' hints that most of their products use identical control hardware.  Internal photos of the YT1500 controller on the FCC site also features a Si24R1 chip. So it is likely this documentation and software will work with other Zifon gimbal products. 

However I know for a fact that it will not work with the YT1000 which is based on the JDY-40 radio module. See https://github.com/featherbear/zifon-yt1000-wifi-acu for information on that gimbal.

## Glossary / terminology

I am using the term 'azimuth' as an alternative to the word 'pan', and 'elevation' as an alternative to 'tilt'.
In the code I've abbreviated azimuth as 'az' and elevation as 'el'.

## Open questions / help

Some items I have not yet solved:
* It would be nice to get this working with one nRF24L01+ module (using EnhancedShockBurst features).
* I still can't find where the gimbal battery status is communicated back to the controller
* I would have thought there was a 'go to gimbal azimuth/elevation angle' command, which would eliminate the need for lots of frequent joystick commands. Maybe it's there (?), but I haven't found it. To go to a specific gimbal azimuth/elevation angle issue joystick commands in a tight loop monitoring the returned gimbal angles.
* The gimbal is preconfigured to "channel 2". It's unclear how other channels work.
* I'd like to know more about the internals of the gimbal, but right now I don't have time to tear it down. Replacing its MCU with my own MCU (eg Raspberry Pi Pico) might be useful, but that will probably mean losing functions of the buttons and display.

Please open a issue in this repository if you have any questions or suggestions. Thanks!

## Related documents
 * [US FCC approval application by Zifon for YT1500 controller](https://apps.fcc.gov/oetcf/eas/reports/GenericSearch.cfm) Enter 'Zifon' for the 'Applicant' field in the search engine (sorry, deep links into this database don't work). There are two product families registered: "2A5TN-YT1000" and "2A5TN-YT1500PRO". The information there is contradictory: model PT5000 is included in the 2A5TN-YT1000 family and I know the YT1000 uses a JDY-40 radio module, not the SI24R1 / nRF24L01+ of the PT5000. Information there includes external and internal photos of the remote control units, but not the gimbal itself. There are some RF emissions tests/certs, but no details on the radio protocols etc.

* Some discussion about this gimbal here: https://www.talkphotography.co.uk/threads/zifon-pt-5000-anyone.763467/
