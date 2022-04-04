"""
Code to parse a stream of data from a UBlox reveiver (not necessarily just UBlox packets)
and do useful things with the data.
"""
import re
import struct
from collections import namedtuple
from functools import partial
from struct import unpack
from enum import Enum
import traceback

from parse_rtcm import parse_rtcm


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

class GNSS(Enum):
    GPS=0
    SBAS=1
    GAL=2
    BDS=3
    IMES=4
    QZSS=5
    GLO=6
    NavIC=7


class ANTSTAT(Enum):
    INIT=0
    DONTKNOW=1
    OK=2
    SHORT=3
    OPEN=4


class ANTPWR(Enum):
    OFF=0
    ON=1
    DONTKNOW=2


class LAYER(Enum):
    RAM=0
    BBR=1
    Flash=2
    Default=7


ublox_packets={
    0x05:("ACK",{0x01:("ACK",{"clsID":("U1",None,None,None),
                              "msgID":("U1",None,None,None)}),
                 0x00:("NAK",)}),
    0x06:("CFG",{0x13:("ANT",),
                 0x09:("CFG",),
                 0x06:("DAT",),
                 0x70:("DGNSS",),
                 0x69:("GEOFENCE",),
                 0x3e:("GNSS",),
                 0x02:("INF",),
                 0x39:("ITFM",),
                 0x47:("LOGFILTER",),
                 0x01:("MSG",),
                 0x24:("NAV5",),
                 0x23:("NAVX5",),
                 0x17:("NMEA",),
                 0x1e:("ODO",),
                 0x00:("PRT",),
                 0x57:("PWR",),
                 0x08:("RATE",),
                 0x34:("RINV",),
                 0x04:("RST",),
                 0x16:("SBAS",),
                 0x71:("TMODE3",),
                 0x31:("TP5",),
                 0x1b:("USB",),
                 0x8c:("VALDEL",),
                 0x8b:("VALGET",{"version":("U1",None,None,None),
                                 "layer":  ("U1",LAYER,None,"%20s"),
                                 "position":("U2",None,None,None),
                                 "cfgData[N]":("X1",None,None,None)}),
                 0x8a:("VALSET",)}),
    0x0a:("MON",{0x36:("COMMS",),
                 0x28:("GNSS",),
                 0x09:("HW",),
                 0x0b:("HW2",),
                 0x37:("HW3",),
                 0x02:("IO",),
                 0x06:("MSGPP",),
                 0x27:("PATCH",),
                 0x38:("RF",{"version":("U1",None,None,None),
                             "nBlocks":("U1",None,None,None),
                             "reserved0":  ("X2",None,None,None),
                             "blockId[N]": ("U1",None,None,None),
                             "flags[N]":   ("X1", None, None, None),
                             "antStatus[N]": ("U1", ANTSTAT, None, "%16s"),
                             "antPower[N]": ("U1", ANTPWR, None, "%16s"),
                             "postStatus[N]": ("X4", None, None, None),
                             "reserved1[N]": ("X4", None, None, None),
                             "noisePerMS[N]": ("U2", None, None, None),
                             "agcCnt[N]": ("U2", 1/8191, None, "%7.5f"),
                             "jamInd[N]": ("U1", 1/255, None, "%5.3f"),
                             "ofsI[N]": ("I1", 1/128, None, "%6.3f"),
                             "magI[N]": ("U1", 1/255, None, "%5.3f"),
                             "ofsQ[N]": ("I1", 1/128, None, "%6.3f"),
                             "magQ[N]": ("U1", 1/255, None, "%5.3f"),
                             "reserved2A[N]": ("U1", None, None, None),
                             "reserved2B[N]": ("U2", None, None, None),

                             }),
                 0x07:("RXBUF",),
                 0x21:("RXR",),
                 0x31:("SPAN",),
                 0x39:("SYS",),
                 0x08:("TXBUF",),
                 0x04:("VER",{"swVersion":("CH30",None,None,"%30s"),
                              "hwVersion":("CH10",None,None,"%10s"),
                              "extension[N]":("CH30",None,None,"%30s")}),
                 }),
    0x01:("NAV", {0x22:("CLOCK",),
                  0x36:("COV",),
                  0x04:("DOP",),
                  0x61:("EOE",),
                  0x39:("GEOFENCE",),
                  0x13:("HPPOSECEF",),
                  0x14:("HPPOSLLH",),
                  0x09:("ODO",),
                  0x01:("POSECEF",{"iTOW": ("U4",1e-3,"s","%10.3f"),
                                   "ecefX":("I4",1e-2,"m","%12.2f"),
                                   "ecefY":("I4",1e-2,"m","%12.2f"),
                                   "ecefZ":("I4",1e-2,"m","%12.2f"),
                                   "pAcc": ("U4",1e-2,"m","%12.2f")}),
                  0x02:("POSLLH",{"iTOW":("U4",1e-3,"s","%10.3f"),
                                  "lon":      ("I4",1e-7,"deg","%12.7f"),
                                  "lat":      ("I4",1e-7,"deg","%12.7f"),
                                  "height":   ("I4",1e-3,"m","%12.3f"),
                                  "hMSL":     ("I4",1e-3,"m","%12.3f"),
                                  "hAcc":     ("U4",1e-3,"m","%12.3f"),
                                  "vAcc":     ("U4",1e-3,"m","%12.3f")}),
                  0x07:("PVT",{"iTOW":     ("U4",1e-3,"s","%10.3f"),
                               "year":     ("U2",None,"y",None),
                               "month":    ("U1",None,"month",None),
                               "day":      ("U1",None,"d",None),
                               "hour":     ("U1",None,"h",None),
                               "min":      ("U1",None,"min",None),
                               "sec":      ("U1",None,"s",None),
                               "valid":    ("X1",None,None,None),
                               "tAcc":     ("U4",1e-9,"s","%12.9f"),
                               "nano":     ("I4",1e-9,"s","%12.9f"),
                               "fixType":  ("X1",None,None,None),
                               "flags":    ("X1",None,None,None),
                               "flags2":   ("X1",None,None,None),
                               "numSV":    ("U1",None,None,None),
                               "lon":      ("I4",1e-7,"deg","%12.7f"),
                               "lat":      ("I4",1e-7,"deg","%12.7f"),
                               "height":   ("I4",1e-3,"m","%12.3f"),
                               "hMSL":     ("I4",1e-3,"m","%12.3f"),
                               "hAcc":     ("U4",1e-3,"m","%12.3f"),
                               "vAcc":     ("U4",1e-3,"m","%12.3f"),
                               "velN":     ("I4",1e-3,"m/s","%12.3f"),
                               "velE":     ("I4",1e-3,"m/s","%12.3f"),
                               "velD":     ("I4",1e-3,"m/s","%12.3f"),
                               "gSpeed":   ("I4",1e-3,"m/s","%12.3f"),
                               "headMot":  ("I4",1e-5,"deg","%12.5f"),
                               "sAcc":     ("U4",1e-3,"m/s","%12.3f"),
                               "headAcc":  ("U4",1e-5,"deg","%12.5f"),
                               "pDOP":     ("U2",0.01,None,"%6.2f"),
                               "flags3":   ("X2",None,None,None),
                               "reserved0":("U4",None,None,None),
                               "headVeh":  ("I4",1e-5,"deg","%12.5f"),
                               "magDec":   ("I2",1e-5,"deg","%8.5f"),
                               }),
                  0x3c:("RELPOSNED",{"version":       ("U1",None,None,None),
                                     "reserved0":     ("X1",None,None,None),
                                     "refStationID":  ("U2",None,None,None),
                                     "iTOW":          ("U4",1e-3,"s","%10.3f"),
                                     "relPosN":       ("I4",1e-2,"m","%12.2f"),
                                     "relPosE":       ("I4",1e-2,"m","%12.2f"),
                                     "relPosD":       ("I4",1e-2,"m","%12.2f"),
                                     "relPosLength":  ("I4",1e-2,"m","%12.2f"),
                                     "relPosHeading": ("I4",1e-5,"deg","%12.5f"),
                                     "reserved1":     ("X4",None,None,None),
                                     "relPosHPN":     ("I1",1e-4,"m","%6.4f"),
                                     "relPosHPE":     ("I1",1e-4,"m","%6.4f"),
                                     "relPosHPD":     ("I1",1e-4,"m","%6.4f"),
                                     "relPosHPLength":("U1",1e-4,"m","%6.4f"),
                                     "accN":          ("U4",1e-4,"m","%12.4f"),
                                     "accE":          ("U4",1e-4,"m","%12.4f"),
                                     "accD":          ("U4",1e-4,"m","%12.4f"),
                                     "accLength":     ("U4",1e-4,"m","%12.4f"),
                                     "accHeading":    ("U4",1e-5,"deg","%12.5f"),
                                     "reserved2":     ("X4",None,None,None),
                                     "flags":         ("X4",None,None,None),
                                     }),
                  0x10:("RESETODO",),
                  0x35:("SAT",),
                  0x32:("SBAS",),
                  0x43:("SIG",),
                  0x42:("SLAS",),
                  0x03:("STATUS",),
                  0x3b:("SVIN",),
                  0x24:("TIMEBDS",),
                  0x25:("TIMEGAL",),
                  0x23:("TIMEGLO",),
                  0x20:("TIMEGPS",),
                  0x26:("TIMELS",),
                  0x27:("TIMEQZSS",),
                  0x21:("TIMEUTC",),
                  0x11:("VELECEF",),
                  0x12:("VELNED",)}),
    0x29:("NAV2",{0x22:("CLOCK",),
                  0x36:("COV",),
                  0x04:("DOP",),
                  0x61:("EOE",),
                  0x09:("ODO",),
                  0x34:("ORB",),
                  0x62:("PL",),
                  0x01:("POSECEF",),
                  0x02:("POSLLH",),
                  0x07:("PVT",),
                  0x35:("SAT",),
                  0x32:("SBAS",),
                  0x43:("SIG",),
                  0x42:("SLAS",),
                  0x03:("STATUS",),
                  0x3b:("SVIN",),
                  0x24:("TIMEBDS",),
                  0x25:("TIMEGAL",),
                  0x23:("TIMEGLO",),
                  0x20:("TIMEGPS",),
                  0x26:("TIMELS",),
                  0x27:("TIMEQZSS",),
                  0x21:("TIMEUTC",),
                  0x11:("VELECEF",),
                  0x12:("VELNED",)}),
    0x02:("RXM",{0x34:("COR",),
                 0x14:("MEASX",),
                 0x72:("PMP",),
                 0x41:("PMREQ",),
                 0x73:("QZSSL6",),
                 0x15:("RAWX",{"rcvTow":      ("R8",None,"s","%21.8f"),
                               "week":        ("U2",None,"weeks",None),
                               "leapS":       ("I1",None,"s",None),
                               "numMeas":     ("U1",None,None,None),
                               "recStat":     ("X1",None,None,None),
                               "version":     ("U1",None,None,None),
                               "reserved0":   ("X2",None,None,None),
                               "prMes[N]":    ("R8",None,"m","%21.8f"),
                               "cpMes[N]":    ("R8",None,"cycles","%21.8f"),
                               "doMes[N]":    ("R4",None,"Hz","%21.4f"),
                               "gnssId[N]":   ("U1",GNSS,None,"%10s"),
                               "svId[N]":     ("U1",None,None,None),
                               "sigId[N]":    ("U1",None,None,None),
                               "freqId[N]":   ("U1",None,None,None),
                               "locktime[N]": ("U2",1e-3,"s","%6.3f"),
                               "cno[N]":      ("U1",None,"dBHz",None),
                               "prStdev[N]":  ("U1",lambda n:0.01*2**n,"m","%10.2f"),
                               "cpStdev[N]":  ("U1",0.004,"cycles","%5.3f"),
                               "doStdev[N]":  ("U1",lambda n:0.002*2**n,"Hz","%10.3f"),
                               "trkStat[N]":  ("X1",None,None,None),
                               "reserved1[N]":("X1",None,None,None)
                               }),
                 0x59:("RLM",),
                 0x32:("RTCM",),
                 0x13:("SFRBX",{"gnssId":   ("U1",GNSS,None,"%10s"),
                                "svId":     ("U1",None,None,None),
                                "sigId":    ("U1",None,None,None),
                                "freqId":   ("U1",None,None,None),
                                "numWords": ("U1",None,None,None),
                                "chn":      ("U1",None,None,None),
                                "version":  ("U1",None,None,None),
                                "reserved0":("U1",None,None,None),
                                "dwrd[N]":  ("X4",None,None,"%08x")}),
                 0x33:("SPARTN",),
                 0x36:("SPARTNKEY",)})
}

