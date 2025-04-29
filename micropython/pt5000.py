"""
Zifon PT5000 camera gimbal control library.

See https://github.com/jdesbonnet/zifon_pt5000

"""
import sys
#from nrf24l01 import NRF24L01
from nrf24l01 import *
from nrf24l01util import *

# PT5000 command codes
# See https://github.com/jdesbonnet/zifon_pt5000 for details.
CMD_NOP = 0x00
CMD_PAN_ANTICLOCKWISE = 0x23
CMD_PAN_CLOCKWISE = 0x25
CMD_GOTO_A = 0x29
CMD_GOTO_B = 0x2B
CMD_SET_A = 0x43
CMD_SET_B = 0x44

# PT5000 gimbal address
PT5000_ADDR = b"\x52\x56\x0c\x07\x02"

# PT5000 frequency channel (80 = 2.480GHz)
PT5000_FCH   = 80

# Missing EN_AA (auto-ack) register address
EN_AA = 0x01

def pt5000_init_rx (nrf1) :
    '''
    Initialize nRF24L01 / nRF24L01+ radio for receive.
    '''
    # Listen on nrf1
    #nrf1 = NRF24L01(spi1, csn1, ce1, payload_size=12)
    nrf1.set_power_speed(POWER_0, SPEED_1M)
    nrf1.set_channel (PT5000_FCH)
    nrf1.open_tx_pipe (PT5000_ADDR) # not normally used
    nrf1.open_rx_pipe(0, PT5000_ADDR)
    nrf1.reg_write(EN_AA,0)
    nrf1.set_crc(2) 
    nrf1.start_listening()
    
def pt5000_init_tx (nrf0) :
    '''
    Initialize nRF24L01 / nRF24L01+ radio for transmit.
    '''
    # Found that power less than POWER_2 resulted in motion stutter,
    # presumably due to nearby interference
    
    activate_features(nrf0)

    nrf0.set_power_speed(POWER_2, SPEED_1M)
    nrf0.set_channel (PT5000_FCH)    
    nrf0.open_tx_pipe (PT5000_ADDR)
    nrf0.open_rx_pipe(0, PT5000_ADDR)
    nrf0.reg_write(EN_AA,0)
    nrf0.set_crc(2) 


def pt5000_get_gimbal_angles (nrf0,nrf1) :
    """
    Poll PT5000 gimbal for current azimuth and elevation angle.
    
    nrf0: TX radio
    nrf1: RX radio
    
    Implementation is a little complicated. A command must be sent to the gimbal to solicit a
    response which expected to be packet type 0x37 with gimbal angles. However only joystick
    commands seem to work.
    
    Known issues: does not work when Pico 2W wifi enabled. Reason unknown.
    
    """

    # Need to send something to the gimbal so that we get the angles back in response

    # Having trouble with NOP command, try joystick instead (0x15)
    #cmd = 0x00
    #nop0 = build_nrf24_air_packet(pt5000_create_command_packet(cmd), pid=0, no_ack=0, crc_len=2)
    #nop1 = build_nrf24_air_packet(pt5000_create_command_packet(cmd), pid=1, no_ack=0, crc_len=2)
    #nop2 = build_nrf24_air_packet(pt5000_create_command_packet(cmd), pid=2, no_ack=0, crc_len=2)
    #nop3 = build_nrf24_air_packet(pt5000_create_command_packet(cmd), pid=3, no_ack=0, crc_len=2)
    
    nop0 = build_nrf24_air_packet(pt5000_create_joystick_packet(1,0), pid=0, no_ack=0, crc_len=2)
    nop1 = build_nrf24_air_packet(pt5000_create_joystick_packet(1,0), pid=1, no_ack=0, crc_len=2)
    nop2 = build_nrf24_air_packet(pt5000_create_joystick_packet(1,0), pid=2, no_ack=0, crc_len=2)
    nop3 = build_nrf24_air_packet(pt5000_create_joystick_packet(1,0), pid=3, no_ack=0, crc_len=2)
    
    # Having issues where angle values which are clearly out of date are
    # being returned. A few things were tried to cear out the radio of
    # any old traffic which didn''t work. The following block of code
    # seems to work.
    
    nrf1.start_listening()
    
    nrf1.flush_rx()
    for i in range(32) :    
        j = i % 4;
        if (j==0) : nrf0.send(nop0)
        elif (j==1) : nrf0.send(nop1)
        elif (j==2) : nrf0.send(nop2)
        elif (j==3) : nrf0.send(nop3)
    nrf1.flush_rx()

        
    response_packet_count = 0
    last_response_packet_type = -1
    for i in range(1024) :
        
        j = i % 4;
        if (j==0) : nrf0.send(nop0)
        elif (j==1) : nrf0.send(nop1)
        elif (j==2) : nrf0.send(nop2)
        elif (j==3) : nrf0.send(nop3)
        #utime.sleep_us(500)
        if nrf0.any() : print ("*",end="")
        
        # This can pick up on the transmitted packet, how can we avoid this?
        while nrf1.any() :
            response_packet_count += 1
            #led.on()
            buf = nrf1.recv()
            #led.off()
            payload = remove_first_n_bits(buf,9)
            last_response_packet_type = payload[1]
            if (payload[1] == 0x37) :
                    (az,el) = pt5000_decode_angles (payload)
                    print (f"az={az} el={el} i={i}")
                    return az,el
            else :
                #print (f"P={buf_to_hex(payload)}")
                pass
            
    raise Exception(f"ERROR: cannot read gimbal angles, tried {i} iterations, received {response_packet_count} response packets, last type={last_response_packet_type:02X}")

