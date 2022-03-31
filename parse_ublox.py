"""
Code to parse a stream of data from a UBlox reveiver (not necessarily just UBlox packets)
and do useful things with the data.
"""
from struct import unpack
from enum import Enum

class PacketType(Enum):
    NMEA = 1
    UBLOX = 2


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
    else:
        # Not either kind of packet we can recognize. Return None, and know that the
        # data stream has had one byte consumed.
        return None,None


        #  x0    x1    x2    x3    x4    x5    x6    x7    x8    x9    xa    xb    xc    xd    xe    xf
low_sub=('\u2400\u263A\u263b\u2665\u2666\u2663\u2660\u2022\u25d8\u25cb\u25d9\u2642\u2640\u266a\u266b\u263c'+
         '\u25ba\u25c4\u2195\u203c\u00b6\u00a7\u25ac\u21a8\u2191\u2193\u2192\u2190\u221f\u2194\u25b2\u25bc\u2420')


def dump_bin(buf,word_len=4, words_per_line=8):
    line_len = word_len * words_per_line
    for i_line in range((len(buf) // line_len)+1):
        i_line0 = i_line * line_len
        i_line1 = (i_line + 1) * line_len
        print(f"{i_line0:04x} - ", end='')
        for i_byte_in_line, i_byte in enumerate(range(i_line0, i_line1)):
            if i_byte<len(buf):
                print(f"{buf[i_byte]:02x}",end='')
            else:
                print("  ",end='')
            if (i_byte_in_line + 1) % 4 == 0:
                print(" ", end='')
        print("|",end='')
        for i_byte_in_line, i_byte in enumerate(range(i_line0, i_line1)):
            if i_byte < len(buf):
                if buf[i_byte]<len(low_sub):
                    print(low_sub[buf[i_byte]],end='')
                else:
                    print(str(buf[i_byte:i_byte+1],encoding='iso8859-1'),end='')
            else:
                print(" ",end='')
        print("")


def main():
    with open("fluttershy_220331_150823.ubx","rb") as inf:
        while True:
            packet_type,packet=next_packet(inf)
            if packet_type==PacketType.NMEA:
                print(packet)
            elif packet_type==PacketType.UBLOX:
                dump_bin(packet)
                pass


if __name__=="__main__":
    main()