def fmt_width(fmt):
    match=re.match("( *)[^1-9]*(\d+).*",fmt)
    return len(match.group(1))+int(match.group(2))

def fmt_set_width(fmt,width):
    match=re.match("(?P<spaces> *)(?P<prefix>[^1-9]*)(?P<sigwidth>\d+)(?P<suffix>.*)",fmt)
    old_width=int(match.group("sigwidth"))
    if width<old_width:
        return match.group("spaces")+match.group("prefix")+str(width)+match.group("suffix")
    else:
        return " "*(width-old_width)+match.group("prefix")+str(old_width)+match.group("suffix")


def compile(field_dict):
    """
    Compile a field_dict from the form that most closely matches the
    book to something more usable at runtime

    :param field_dict: Field dict to compile, keyed on field, value is tuple:
      * type in UBX form (UBX manual 3.3.5)
      * Scale, or None if not scaled
      * units, or None if no units
    :return: Tuple
      * b: number of bytes before repeating block
      * m: number of bytes in repeating block
      * c: number of bytes after repeating block
      * header_fields: string suitable for handing to namedtuple, representing all fields before repeating block, or None if none
      * header_type: string suitable for handing to struct.unpack, for fields before repeating block
      * header_scale: list of lambdas which scale the field for fields before repeating block
      * header_units: list of units for fields before repeating block
      * block_fields: string suitable for handing to namedtuple, representing all fields in repeating block, or None if none
      * block_type: string suitable for handing to struct.unpack, for fields in repeating block
      * block_scale: list of scales for fields in repeating block
      * block_units: list of units for fields in repeating block
      * footer_fields: string suitable for handing to namedtuple, representing all fields after repeating block, or None if none
      * footer_type: string suitable for handing to struct.unpack, for fields after repeating block
      * footer_scale: list of scales for fields after repeating block
      * footer_units: list of units for fields after repeating block

    At parse time, the number of repeats of the repeating block is determined as follows:

    d: full packet size
    n: number of repeats
    d=b+m*n+c
    d-b-c=m*n
    (d-b-c)/m=n
    """
    size_dict={"U1":("B",1,"%3d"),
               "U2":("H",2,"%5d"),
               "U4":("I",4,"%9d"),
               "I1":("b",1,"%4d"),
               "I2":("h",2,"%6d"),
               "I4":("i",4,"%10d"),
               "X1":("B",1,"%02x"),
               "X2":("H",2,"%04x"),
               "X4":("I",4,"%08x"),
               "R4":("f",4,"%14.7e"),
               "R8":("d",8,"%21.14e")}
    lengths=[0,0,0]
    fields=[[],[],[]]
    types=["","",""]
    scales=[[],[],[]]
    units=[[],[],[]]
    fmts=[[],[],[]]
    widths=[[],[],[]]
    part=0
    for field_name,(ublox_type,scale,unit,fmt) in field_dict.items():
        if "[N]" in field_name:
            if part==0:
                part=1
            field_name=field_name[:-3]
        else:
            if part==1:
                part=2
        fields[part].append(field_name)
        if ublox_type[0:2]=="CH":
            types[part]+=ublox_type[2:]+"s"
            lengths[part]+=int(ublox_type[2:])
        else:
            types[part]+=size_dict[ublox_type][0]
            lengths[part]+=size_dict[ublox_type][1]
        if scale is None:
            scales[part].append(lambda x:x)
        elif callable(scale):
            scales[part].append(scale)
        else:
            scales[part].append(partial(lambda s,x:s*x,scale))
        units[part].append(unit)
        if fmt is None:
            fmt=size_dict[ublox_type][2]
        if part==1:
            colhead_width=len(field_name)+(0 if unit is None else 3+len(unit))
            if fmt_width(fmt)<colhead_width:
                fmt=fmt_set_width(fmt,colhead_width)
        fmts[part].append(fmt)
        widths[part].append(fmt_width(fmt))
    b,m,c=lengths
    header_fields,block_fields,footer_fields=fields
    header_types,block_types,footer_types=["<"+x for x in types]
    header_scale,block_scale,footer_scale=scales
    header_units,block_units,footer_units=units
    header_format,block_format,footer_format=fmts
    header_widths,block_widths,footer_widths=widths
    return namedtuple("packet_desc","b m c hn ht hs hu hf hw bn bt bs bu bf bw fn ft fs fu ff fw")._make((b,m,c,
            header_fields,header_types,header_scale,header_units,header_format,header_widths,
            block_fields,block_types,block_scale,block_units,block_format,block_widths,
            footer_fields, footer_types, footer_scale, footer_units, footer_format,footer_widths))


