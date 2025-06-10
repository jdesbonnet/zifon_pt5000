# MicroPython script to control Zifon PT5000 camera gimbal

> [!WARNING]
>
> Update 2025-06-10: The code here is now obsolete. New python code running on a Raspberry Pi 5
> that can interface with a nRF24L01+ (or clone) on its SPI bus will be posted soon.
> 


![Raspberry Pi Pico2W controller diagram](/Zifon_PT5000_Pico2W_controller.png)


You will need a PT5000 gimbal, a MCU with MicroPython installed, and *two* nRF24L01 (or compatible) radio modules.  
This has been tested with Raspberry Pi Pico 2 / 2W microcontroller board.

The nRF24L01+ enhanced version is not required for this (sub-optimum) two radio setup.

The two radio modules will need to be hooked up to two separate SPI buses and the SPI bus initialize statement may need to be modified
to reflect your choice of SPI wiring.

When running this script it's important to switch off the 'official' remote control units as they will interfere with the operation 
this control script (resulting in jerky motion).
