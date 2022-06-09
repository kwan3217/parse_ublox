import re
from collections import namedtuple
from enum import Enum
from functools import partial
from struct import unpack

from bin import dump_bin
from parse_l1ca_nav import parse_l1ca_subframe


class GNSS(Enum):
    GPS=0
    SBAS=1
    GAL=2
    BDS=3
    IMES=4
    QZSS=5
    GLO=6
    NavIC=7


class GPS_SigID(Enum):
    L1CA=0
    L2CL=3
    L2CM=4
    L5I=6
    L5Q=7


class SBAS_SigID(Enum):
    L1CA=0


class GAL_SigID(Enum):
    E1C=0
    E1B=1
    E5AI=3
    E5AQ=4
    E5BI=5
    E5BQ=6


class BDS_SigID(Enum):
    B1D1=0
    B1D2=1
    B2D1=2
    B2D2=3
    B1C=5
    B2A=7


class QZSS_SigID(Enum):
    L1CA=0
    L1S=1
    L2CM=4
    L2CL=5
    L5I=8
    I5Q=9


class GLO_SigID(Enum):
    L1OF=0
    L2OF=2


class NavIC_SigID(Enum):
    L5A=0


SIGID={
    GNSS.GPS: GPS_SigID,
    GNSS.SBAS: SBAS_SigID,
    GNSS.GAL: GAL_SigID,
    GNSS.BDS: BDS_SigID,
    GNSS.QZSS: QZSS_SigID,
    GNSS.GLO: GLO_SigID,
    GNSS.NavIC: NavIC_SigID,
}


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


class QIND(Enum):
    NOSIG=0
    SEARCH=1
    ACQ=2
    DET_UNU=3
    CODE_SYNC=4
    CODE_CAR_SYNC5=5
    CODE_CAR_SYNC6=6
    CODE_CAR_SYNC7=7


class CSRC(Enum):
    NONE=0
    SBAS=1
    BDS=2
    RTCM2=3
    RTCM3_OSR=4
    RTCM3_SSR=5
    QZSS=6
    SPARTN=7
    CLAS=8


class IONO(Enum):
    NONE=0
    KLOBUCHAR_GPS=1
    SBAS=2
    KLOBUCHAR_BDS=3
    DUAL_FREQ=8


class FIX(Enum):
    NONE=0
    DR_ONLY=1
    TWOD=2
    THREED=3
    GPS_DR=4
    TIME=5


class RESET(Enum):
    WDOG=0
    SW=1
    SW_GNSS=2
    HW_SHUTDN=4
    GNSS_STOP=8
    GNSS_START=9


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
                 0x04:("RST",{
                     "navBbrMask":("X2",None,None,None),
                     "resetMode":("U1",RESET,None,"%20s"),
                     "reserved0":("X1",None,None,None)
                 }),
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
                  0x43:("SIG",{
                      "iTOW": ("U4", 1e-3, "s", "%10.3f"),
                      "version":("U1",None,None,None),
                      "numSigs":("U1",None,None,None),
                      "reserved0":("X2",None,None,None),
                      "gnssId[N]": ("U1", GNSS, None, "%10s"),
                      "svId[N]": ("U1", None, None, None),
                      "sigId[N]": ("U1", None, None, "%15s"),
                      "freqId[N]": ("U1", None, None, None),
                      "prRes[N]": ("I2",1e-1,"m","%5.1f"),
                      "cno[N]":   ("U1",None,"dBHz",None),
                      "qualityInd[N]": ("U1",QIND,None,"%20s"),
                      "corrSource[N]": ("U1", CSRC, None, "%20s"),
                      "ionoModel[N]": ("U1", IONO, None, "%20s"),
                      "sigFlags[N]":("X2",None,None,None),
                      "reserved1[N]":("X4",None,None,None),
                  }),
                  0x42:("SLAS",),
                  0x03:("STATUS",{
                      "iTOW": ("U4", 1e-3, "s", "%10.3f"),
                      "gpsFix":("U1",FIX,None,"%20s"),
                      "flags":("X1",None,None,None),
                      "fixStat":("X1",None,None,None),
                      "flags2":("X1",None,None,None),
                      "ttff":("U4",1e-3,"s","%12.3f"),
                      "msss": ("U4", 1e-3, "s", "%12.3f"),
                  }),
                  0x3b:("SVIN",{
                      "version":("U1",None,None,None),
                      "reserved0A":("X1",None,None,None),
                      "reserved0B":("X2",None,None,None),
                      "iTOW": ("U4", 1e-3, "s", "%10.3f"),
                      "dur": ("U4", None, "s", None),
                      "meanX":("I4",1e-2,"m","%12.2f"),
                      "meanY":("I4", 1e-2, "m", "%12.2f"),
                      "meanZ":("I4", 1e-2, "m", "%12.2f"),
                      "meanXHP": ("I1", 1e-4, "m", "%7.4f"),
                      "meanYHP": ("I1", 1e-4, "m", "%7.4f"),
                      "meanZHP": ("I1", 1e-4, "m", "%7.4f"),
                      "reserved1": ("X1", None, None, None),
                      "meanAcc": ("U4", 1e-4, "m", "%12.4f"),
                      "obs": ("U4", None, None, None),
                      "valid": ("U1", bool, None, None),
                      "active": ("U1", bool, None, None),
                      "reserved2": ("X2", None, None, None),
                  }),
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
                               "sigId[N]":    ("U1",None,None,"%15s"),
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
                                "sigId":    ("U1",None,None,"%20s"),
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
        header=[scale(field) for field,scale in zip(unscaled_header,packet_desc.hs)]
        if "gnssId" in packet_desc.hn and "sigId" in packet_desc.hn:
            gnssId = header[packet_desc.hn.index("gnssId")]
            sigId = header[packet_desc.hn.index("sigId")]
            sigId=SIGID[gnssId](sigId)
            header[packet_desc.hn.index("sigId")]=sigId
        header=tuple(header)
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
        if "gnssId" in packet_desc.bn and "sigId" in packet_desc.bn:
            for i_row in range(n_rows):
                gnssId = cols[packet_desc.bn.index("gnssId")][i_row]
                sigId =  cols[packet_desc.bn.index("sigId" )][i_row]
                sigId=SIGID[gnssId](sigId)
                cols[packet_desc.bn.index("sigId")][i_row]=sigId
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
    result=returntype._make(header+cols+footer+(cls,id,name,n_rows,payload,packet_desc))
    if (result.name == "UBX-RXM-SFRBX") and (result.gnssId == GNSS.GPS) and (result.sigId == 0):
        subframe,sfu,sff= parse_l1ca_subframe(result)
        if subframe is not None:
            returntype=namedtuple(f"{idname}_L1CA{subframe.subframe}"," ".join(tuple(packet_desc.hn)+subframe._fields)+" cls id name n_rep payload desc")
            packet_desc=packet_desc._replace(hn=packet_desc.hn+list(subframe._fields),
                                             hu=packet_desc.hu+sfu,
                                             hf=packet_desc.hf+sff,
                                             bn=[],bt='<',bs=[],bu=[],bf=[],m=0)
            result=returntype._make(header+subframe+(cls,id,name,0,payload,packet_desc))
    return result


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

