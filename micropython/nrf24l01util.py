#from nrf24l01 import *

# Required according to nRF24L01 datasheet to enable extra features
#
#This write command followed by data 0x73 acti-
#vates the following features:
#• R_RX_PL_WID
#• W_ACK_PAYLOAD
#• W_TX_PAYLOAD_NOACK
#A new ACTIVATE command with the same data
#deactivates them again. This is executable in
#power down or stand by modes only.
#The R_RX_PL_WID, W_ACK_PAYLOAD, and
#W_TX_PAYLOAD_NOACK features registers are
#initially in a deactivated state; a write has no
#effect, a read only results in zeros on MISO. To
#activate these registers, use the ACTIVATE com-
#mand followed by data 0x73. Then they can be
#accessed as any other register in nRF24L01. Use
#the same command and data to deactivate the
#registers again.

def activate_features(nrf):
    nrf.cs(0)
    nrf.spi.write(bytearray([0x50, 0x73]))  # ACTIVATE command
    nrf.cs(1)
    
def enable_ack_payload(nrf, pipes=0x01):
    nrf.reg_write(0x1D, 0x06)       # FEATURE: EN_DPL | EN_ACK_PAY
    nrf.reg_write(0x1C, pipes)      # DYNPD: enable dynamic payload on specified pipes
    
def load_ack(nrf, pipe, payload):
    assert 0 <= pipe <= 5
    assert len(payload) <= 32
    nrf.csn(0)
    nrf.spi.write(bytearray([0xA8 | pipe]))
    nrf.spi.write(payload)
    nrf.csn(1)

def print_registers (nrf) :
    for i in range(0x1e) :
        print (f"reg[{i:02X}] = {nrf.reg_read(i):02X}")
    
def buf_to_hex (buf) :
    hex = ""
    for i in range (len(buf)) :
        hex += f"{buf[i]:02X}"
    return hex;

def remove_first_n_bits(data, n_bits):
    # Convert each byte to 8-bit binary string and concatenate
    bit_str = ''
    for byte in data:
        bit_str += '{:08b}'.format(byte)

    # Remove the first n bits
    sliced_bits = bit_str[n_bits:]

    # Pad with zeros to make the length a multiple of 8
    pad_len = (8 - (len(sliced_bits) % 8)) % 8
    sliced_bits += '0' * pad_len

    # Convert back to bytes
    result = bytearray()
    for i in range(0, len(sliced_bits), 8):
        byte = int(sliced_bits[i:i+8], 2)
        result.append(byte)

    return result

def build_nrf24_air_packet(payload, pid=0, no_ack=0, crc_len=2):
    assert 0 <= len(payload) <= 32
    assert 0 <= pid <= 3
    assert no_ack in (0, 1)
    assert crc_len in (0, 1, 2)


    buf = bytearray (len(payload) + 2)

    length = len(payload)
    inverted_len = (~length) & 0x3F
    
    buf[0] = inverted_len << 2 | pid;
    buf[1] = no_ack << 7 | payload[0]>>1;
    
    for i in range(len(payload)-1) :
        buf[i+2] = (payload[i]<<7) | (payload[i+1]>>1)
        #buf[i+2] = 0x99

    return buf


def build_nrf24_packet(payload, pid=0, no_ack=0, crc_len=2):
    assert 0 <= len(payload) <= 32, "Payload must be 0–32 bytes"
    assert 0 <= pid <= 3, "PID must be 2-bit (0–3)"
    assert no_ack in (0, 1), "NO_ACK must be 0 or 1"
    assert crc_len in (0, 1, 2), "CRC length must be 0, 1, or 2"

    length = len(payload)
    inverted_len = (~length) & 0x3F  # 6-bit bitwise NOT
    packet_control = (no_ack << 6) | (pid << 4) | inverted_len
    packet = bytearray([packet_control]) + bytearray(payload)

    # Optionally append CRC
    if crc_len:
        crc = crc16_ccitt(packet)  # returns 16-bit int
        if crc_len == 1:
            packet.append(crc & 0xFF)
        elif crc_len == 2:
            packet += bytes([(crc >> 8) & 0xFF, crc & 0xFF])

    return packet

def crc16_ccitt(data, poly=0x1021, init_val=0xFFFF):
    crc = init_val
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
            crc &= 0xFFFF  # Ensure 16-bit
    return crc



