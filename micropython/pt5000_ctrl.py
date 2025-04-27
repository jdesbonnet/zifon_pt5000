"""
Zifon PT5000 controller.

Status: pre-alpha. This is more an experimentation script right now.

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

import sys
import struct
import utime
import time
from machine import Pin, SPI, SoftSPI
from nrf24l01 import NRF24L01
from nrf24l01 import *
from nrf24l01util import *
from pt5000 import *
from micropython import const

# Missing EN_AA (auto-ack) register address
EN_AA = 0x01


led = Pin("LED", Pin.OUT)
led.off()

# TX radio
spi0 = SPI(0, sck=Pin(2), mosi=Pin(3), miso=Pin(0))
csn0 = Pin(1, mode=Pin.OUT, value=1)
ce0 = Pin(5, mode=Pin.OUT, value=0)

# RX radio
spi1 = SPI(1, sck=Pin(10), mosi=Pin(11), miso=Pin(8))
csn1 = Pin(9, mode=Pin.OUT, value=1)
ce1 = Pin(13, mode=Pin.OUT, value=0)

# PT5000 gimbal address
pipe = b"\x52\x56\x0c\x07\x02"

# PT5000 frequency channel (80 = 2.480GHz)
channel = 80

# It's a 10 byte packet, but 12 is necessary here if sending 9 bit header manually
nrf0 = NRF24L01(spi0, csn0, ce0, payload_size=12)
activate_features(nrf0)

# Transmit on nrf0
# Found that power less than POWER_2 resulted in motion stutter,
# presumably due to nearby interference
nrf0.set_power_speed(POWER_2, SPEED_1M)
nrf0.set_channel (channel)    
nrf0.open_tx_pipe (pipe)
nrf0.open_rx_pipe(0, pipe)
nrf0.reg_write(EN_AA,0)
nrf0.set_crc(2) 

# Listen on nrf1
nrf1 = NRF24L01(spi1, csn1, ce1, payload_size=12)
nrf1.set_power_speed(POWER_0, SPEED_1M)
nrf1.set_channel (channel)    
nrf1.open_rx_pipe(0, pipe)
nrf1.reg_write(EN_AA,0)
nrf1.set_crc(2) 
nrf1.start_listening()

#print ("NRF0 REGISTERS:")
#print_registers(nrf0)
#print ("NRF1 REGISTERS:")
#print_registers(nrf1)

# Target angle accuracy threshold
TAAT = 0.08

def pt5000_get_angles () :
    
    #ping0 = build_nrf24_air_packet(pt5000_create_packet_ping(), pid=0, no_ack=0, crc_len=2)
    #ping1 = build_nrf24_air_packet(pt5000_create_packet_ping(), pid=1, no_ack=0, crc_len=2)
    #ping2 = build_nrf24_air_packet(pt5000_create_packet_ping(), pid=2, no_ack=0, crc_len=2)
    #ping3 = build_nrf24_air_packet(pt5000_create_packet_ping(), pid=3, no_ack=0, crc_len=2)
    
    # Ping is not working... so move slightly instead
    ping0 = build_nrf24_air_packet(pt5000_create_pan_tilt(1,0), pid=0, no_ack=0, crc_len=2)
    ping1 = build_nrf24_air_packet(pt5000_create_pan_tilt(1,0), pid=1, no_ack=0, crc_len=2)
    ping2 = build_nrf24_air_packet(pt5000_create_pan_tilt(1,0), pid=2, no_ack=0, crc_len=2)
    ping3 = build_nrf24_air_packet(pt5000_create_pan_tilt(1,0), pid=3, no_ack=0, crc_len=2)

    az = -999
    el = -999
    for i in range(32) :
        
        #nrf1.stop_listening()
        if (i%2==0) : nrf0.send(ping0)
        if (i%2==1) : nrf0.send(ping1)
        if (i%2==2) : nrf0.send(ping2)
        if (i%2==3) : nrf0.send(ping3)

        #nrf1.start_listening()
        #utime.sleep_ms(1)
        
        if nrf1.any() :
            led.on()
            buf = nrf1.recv()
            led.off()
            payload = remove_first_n_bits(buf,9)
            if (payload[1] == 0x37) :
                    (az,el) = pt5000_decode_angles (payload)
                    print (f"az={az} el={el}")
                    break
            else :
                print (buf_to_hex(payload))
                

    return az, el

# Private function to calculate optimal gimbal speed given proximity to target
def pt5000_calc_opt_speed (target_az, az, target_el, el) :
    """
    Calculate optimum speed for azimuth and elevation movement
    taking into account how close the angle is to target.
    """
    
    assert el >= 0
    
    # How far to travel and in what direction?
    delta_az = target_az - az
    delta_el = target_el - el
    
    # Go clockwise / counterwise to get there quickest
    if (delta_az > 180 ) :
        delta_az -= 360
    elif (delta_az < -180) :
        delta_az += 360
        
    # Decelerate when approaching target. Speed proportional to proximity to target.
    
    if (delta_az >= 10) : azspeed = -4
    elif (delta_az >= 2) : azspeed = -2
    elif (delta_az > TAAT) : azspeed = -1
    elif (delta_az >= -TAAT) : azspeed = 0
    elif (delta_az >= -2) : azspeed = 1
    elif (delta_az >= -10) : azspeed = 2
    elif (delta_az < -10)  : azspeed = 4
    
    if (delta_el >= 10) : elspeed = -4
    elif (delta_el >= 2) : elspeed = -2
    elif (delta_el > TAAT) : elspeed = -1
    elif (delta_el >= -TAAT) : elspeed = 0
    elif (delta_el >= -2) : elspeed = 1
    elif (delta_el >= -10) : elspeed = 2
    elif (delta_el < -10)  : elspeed = 4
    
    #azspeed = int(delta_az * -2)
    #if (azspeed > 8) : azspeed = 8
    #if (azspeed < -8) : azspeed = -8
    #if (azspeed == 0 and abs(delta_az)>0.1) : azspeed = 1 if delta_az < 0 else -1
    
    elspeed = int(delta_el * -2)
    if (elspeed > 8) : elspeed = 8
    if (elspeed < -8) : elspeed = -8
    if (elspeed == 0 and abs(delta_el)>0.1 ) : elspeed = 1 if delta_el < 0 else -1
    
    return azspeed, elspeed

# Make on-the-air joystick packets for the specified gimbal speeds
def pt5000_create_moveto_packets (azspeed, elspeed) :
    if (abs(azspeed)>0 or abs(elspeed)>0) :
        p0 = build_nrf24_air_packet(pt5000_create_pan_tilt(azspeed,elspeed), pid=0, no_ack=0, crc_len=2)
        p1 = build_nrf24_air_packet(pt5000_create_pan_tilt(azspeed,elspeed), pid=1, no_ack=0, crc_len=2)
        p2 = build_nrf24_air_packet(pt5000_create_pan_tilt(azspeed,elspeed), pid=1, no_ack=0, crc_len=2)
        p3 = build_nrf24_air_packet(pt5000_create_pan_tilt(azspeed,elspeed), pid=1, no_ack=0, crc_len=2)

    else :
        # The gimbal does not report angles when joystick is 0,0, so switch to ping packets
        p0 = build_nrf24_air_packet(pt5000_create_pan_tilt(1,0), pid=0, no_ack=0, crc_len=2)
        p1 = build_nrf24_air_packet(pt5000_create_pan_tilt(1,0), pid=1, no_ack=0, crc_len=2)
        p2 = build_nrf24_air_packet(pt5000_create_pan_tilt(1,0), pid=2, no_ack=0, crc_len=2)
        p3 = build_nrf24_air_packet(pt5000_create_pan_tilt(1,0), pid=3, no_ack=0, crc_len=2)
        
    return p0, p1, p2 , p3
        
def pt5000_goto_a () :    
    nrf0.send(build_nrf24_air_packet(pt5000_create_packet_goto_a(), pid=0, no_ack=0, crc_len=2))

def pt5000_goto_b () :    
    nrf0.send(build_nrf24_air_packet(pt5000_create_packet_goto_b(), pid=0, no_ack=0, crc_len=2))



def pt5000_move_to_fast (target_az, target_el) :
    
    az , el = pt5000_get_angles()
    
    # How far to travel and in what direction?
    delta_az = target_az - az
    delta_el = target_el - el
    
    # Go clockwise / counterwise to get there quickest
    if (delta_az > 180 ) :
        delta_az -= 360
    elif (delta_az < -180) :
        delta_az += 360

    if (delta_az > TAAT) : azspeed = -8
    if (delta_az < TAAT) : azspeed = 8
    if (delta_el > TAAT) : elspeed = -8
    if (delta_el < TAAT) : elspeed = 8   
    p0, p1, p2, p3 = pt5000_create_moveto_packets(azspeed,elspeed)

    i = 0

    while True:
        
        i += 1
        j = i % 4
        
        #if (i % 100) == 0 : print ("*",end="")
        if (i > 100000) :
            print ("ERROR: unable to reach target")
            break
        
        try:
            # Vary the PID else packets are rejected by PT5000 gimbal
            if (j==0) : nrf0.send(p0)
            if (j==1) : nrf0.send(p1)
            if (j==2) : nrf0.send(p2)
            if (j==3) : nrf0.send(p3)
            
            #utime.sleep_us(200)
            
            if nrf1.any() :
                led.on()
                buf = nrf1.recv()
                led.off()
                continue
                payload = remove_first_n_bits(buf,9)
                if (payload[1] == 0x37) :
                    (az,el) = pt5000_decode_angles (payload)
                    delta_az = target_az - az
                    delta_el = target_el - el
                    if (delta_az < -180) : delta_az += 360
                    if (delta_az >  180) : delta_az -= 360
                    if abs(delta_az) <= TAAT and abs(delta_el) <= TAAT :
                        print ("STOP")
                        break
        except OSError as e:
            print(f"Send failed for packet {i}: {e}")
                    


def pt5000_move_to (target_az, target_el) :
    
    az , el = pt5000_get_angles()
    #az = 5;
    #el = 47;
    
    if (az == -999 or el == -999) :
        print ("ERROR: start angle could not be determined")
        return
    else :
        print (f"MOVE_TO: az={target_az} el={target_el} start_az={az} start_el={el}")
    
    target_azspeed, target_elspeed = pt5000_calc_opt_speed(target_az,az,target_el,el)
    
    #Accelerate to speed
    current_azspeed = 0.0
    current_elspeed = 0.0
    
    p0, p1, p2, p3 = pt5000_create_moveto_packets(int(current_azspeed),int(current_elspeed))

    print (f"MOVE_TO (az={target_az}, el={target_el}) ")
    
    i = 0

    while True:
        
        i += 1
        #if (i % 100) == 0 : print ("*",end="")
        if (i > 100000) :
            print ("ERROR: unable to reach target")
            break
        
        try:
            # Vary the PID else packets are rejected by PT5000 gimbal
            if (i%4==0) : nrf0.send(p0)
            if (i%4==1) : nrf0.send(p1)
            if (i%4==2) : nrf0.send(p2)
            if (i%4==3) : nrf0.send(p3)
                
            if nrf1.any() :
                led.on()
                buf = nrf1.recv()
                led.off()
                payload = remove_first_n_bits(buf,9)
                if (payload[1] == 0x37) :

                    delta_az = target_az - az
                    delta_el = target_el - el
                    if (delta_az < -180) : delta_az += 360
                    if (delta_az >  180) : delta_az -= 360
                    
                    (az,el) = pt5000_decode_angles (payload)
                    


                    if abs(delta_az) <= TAAT and abs(delta_el) <= TAAT :
                        print ("STOP")
                        break
                    
                    
                    (target_azspeed, target_elspeed) = pt5000_calc_opt_speed (target_az, az, target_el, el)


                    #if (i % 20 == 0) :
                    #    print (f"  az={az:6.2f} el={el:5.2f} target_az={target_az:6.2f} target_el={target_el:5.2f} delta_az={delta_az:5.2f} delta_el={delta_el:5.2f} cazs={current_azspeed} cels={current_elspeed} tazs={target_azspeed} tels={target_elspeed}")
                    # Recalc packets only when needed
                    if (target_azspeed != current_azspeed or target_elspeed != current_elspeed) :
                        if (target_azspeed != 0) :
                            if (target_azspeed > current_azspeed) : current_azspeed += 1
                            if (target_azspeed < current_azspeed) : current_azspeed -= 1
                        else :
                            current_azspeed = 0
                            
                        if (target_elspeed != 0) :
                            if (target_elspeed > current_elspeed) : current_elspeed += 1
                            if (target_elspeed < current_elspeed) : current_elspeed -= 1
                        else :
                            current_elspeed = 0
                            
                        print (f"drive az_speed={current_azspeed:4.2f} el_speed={current_elspeed:4.2f} az={az:5.2f} -> {target_az} el={el:4.2f} -> {target_el}")
                        p0, p1, p2, p3 = pt5000_create_moveto_packets(int(current_azspeed),int(current_elspeed))
                        #print (f"({current_azspeed},{current_elspeed})  ", end="")

                    #print (f"({current_azspeed},{current_elspeed})  ", end="")


                        
                else :
                    #print (buf_to_hex(payload))
                    pass
                
            # Put gap between packets when very slow
            #if (abs(current_azspeed) < 2 and abs(current_elspeed) < 2) :
            #    utime.sleep_ms(100)
                
        except OSError as e:
            print(f"Send failed for packet {i}: {e}")
        
        
        
p0, p1, p2, p3 = pt5000_create_moveto_packets(8,0)

i = 0

#100 is smoothish
d = 250 # reasonable smooth, the odd jutter and stop
d = 200 # not as good as 250
d = 2000 # juttery 
d = 4000 # bad! 
d = 500

while True:

    i += 1
    j = i & 0x3

    led.on()
    
    # Vary the PID else packets are rejected by PT5000 gimbal
    try :
        if (j==0) : nrf0.send(p0)
        if (j==1) : nrf0.send(p1)
        if (j==2) : nrf0.send(p2)
        if (j==3) : nrf0.send(p3)
    except OSError as e:
            print(f"Send failed for packet {i}: {e}")
    led.off()
    
    utime.sleep_us(d)

#print ("move to A...")
#pt5000_goto_a()
#utime.sleep_ms(10000)

#print ("move to B...")
#pt5000_goto_b()
#utime.sleep_ms(10000)

targets = [
   [58.7,49.3], [0,0], [2,2], [5,15], [5,17], [10,17], [20,8], [35,22]
]

for i in range (100) :
    for target in targets :
        print (f"MOVE_TO {target[0]},{target[1]}")
        pt5000_move_to(target[0],target[1])
        utime.sleep_ms(1000)
        final_az, final_el = pt5000_get_angles()
        print (f"final_az={final_az} final_el={final_el}")

  
final_az, final_el = pt5000_get_angles()
print (f"final_az={final_az} final_el={final_el}")