def parse_ublox(packet):
    """
    Parse a ublox packet

    :param packet: bytes array containting full binary packet, including header and checksum
    :return: namedtuple with name set to name of packet (UBX-xxx-xxx format) and the following elements:
    * cls -- class of packet
    * id  -- ID of packet
    * n_rep -- number of times the repeating block in the packet repeats. Will be None if there is no repeating block.
    * one element for each field in the packet. Values will be converted (scaled, made into enum, etc)
      as indicated by the packet description. Fields in a repeating block are lists, one element for each repeat.
    """
    cls=packet[2]
    id=packet[3]
    length=len(packet)-8
    payload=packet[6:-2]
    clsname = f"0x{cls:02x}"
    idname = f"0x{id:02x}"
    packet_desc=None
    if cls in ublox_packets:
        clsname=ublox_packets[cls][0]
        if id in ublox_packets[cls][1]:
            idtuple=ublox_packets[cls][1][id]
            idname=idtuple[0]
            if len(idtuple)>1:
                packet_desc=compile(idtuple[1])
    name=f"UBX-{clsname}-{idname}"
    idname=f"UBX_{clsname}_{idname}"
    if packet_desc.b>0:
        unscaled_header=unpack(packet_desc.ht,payload[0:packet_desc.b])
        header=tuple([scale(field) for field,scale in zip(unscaled_header,packet_desc.hs)])
    else:
        header=tuple()
    if packet_desc.m>0:
        # The repeating blocks are represented in memory by a list of fields, each long enough to hold
        # one element for each repeat. Following the database convention, we will call the collection
        # of numbers which all mean the same thing for different repeats, a "column" or "field", and
        # the collection of numbers which all mean different things in the same repeat, a "row".
        d = len(payload)
        assert (d-packet_desc.b-packet_desc.c) % packet_desc.m == 0, "Non-integer number of rows"
        n_rows = (d - packet_desc.b - packet_desc.c) // packet_desc.m
        n_cols=len(packet_desc.bs)
        # in memory -- the blocks are a tuple of columns, each a list long enough to hold one member
        # for each row. This means each cell has a double index, the first one being the column index,
        # second being row. We do it this way so that we can concatenate it with the header and
        # footer tuple, and hand the combo right off to the _make() method of namedtuple.
        cols=tuple([[None for x in range(n_rows)] for y in range(n_cols)])
        for i_row in range(n_rows):
            unscaled_row=unpack(packet_desc.bt,payload[packet_desc.b+i_row*packet_desc.m:packet_desc.b+i_row*packet_desc.m+packet_desc.m])
            row=[scale(field) for field,scale in zip(unscaled_row,packet_desc.bs)]
            for i_col,element in enumerate(row):
                cols[i_col][i_row]=element
        if packet_desc.c>0:
            unscaled_footer = unpack(packet_desc.ft, payload[packet_desc.b+packet_desc.m*n_rows:])
            footer = tuple([scale(field) for field, scale in zip(unscaled_footer, packet_desc.hs)])
        else:
            footer = tuple()
    else:
        cols=tuple()
        footer=tuple()
        n_rows=0
    returntype=namedtuple(idname," ".join(packet_desc.hn+packet_desc.bn+packet_desc.fn)+" cls id name n_rep payload desc")
    return returntype._make(header+cols+footer+(cls,id,name,n_rows,payload,packet_desc))


