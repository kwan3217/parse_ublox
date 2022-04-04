from collections import namedtuple
from enum import Enum


class GLOdow(Enum):
    SUN=0
    MON=1
    TUE=2
    WED=3
    THU=4
    FRI=5
    SAT=6
    UNK=7


df_entry=namedtuple("df_entry","name bits signed scale unit fmt")


df_table={
# DFxxx                   name          bits  signed  scale  units  fmt
      2:  df_entry._make(("msgNum",     12,  False,   None,  None,  None)),
      3:  df_entry._make(("staId",      12,  False,   None,  None,  None)),
     21:  df_entry._make(("ITRFyear",    6,  False,   None,  None,  None)),
     22:  df_entry._make(("GPSind",      1,  False,   bool,  None,  None)),
     23:  df_entry._make(("GLOind",      1,  False,   bool,  None,  None)),
     24:  df_entry._make(("GALind",      1,  False,   bool,  None,  None)),
    141:  df_entry._make(("refind",      1,  False,   bool,  None,  None)),
     25:  df_entry._make(("ecefX",      38,   True, 0.0001,   "m",  None)),
    142:  df_entry._make(("SROscInd",    1,  False,   bool,  None,  None)),
      1:  df_entry._make(("res",         1,  False,   None,  None,  None)),
     26:  df_entry._make(("ecefY",      38,   True, 0.0001,   "m",  None)),
    364:  df_entry._make(("qcind",       2,  False,   None,  None,  None)),
     27:  df_entry._make(("ecefZ",      38,   True, 0.0001,   "m",  None)),
    405:  df_entry._make(("finePRext",  20,   True, 2**-29,  "ms",  None)),
    406:  df_entry._make(("finePhRext", 24,   True, 2**-31,  "ms",  None)),
    407:  df_entry._make(("lockTime",   10,  False,   None,  None,  None)),
    420:  df_entry._make(("hcAmbFlag",   1,  False,   bool,  None,  None)),
    408:  df_entry._make(("CNRext",     10,  False,  2**-4,"dbHz",  None)),
    404:  df_entry._make(("finedPhR",   15,   True, 0.0001, "m/s",  None)),
      4:  df_entry._make(("gpsTow",     30,  False,   None,  "ms",  None)),
    393:  df_entry._make(("mult_msg",    1,  False,   bool,  None,  None)),
    409:  df_entry._make(("iods",        3,  False,   None,  None,  None)),
    411:  df_entry._make(("cksteerind",  2,  False,   None,  None,  None)),
    412:  df_entry._make(("extckind",    2,  False,   None,  None,  None)),
    417:  df_entry._make(("dfsmoothind", 1,  False,   bool,  None,  None)),
    418:  df_entry._make(("gnsssmoothind",3, False,   None,  None,  None)),
    394:  df_entry._make(("satmask",    64,  False,   None,  None,  None)),
    395:  df_entry._make(("sigmask",    32,  False,   None,  None,  None)),
    396:  df_entry._make(("cellmask",    0,  False,   None,  None,  None)), #variable size
    397:  df_entry._make(("roughrangeint",8, False,   None,  "ms",  None)),
    398:  df_entry._make(("roughrangesub",10,False, 2**-10,  "ms",  None)),
    399:  df_entry._make(("roughdphr",  14,   True,   None, "m/s",  None)),
    416:  df_entry._make(("glodow",      3,  False, GLOdow,  None,  None)),
     34:  df_entry._make(("glotk",      27,  False,   None,  "ms",  None)),
    419:  df_entry._make(("glocha",      4,  False,   None,  None,  None)),
    248:  df_entry._make(("galTow",     30,  False,   None,  "ms",  None)),
}


class GPSSigID(Enum):
    L1CA=2
    L1P=3
    L1Z=4
    L2CA=8
    L2P=9
    L2Z=10
    L2CM=15
    L2CL=16
    L2CML=17
    L5I=22
    L5Q=23
    L5IQ=24


