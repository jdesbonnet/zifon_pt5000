"""
Zifon PT5000 controller which accepts commands over local network over WiFi.

This requires two nRF24L01 or nRF24L01+ radio modules to be connected to a Raspberry
Pi Pico (1, 2 or 2W) running MicroPython firmware.

One radio on SPI0 is for transmission of command packets and another on SPI1 is for
reception. In theory it should be possible to use one radio, but I have not been
sucessful in configuring the radio module to do so.

The current version relies on expecitly prefixing the 9 bit Packet Control structure
and removing it from received packets. Ie it's communicating to a device using
Enhanced ShockBurst but doing so with that feature disabled. A future version will
(hopefully) remove that limitatin and operate with just one radio.

Hooking up the radios: see lines where spi0, csn0, ce0, spi1, csn1, ce1 pinouts
are defined.

Version: 0.1
Date: 2025-04-25
Author: Joe Desbonnet

"""

import network
import socket
from machine import Pin, SPI, SoftSPI
from nrf24l01 import NRF24L01
from pt5000 import *

# Boost speed
machine.freq(240000000)


wlan = network.WLAN()       # create station interface (the default, see below for an access point interface)
wlan.active(True)           # activate the interface
scan = wlan.scan()
print (f"scan={scan}")
isconnected = wlan.isconnected()          # check if the station is connected to an AP
print (f"isconnected={isconnected}")
wlan.connect('my_wifi_name', 'my_wifi_pw') # connect to an AP
print (f"connect={connect}")

# Wait for connection
utime.sleep_ms(3000)

wlan.config('mac')          # get the interface's MAC address
ipaddr = wlan.ipconfig('addr4')      # get the interface's IPv4 addresses
print (f"ipaddr={ipaddr}")


# TCP server
addr = socket.getaddrinfo('0.0.0.0', 1234)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)

print('Listening on', addr)

# TX radio
spi0 = SPI(0, sck=Pin(2), mosi=Pin(3), miso=Pin(0))
csn0 = Pin(1, mode=Pin.OUT, value=1)
ce0 = Pin(5, mode=Pin.OUT, value=0)

# RX radio
spi1 = SPI(1, sck=Pin(10), mosi=Pin(11), miso=Pin(8))
csn1 = Pin(9, mode=Pin.OUT, value=1)
ce1 = Pin(13, mode=Pin.OUT, value=0)

# Transmit on nrf0
# It's a 10 byte packet, but 12 is necessary here if sending 9 bit header manually
nrf0 = NRF24L01(spi0, csn0, ce0, payload_size=12)
activate_features(nrf0)
pt5000_init_tx(nrf0)

# Listen on nrf1
nrf1 = NRF24L01(spi1, csn1, ce1, payload_size=12)
pt5000_init_rx(nrf1)

#print ("nrf0:")
#print_registers(nrf0)
#print ("nrf1:")
#print_registers(nrf1)

while True:
    cl, addr = s.accept()
    print('Client connected from', addr)
    cl_file = cl.makefile('rwb', 0)
    
    try:
        while True:
            line = cl_file.readline()
            if not line:
                break
            cmd = line.strip().decode('utf-8')
            part = cmd.split(" ")
            print("Received command:", cmd)

            # Interpret command TODO: find a proper command line parser
            response = "OK"
            
            try :
                if part[0] == "PAN":
                    if part[1] == "ACW" :
                        print ("start pan anti-clockwise (from above)...")
                        packet = build_nrf24_air_packet(pt5000_create_command_packet(0x23), pid=0, no_ack=0, crc_len=2)
                        nrf0.send(packet)
                    if part[1] == "CW" :
                        print ("start pan clockwise (from above)...")
                        packet = build_nrf24_air_packet(pt5000_create_command_packet(0x25), pid=0, no_ack=0, crc_len=2)
                        nrf0.send(packet)
                elif cmd == "GET ANGLES1" :
                    az, el = pt5000_get_gimbal_angles(nrf0,nrf1)

                    # This is problematic with WiFi on. Why?
                    # I had to switch designated tx/rx radios to make this work with WiFi on.
                    #az, el = pt5000_get_gimbal_angles(nrf1,nrf0)
                    response = f"{az} {el}"
                elif cmd == "GET ANGLES2" :
                    # This is problematic with WiFi on. Why?
                    # I had to switch designated tx/rx radios to make this work with WiFi on.
                    az, el = pt5000_get_gimbal_angles(nrf1,nrf0)
                    response = f"{az} {el}"
                elif part[0] == "GET" and part[1] == "ANGLES" :
                    # Experimental get angles using supplied command to ping
                    cmd = int(part[2],0)
                    print (f"cmd=0x{cmd:02X}")
                    # This actually works with WiFi on and also using cmd=0.
                    # Sometimes get a timeout tho'
                    az, el = pt5000_get_gimbal_angles_using_cmd(nrf1,nrf0,cmd)
                    response = f"{az} {el}"
                elif part[0] == "GOTO" :
                    # This is not really working, getting start angle is too unreliable.
                    target_az = float(part[1])
                    # Start angle?
                    print ("finding start angle...")
                    try :
                        az, el = pt5000_get_gimbal_angles_using_cmd(nrf1,nrf0,0)
                    except Exception as e :
                        print ("first attempt at finding start angle failed... trying again")
                        try :
                            az, el = pt5000_get_gimbal_angles_using_cmd(nrf0,nrf1,0)
                        except Exception as e :
                            print ("second attempt at finding start angle failed... giving up")
                            raise Exception ("unable to get start angle")
                    delta_az = target_az - az
                    if delta_az > 180 : delta_az -= 360
                    elif delta_az < -180 : delta_az += 360
                    if delta_az < 0 :
                        # pan decreasing angle
                        packet = build_nrf24_air_packet(pt5000_create_command_packet(0x25), pid=0, no_ack=0, crc_len=2)
                        nrf0.send(packet)
                    elif delta_az > 0 :
                        # pan increasing angle
                        packet = build_nrf24_air_packet(pt5000_create_command_packet(0x23), pid=0, no_ack=0, crc_len=2)
                        nrf0.send(packet)
                    for i in range (1000) :
                        az, el = pt5000_get_gimbal_angles_using_cmd(nrf1,nrf0,0)
                        if (delta_az < 0  and az < target_az) or (delta_az > 0 and az > target_az) :
                            print (f"target reached, az={az}, target_az={target_az}")
                            packet = build_nrf24_air_packet(pt5000_create_command_packet(0x33), pid=0, no_ack=0, crc_len=2)
                            nrf0.send(packet)
                            break
                        print ("timeout waiting to reach target angle")
                elif part[0] == "STOP":
                    print ("stop pan motion...")
                    packet = build_nrf24_air_packet(pt5000_create_command_packet(0x33), pid=0, no_ack=0, crc_len=2)
                    nrf0.send(packet)
                elif part[0] == "SET" and part[1] == "AZSPEED":
                    azspeed = int(part[2])
                    print (f"set azspeed to {azspeed}")
                    packet = build_nrf24_air_packet(pt5000_create_set_azspeed_packet(azspeed), pid=0, no_ack=0, crc_len=2)
                    nrf0.send(packet)
                elif part[0] == "QUIT" :
                    #raise Exception(f"QUIT")
                    break
                else:
                    response = "ERROR: unknown command {part[0]}"
            except Exception as e :
                response = f"ERROR: command fail: {e}"
                
            # Send response back
            cl.send((response + "\n").encode('utf-8'))
            
    except Exception as e:
        print('Connection error:', e)
    finally:
        cl.close()
        
        