def print_ublox(packet):
    print(packet.name)
    dump_bin(packet.payload)
    if len(packet.payload)==0:
        print("Null packet")
        return
    if packet.desc is not None:
        for i_header_field,(fieldname,unit,fmt) in enumerate(zip(packet.desc.hn,packet.desc.hu,packet.desc.hf)):
            i_field=i_header_field
            value=packet[i_field]
            print(f"{fieldname:>21s}: ",end='')
            print(fmt % value,end='')
            print(' '+unit if unit is not None else '')
        if packet.n_rep>0:
            print("  i", end='')
            for i_block_field,(fieldname,unit,width) in enumerate(zip(packet.desc.bn,packet.desc.bu,packet.desc.bw)):
                print(" "+(f"%-{width}s")%(fieldname+(' ('+unit+')' if unit is not None else '')),end='')
            print("")
            print("---",end='')
            for width in packet.desc.bw:
                print(" "+("-"*width),end='')
            print("")
            for i_row in range(packet.n_rep):
                print(f"{i_row:3d}",end='')
                for i_block_field, (unit,fmt) in enumerate(zip(packet.desc.bu,packet.desc.bf)):
                    i_field = i_block_field+len(packet.desc.hu)
                    value = packet[i_field][i_row]
                    print(" "+fmt % value,end='')
                print("")
            for i_footer_field,(fieldname,unit) in enumerate(zip(packet.desc.ff,packet.desc.fu)):
                i_field=len(packet.desc.hu)+len(packet.desc.bu)+i_footer_field
                value=packet[i_field]
                print(f"{fieldname:>21s}: ",end='')
                print(fmt % value,end='')
                print(' '+unit if unit is not None else '')
    else:
        raise ValueError(f"No packet description for {packet.name}")

