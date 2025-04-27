# MicroPython script to control Zifon PT5000 camera gimbal

> [!WARNING]
> This is very much in a draft state right now (as of 2025-04-26). I expect to put polish
> on this in the coming weeks.

You will need a PT5000 gimbal, a MCU with MicroPython installed, and *two* nRF24L01 (or compatible) radio modules.  
This has been tested with Raspberry Pi Pico 2 / 2W microcontroller board.

The nRF24L01+ enhanced version is not required for this (sub-optimum) two radio setup.

The two radio modules will need to be hooked up to two separate SPI buses and the SPI bus initialize statement may need to be modified
to reflect your choice of SPI wiring.

