"""
Code to parse a stream of data from a UBlox reveiver (not necessarily just UBlox packets)
and do useful things with the data.
"""
import struct
import traceback

from struct import unpack
from enum import Enum
from bin import dump_bin
from parse_l1ca_nav import parse_l1ca_subframe
from parse_rtcm import parse_rtcm
from parse_ublox import parse_ublox, print_ublox, GNSS


class PacketType(Enum):
    NMEA = 1
    UBLOX = 2
    RTCM = 3


def ublox_ck_valid(payload:bytes,ck_a:int,ck_b:int):
    """
    Check the checksum of a UBlox packet

    :param payload:
    :param ck_a:
    :param ck_b:
    :return:
    """
    return True


def nmea_ck_valid(packet:bytes,has_checksum):
    """
    Check the checksum of an NMEA packet

    :param packet:
    :return:
    """
    return True


def rtcm_ck_valid(packet:bytes):
    """
    Check the checksum of an RTCM packet

    :param packet:
    :return:
    """
    return True


def next_packet(inf,reject_invalid=True,nmea_max=None):
    """

    :param inf:
    :param reject_invalid:
    :param nmea_max:
    :return:
    """
    header_peek=inf.read(1)
    if header_peek[0]==ord('$'):
        #Looks like an NMEA packet, read until the asterisk
        result=header_peek
        while result[-1]!=ord('*'):
            result+=inf.read(1)
        #Read either 0D0A or checksum
        result+=inf.read(2)
        has_checksum=False
        if not (result[0]==0x0d and result[1]==0x0a):
            result+=inf.read(2)
            has_checksum=True
        if not reject_invalid or nmea_ck_valid(result,has_checksum):
            return PacketType.NMEA, str(result,encoding='cp437').strip()
        else:
            return None, None
    elif header_peek[0]==0xb5:
        #Start of UBlox header
        header=header_peek+inf.read(1)
        if header[1]==0x62:
            #Header is valid, read the entire packet
            header=header+inf.read(4)
            cls=header[2]
            id=header[3]
            length=unpack('<H',header[4:6])[0]
            payload=inf.read(length)
            ck=inf.read(2)
            if not reject_invalid or ublox_ck_valid(payload,ck[0],ck[1]):
                return PacketType.UBLOX, header+payload+ck
            else:
                #Checksum failed. Advanced past the whole packet, but packet is not returned.
                return None,None
        else:
            #Not a ublox packet. We wish we could push back, but won't for now. Know that
            #the stream has been advanced by two bytes. If there is a stray 0xb5 (mu) before
            #an actual packet, this will cause the packet to be missed.
            return None,None
    elif header_peek[0]==0xd3:
        # Start of RTCM packet. One byte preamble, two-byte big-endian length (only 10 ls bits
        # are significant), n-byte payload, three byte CRC
        #Start of UBlox header
        header=header_peek+inf.read(2)
        length=unpack('>H',header[1:3])[0] & 0x3ff
        payload=inf.read(length)
        ck=inf.read(3)
        if not reject_invalid or ublox_ck_valid(payload,ck[0],ck[1]):
            return PacketType.RTCM, header+payload+ck
        else:
            #Checksum failed. Advanced past the whole packet, but packet is not returned.
            return None,None
    else:
        # Not either kind of packet we can recognize. Return None, and know that the
        # data stream has had one byte consumed.
        return None,None


def main():
    with open("fluttershy_survey_in_220404_205357.ubx","rb") as inf:
        ofs=0
        while True:
            packet_type,packet=next_packet(inf)
            print(f"ofs: {ofs:08x}, pkt_len: {len(packet)}")
            ofs+=len(packet)
            if packet_type==PacketType.NMEA:
                print(packet)
            elif packet_type==PacketType.UBLOX:
                try:
                    parsed_packet=parse_ublox(packet)
                    print_ublox(parsed_packet)
                except struct.error:
                    traceback.print_exc()
                    dump_bin(packet)
            elif packet_type==PacketType.RTCM:
                try:
                    parsed_packet=parse_rtcm(packet,verbose=False)
                    print(parsed_packet)
                except AssertionError:
                    traceback.print_exc()
                    dump_bin(packet)


if __name__=="__main__":
    main()