# GPS L1C/A Nav Message description. Each field consists of:
# key is name of field
# value is tuple
#  * list of tuples, each indicating the start and end bit of a part of the value. Most fields
#    are contiguous, so there is only one entry in the list. If a field is discontiguous, each part
#    will be ordered in the list such that the more significant parts are earlier. Each tuple is the
#    start and end bits of the field part, numbered according to the ICD convention of bit 1 being
#    the most significant bit of dwrd[0], bit 31 being most significant of dwrd[1], etc. No part will
#    ever cross a word boundary (IE not something like 25,35) because the parity bits always delimit
#    each word. Starts and ends are inclusive (unlike Python in general, where start is included but
#    end is not). So, the preamble is bits 1-8, and should always be the preamble value 0x8B.
#  * True if value is twos-complement signed, False if unsigned
#  * Scaling factor or function, or None if the scaling is identity.
#  * Physical units of scaled value, or None if there are none.
#  * Recommended format string, suitable for the % operator.
#
tlm_struct={
    "preamble":([(1,8)],False,None,None,"%02x"),
    "tlm":([(9,22)],False,None,None,"%04x"),
    "integ_stat":([(24,24)],False,None,None,"%01x"),
}

how_struct={
    "tow_count":([(31,47)],False,None,None,None),
    "alert":([(48,48)],False,None,None,None),
    "antispoof":([(49,49)],False,None,None,None),
    "subframe":([(50,52)],False,None,None,None),
}