class GLOSigID(Enum):
    G1CA=2
    G1P=3
    G2CA=8
    G2P=9


class GALSigID(Enum):
    E1C=2
    E1A=3
    E1B=4
    E1BC=5
    E1ABC=6
    E6C=8
    E6A=9
    E6B=10
    E6BC=11
    E6ABC=12
    E5BI=14
    E5BQ=15
    E5BIQ=16
    E5ABI=18
    E5ABQ=19
    E5ABIQ=20
    E5AI=22
    E5AQ=23
    E5AIQ=24

MSM_header=[[2,3],[393,409,-7,411,412,417,418,394,395]]
MSM7_sat_record=[[397],[398,399]]
MSM7_sig_record=[405,406,407,420,408,404]


MSM7_ids={
    1077:((4,),(-4,),GPSSigID),
    1087:((416,34),(419,),GLOSigID),
    1097:((248,),(-4,),GALSigID),
}

rtcm_table={
    1005:("statARP","Stationary RTK Reference Station ARP",0,[2,3,21,22,23,24,141,25,142,-1,26,364,27]),
}

def get_bigend_bits(payload, b0, length, signed, verbose):
    """
    Get an arbitrary-width bitfield from a stream of bytes, interpreting all fields as big-endian.
    :param payload: Array of bytes to read from
    :param b0: Start byte position, MSB of byte 0 is bit 0
    :param length: Number of bytes to read
    :param signed: True if the number is interpreted as a signed two's complement value
    :return: integer value
    """
    b1 = b0 + length - 1
    done = False
    result = 0
    while not done:
        B0 = b0 // 8  # Byte that bit 0 is in
        B1 = b1 // 8  # Byte that bit 1 is in
        if B1 > B0:  # Not on the last byte yet
            bb0 = b0 % 8  # starting point in current byte
            bb1 = 7  # end of current byte
        else:
            bb0 = b0 % 8
            bb1 = b1 % 8
        width = bb1 - bb0 + 1
        mask = (1 << width)-1
        shift=7-bb1
        result<<=width
        this_result=(payload[B0]>>shift) & mask
        result=result|this_result
        b0=(B0+1)*8
        done=(b0>=b1)
    signed_result = result
    if signed:
        cutoff=1<<(length-1)
        if result>cutoff:
            signed_result=result-2*cutoff
    if verbose: print(f"{signed_result:d}  0x{result:x}  {result:0{length}b}")
    return signed_result


def parse_rtcm_field(payload,bitPos,df,verbose):
    if df<0:
        if verbose: print(f"payload bitpos: {bitPos:4d}   reserved")
        value = get_bigend_bits(payload, bitPos, -df, False, verbose)
        bitPos -= df  # advance (subtract a negative number of) bits
        name,value,unit,fmt=None,None,None,None
    else:
        (name, bits, signed, scale, unit, fmt) = df_table[df]
        if verbose: print(f"payload bitpos: {bitPos:4d}   width: {bits:2d}  name: {name}   ")
        value = get_bigend_bits(payload, bitPos, bits, signed, verbose)
        bitPos += bits
        if callable(scale):
            value = scale(value)
        elif scale is not None:
            value = scale * value

    return name,value,unit,fmt,bitPos


def popcount(bitmask):
    count=0
    while bitmask!=0:
        count=count+(bitmask & 1)
        bitmask=bitmask>>1
    return count


def enum_bits(bitmask,width):
    result=[]
    while bitmask!=0:
        if (bitmask & 1):
            result.append(width)
        bitmask=bitmask>>1
        width-=1
    return sorted(result)