def pt5000_get_gimbal_angles_using_cmd (nrf0,nrf1,cmd) :
    """
    Poll PT5000 gimbal for current azimuth and elevation angle (experimental version which
    takes the command to use to poll as parameter). Command type 0x00 (NOP) sometimes works.
    
    nrf0: TX radio
    nrf1: RX radio
        
    """

    # Need to send something to the gimbal so that we get the angles back in response
    nop0 = build_nrf24_air_packet(pt5000_create_command_packet(cmd), pid=0, no_ack=0, crc_len=2)
    nop1 = build_nrf24_air_packet(pt5000_create_command_packet(cmd), pid=1, no_ack=0, crc_len=2)
    nop2 = build_nrf24_air_packet(pt5000_create_command_packet(cmd), pid=2, no_ack=0, crc_len=2)
    nop3 = build_nrf24_air_packet(pt5000_create_command_packet(cmd), pid=3, no_ack=0, crc_len=2)

    
    # Having issues where angle values which are clearly out of date are
    # being returned. A few things were tried to cear out the radio of
    # any old traffic which didn''t work. The following block of code
    # seems to work.
    
    nrf1.start_listening()
    nrf1.flush_rx()
    for i in range(32) :    
        j = i % 4;
        if   (j==0) : nrf0.send(nop0)
        elif (j==1) : nrf0.send(nop1)
        elif (j==2) : nrf0.send(nop2)
        elif (j==3) : nrf0.send(nop3)
    nrf1.flush_rx()

    
    # Now ping the gimbal expecting a ack-with-payload containing angles in return.
    # Since all attempts to get this to work with the 'official' micropython nrf24l01
    # library have failed, no option but to listen for this ack in PRX mode.
    response_packet_count = 0
    last_response_packet_type = -1
    for i in range(512) :
        
        j = i % 4;
        if   (j==0) : nrf0.send(nop0)
        elif (j==1) : nrf0.send(nop1)
        elif (j==2) : nrf0.send(nop2)
        elif (j==3) : nrf0.send(nop3)
        #utime.sleep_us(500)
        if nrf0.any() : print ("*",end="")
        
        # This can pick up on the transmitted packet, how can we avoid this?
        while nrf1.any() :
            response_packet_count += 1
            #led.on()
            buf = nrf1.recv()
            #led.off()
            payload = remove_first_n_bits(buf,9)
            last_response_packet_type = payload[1]
            if (payload[1] == 0x37) :
                    (az,el) = pt5000_decode_angles (payload)
                    print (f"az={az} el={el} i={i}")
                    return az,el
            else :
                #print (f"P={buf_to_hex(payload)}")
                pass
            
    raise Exception(f"cannot read gimbal angles, tried {i} iterations, received {response_packet_count} response packets, last type={last_response_packet_type:02X}")


def pt5000_decode_angles (payload) :
    """
    From gimbal to controller ack-with payload packet (type 0x37) extract
    azimuth and elevation angles in degrees.
    """
    
    assert payload[1] == 0x37
    
    azbin = payload[6]*65536 + payload[5] * 256 + payload[4]
    elbin = payload[9]*65536 + payload[8] * 256 + payload[7]   
    az = azbin * 360 / (4*65536)
    el = elbin * 360 / (4*65536)
    return (az,el)


def pt5000_create_command_packet (cmd) :
    return bytearray([0x02,cmd,0,0, 0,0,0,0, 0,0])

#
# Create a command packet to move the gimbal.
# So far this works for azimuth (pan) move clockwise.
#
# Left pan: 02370808 F1BE03457C0004F09
# 02370808 F1BE 0345 7C00 04F0 || 93 2F || 64
#
def pt5000_create_joystick_packet (azspeed,elspeed) :
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

def pt5000_create_set_elspeed_packet (speed) :
    """
    Create command packet to set the default elevation (tilt) speed of the gimbal. Allowed values 0 to 8.
    """
    assert speed >= 0 and speed <= 8
    return bytearray([0x02,0x1b,0,speed, 0, 0, 0, 0, 0, 0])

def pt5000_create_set_azspeed_packet (speed) :
    """
    Create command packet to set the default azimuth (pan) speed of the gimbal. Allowed values 0 to 8.
    """
    assert speed >= 0 and speed <= 8
    return bytearray([0x02,0x1d,speed,0, 0, 0, 0, 0, 0, 0])
    