def ura_nom(N):
    if N==1:
        return 2.8
    if N==3:
        return 5.7
    if N==5:
        return 11.3
    if N==15:
        return float('inf')
    if N<=6:
        return 2**(1+N/2)
    return 2**(N-2)

subframe_123={
    1:{**tlm_struct,**how_struct,
        "wn":([(61,70)],False,None,"week",None),
        "msg_on_l2":([(71,72)],False,None,None,None),
        "ura":([(73,76)],False,ura_nom,None,None),
        "sv_health":([(77,82)],False,None,None,None),
        "iodc":([(83,84),(211,218)],False,None,None,None),
        "t_gd":([(197,197+8-1)],True,2**-31,"s",None),
        "t_oc":([(219,219+16-1)],False,2**4,"s",None),
        "a_f2":([(241,241+8-1)],True,2**-55,"s/s**2",None),
        "a_f1":([(241+8,241+8+16-1)],True,2**-43,"s/s",None),
        "a_f0":([(271,271+22-1)],True,2**-31,"s",None)
    },
    2:{**tlm_struct,**how_struct,
        "iode":([(61,68)],False,None,"week",None),
        "c_rs":([(69,69+16-1)],True,2**-5,"m",None),
        "delta_n":([(91,106)],True,2**-43,"semicircle/s",None),
        "M_0":([(107,107+8-1),(121,121+24-1)],True,2**-31,"semicircle",None),
        "c_uc":([(151,166)],True,2**-29,"rad",None),
        "e":([(167,167+8-1),(181,181+24-1)],False,2**-33,None,None),
        "c_us":([(211,226)],True,2**-29,"rad",None),
        "A":([(227,227+8-1),(241,241+24-1)],False,lambda sqrtA:(sqrtA*2**-19)**2,"m",None),
        "t_oe":([(271,286)],False,2**4,"s",None),
        "fit":([(287,287)],False,None,None,None),
        "aodo": ([(288,288+5-1)], False,None,None,None),
    },
}


