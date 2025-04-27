# Zifon PT5000 camera gimbal control library
#
#

import sys

def pt5000_decode_angles (payload) :
    azbin = payload[6]*65536 + payload[5] * 256 + payload[4]
    elbin = payload[9]*65536 + payload[8] * 256 + payload[7]   
    az = azbin * 360 / (4*65536)
    el = elbin * 360 / (4*65536)
    return (az,el)

def pt5000_create_packet_ping () :
    return bytearray([0x02,0x00,0x00,0, 0,0,0,0, 0,0])
    #return bytearray([0x02,0,0,0, 0,0,0,0, 0,0])

def pt5000_create_packet_goto_a () :
    return bytearray([0x02,0x29,0x08,0x08, 0,0,0,0, 0,0])

def pt5000_create_packet_goto_b () :
    return bytearray([0x02,0x2b,0x08,0x08, 0,0,0,0, 0,0])
#
# Create a command packet to move the gimbal.
# So far this works for azimuth (pan) move clockwise.
#
# Left pan: 02370808 F1BE03457C0004F09
# 02370808 F1BE 0345 7C00 04F0 || 93 2F || 64
#
def pt5000_create_pan_tilt (azspeed,elspeed) :
    assert azspeed >= -8 and azspeed <=8
    assert elspeed >= -8 and elspeed <=8

    azflags = 0
    if (azspeed>0) : azflags = 0x17
    if (azspeed<0) :
        azspeed = abs(azspeed)
        azflags = 0x15  # was 13
    
    elflags = 0
    if elspeed > 0 : elflags = 0x13
    if (elspeed<0) :
        elspeed = abs(elspeed)
        elflags = 0x11 
        
    # This works for pan right (clockwise) for azspeed 1 to 8.
    #return bytearray([0x02,0x3f,0x08,0x08,    azspeed,elspeed,azflags,elflags,0,0])

    return bytearray([0x02,0x3f,0x08,0x08, azspeed,elspeed, azflags,elflags, 0,0])

    
def decode_packet (payload) :
    
    counter = 0
    prev_azbin = -999
    prev_elbin = -999

    payload = remove_first_n_bits (buf,9)
        
    payload_hex = ""
    for i in range (11) :
        payload_hex += f"{payload[i]:02X}"

    # PT5000 gimbal -> remote controller
    if payload[1] == 0x37 :
        azbin = payload[6]*65536 + payload[5] * 256 + payload[4]
        elbin = payload[9]*65536 + payload[8] * 256 + payload[7]
        if (azbin != prev_azbin) or (elbin != prev_elbin) :
            az = azbin * 360 / (4*65536)
            el = elbin * 360 / (4*65536)
            #print (f"{counter:5d} {payload_hex} az={azbin} {az:.2f}deg el={elbin} {el:.2f}deg")
            prev_azbin = azbin
            prev_elbin = elbin