def parse_msm7(payload, msgNum, verbose):
    times,satext,sigID=MSM7_ids[msgNum]
    names = []
    values = []
    units = []
    fmts = []
    bitPos=0
    for df in MSM_header[0]:
        name, value, unit, fmt, bitPos = parse_rtcm_field(payload, bitPos, df, verbose)
        if name is not None:
            names.append(name)
            values.append(value)
            units.append(unit)
            fmts.append(fmt)
    for df in times:
        name, value, unit, fmt, bitPos = parse_rtcm_field(payload, bitPos, df, verbose)
        if name is not None:
            names.append(name)
            values.append(value)
            units.append(unit)
            fmts.append(fmt)
    for df in MSM_header[1]:
        name, value, unit, fmt, bitPos = parse_rtcm_field(payload, bitPos, df, verbose)
        if name is not None:
            names.append(name)
            values.append(value)
            units.append(unit)
            fmts.append(fmt)
    satmask=values[names.index("satmask")]
    sigmask=values[names.index("sigmask")]
    Nsig=popcount(sigmask)
    Nsat=popcount(satmask)
    X=Nsig*Nsat
    hdrBits=169+X
    prns=enum_bits(satmask,64)
    sigs=[sigID(x) for x in enum_bits(sigmask,32)]
    # DF396 - GNSS Cell Mask
    Ncell=0
    cellmask={}
    cells=[]
    for prn in prns:
        col=get_bigend_bits(payload, bitPos, Nsig, False, verbose)
        bitPos+=Nsig
        this_sigs=enum_bits(col,Nsig)
        for sig in this_sigs:
            cells.append((prn,sigs[sig-1]))
        cellmask[prn]=sigs
        Ncell+=popcount(col)
    # Satellite records
    for df in MSM7_sat_record[0]:
        value={}
        for prn in prns:
            name, value[prn], unit, fmt, bitPos = parse_rtcm_field(payload, bitPos, df, verbose)
        if name is not None:
            names.append(name)
            values.append(value)
            units.append(unit)
            fmts.append(fmt)
    for df in satext:
        value={}
        for prn in prns:
            name, value[prn], unit, fmt, bitPos = parse_rtcm_field(payload, bitPos, df, verbose)
        if name is not None:
            names.append(name)
            values.append(value)
            units.append(unit)
            fmts.append(fmt)
    for df in MSM7_sat_record[1]:
        value={}
        for prn in prns:
            name, value[prn], unit, fmt, bitPos = parse_rtcm_field(payload, bitPos, df, verbose)
        if name is not None:
            names.append(name)
            values.append(value)
            units.append(unit)
            fmts.append(fmt)
    # Signal records
    for df in MSM7_sig_record:
        value={}
        for cell in cells:
            name, value[cell], unit, fmt, bitPos = parse_rtcm_field(payload, bitPos, df, verbose)
        if name is not None:
            names.append(name)
            values.append(value)
            units.append(unit)
            fmts.append(fmt)
    return namedtuple(f"msg{values[names.index('msgNum')]:04d}",
                      " ".join(names)+" units fmts")._make(tuple(values)+(units,fmts))


def parse_rtcm(packet, verbose=False):
    payload=packet[3:-3]
    msgNum=get_bigend_bits(payload,0,12,False, verbose)
    if msgNum in MSM7_ids:
        return parse_msm7(payload, msgNum, verbose)
    bitPos=0
    if msgNum in rtcm_table:
        name, desc, repeat, dfs=rtcm_table[msgNum]
        names = []
        values = []
        units = []
        fmts = []
        for df in dfs:
            name, value, unit, fmt, bitPos=parse_rtcm_field(payload,bitPos,df,verbose)
            if name is not None:
                names.append(name)
                values.append(value)
                units.append(unit)
                fmts.append(fmt)
        return namedtuple(f"msg{msgNum:04d}"," ".join(names)+" units fmts")._make(tuple(values)+(units,fmts))
    else:
        return None


if __name__ == "__main__":
    print("%03x" % get_bigend_bits(b'\x12\x34\x56',  0, 12, False, True))
    print("%04x" % get_bigend_bits(b'\x12\x34\x56',  4, 16, False, True))
    print("%03x" % get_bigend_bits(b'\x12\x34\x56', 12, 12, False, True))