def parse_gps_sfrbx(packet):
    def get_bits(dwrd, b0, b1):
        dwrd_i = (b0 - 1) // 30
        rel_0 = b0 - (dwrd_i) * 30
        rel_1 = b1 - (dwrd_i) * 30
        width = rel_1 - rel_0 + 1
        shift = 30 - rel_1
        mask = (1 << width) - 1
        return (dwrd[dwrd_i] >> shift) & mask
    def get_multi_bits(dwrd, parts, signed):
        result = 0
        width = 0
        for (b0, b1) in parts:
            result = result << (b1 - b0 + 1)
            result = result | get_bits(dwrd, b0, b1)
            width += (b1 - b0 + 1)
        if signed:
            cutoff = 1 << (width - 1)
            if result >= cutoff:
                result -= 2 * cutoff
        return result
    names=[]
    values=[]
    subframe=get_bits(packet.dwrd,50,52)
    if subframe==2:
        print(2)
    if subframe in subframe_123:
        for name,(parts,signed,scale,units,fmt) in subframe_123[subframe].items():
            names.append(name)
            value=get_multi_bits(packet.dwrd,parts,signed)
            if callable(scale):
                value=scale(value)
            elif scale is not None:
                value=scale*value
            values.append(value)
        return namedtuple(f"subframe{subframe}", " ".join(names))._make(values)
    else:
        return None

def main():
    with open("fluttershy_rtcm3_220404_181911.ubx","rb") as inf:
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
                    if (parsed_packet.name=="UBX-RXM-SFRBX") and (parsed_packet.gnssId==GNSS.GPS) and (parsed_packet.sigId==0):
                        parsed_subframe=parse_gps_sfrbx(parsed_packet)
                        print(parsed_subframe)
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
