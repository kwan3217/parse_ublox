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

ublox_names={
    0x05:("ACK",{0x01:"ACK",
                 0x00:"NAK"}),
    0x06:("CFG",{0x13:"ANT",
                 0x09:"CFG",
                 0x06:"DAT",
                 0x70:"DGNSS",
                 0x69:"GEOFENCE",
                 0x3e:"GNSS",
                 0x02:"INF",
                 0x39:"ITFM",
                 0x47:"LOGFILTER",
                 0x01:"MSG",
                 0x24:"NAV5",
                 0x23:"NAVX5",
                 0x17:"NMEA",
                 0x1e:"ODO",
                 0x00:"PRT",
                 0x57:"PWR",
                 0x08:"RATE",
                 0x34:"RINV",
                 0x04:"RST",
                 0x16:"SBAS",
                 0x71:"TMODE3",
                 0x31:"TP5",
                 0x1b:"USB",
                 0x8c:"VALDEL",
                 0x8b:"VALGET",
                 0x8a:"VALSET"}),
    0x0a:("MON",{0x04:"VER"}),
    0x29:("NAV2",{0x22:"CLOCK",
                  0x36:"COV",
                  0x04:"DOP",
                  0x61:"EOE",
                  0x09:"ODO",
                  0x01:"POSECEF",
                  0x02:"POSLLH",
                  0x07:"PVT",
                  0x35:"SAT",
                  0x32:"SBAS",
                  0x43:"SIG",
                  0x42:"SLAS",
                  0x03:"STATUS",
                  0x3b:"SVIN",
                  0x24:"TIMEBDS",
                  0x25:"TIMEGAL",
                  0x23:"TIMEGLO",
                  0x20:"TIMEGPS",
                  0x26:"TIMELS",
                  0x27:"TIMEQZSS",
                  0x21:"TIMEUTC",
                  0x11:"VELECEF",
                  0x12:"VELNED"}),
    0x02:("RXM",{0x34:"COR",
                 0x14:"MEASX",
                 0x72:"PMP",
                 0x41:"PMREQ",
                 0x73:"QZSSL6",
                 0x15:"RAWX",
                 0x59:"RLM",
                 0x32:"RTCM",
                 0x13:"SFRBX",
                 0x33:"SPARTN",
                 0x36:"SPARTNKEY"})
}

def print_ublox(packet):
    cls=packet[2]
    id=packet[3]
    length=len(packet)-10
    payload=packet[8:-2]
    clsname = f"0x{cls:02x}"
    idname = f"0x{id:02x}"
    if cls in ublox_names:
        clsname=ublox_names[cls][0]
        if id in ublox_names[cls][1]:
            idname=ublox_names[cls][1][id]
    name=f"UBX-{clsname}-{idname}"
    print(name)
    dump_bin(payload)


def main():
    with open("fluttershy_220331_150823.ubx","rb") as inf:
        while True:
            packet_type,packet=next_packet(inf)
            if packet_type==PacketType.NMEA:
                print(packet)
            elif packet_type==PacketType.UBLOX:
                print_ublox(packet)
                pass


if __name__=="__main__":
    main()
