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
from collections import namedtuple

tlm_struct={
    "preamble":([(1,8)],False,None,None,"%02x"),
    "tlm":([(9,22)],False,None,None,"%04x"),
    "integ_stat":([(24,24)],False,None,None,"%01x"),
}

how_struct={
    "tow_count":([(31,47)],False,None,None,"%6d"),
    "alert":([(48,48)],False,bool,None,"%20s"),
    "antispoof":([(49,49)],False,bool,None,"%20s"),
    "subframe":([(50,52)],False,None,None,"%1d"),
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
        "wn":([(61,70)],False,None,"week","%4d"),
        "msg_on_l2":([(71,72)],False,None,None,"%1x"),
        "ura":([(73,76)],False,ura_nom,None,"%6.1f"),
        "sv_health":([(77,82)],False,None,None,"%2x"),
        "iodc":([(83,84),(211,218)],False,None,None,"%5d"),
        "t_gd":([(197,197+8-1)],True,2**-31,"s","%21.14e"),
        "t_oc":([(219,219+16-1)],False,2**4,"s","%21.14e"),
        "a_f2":([(241,241+8-1)],True,2**-55,"s/s**2","%21.14e"),
        "a_f1":([(241+8,241+8+16-1)],True,2**-43,"s/s","%21.14e"),
        "a_f0":([(271,271+22-1)],True,2**-31,"s","%21.14e")
    },
    2:{**tlm_struct,**how_struct,
        "iode":([(61,68)],False,None,None,"%3d"),
        "c_rs":([(69,69+16-1)],True,2**-5,"m","%8.5e"),
        "delta_n":([(91,106)],True,2**-43,"semicircle/s","%8.5e"),
        "M_0":([(107,107+8-1),(121,121+24-1)],True,2**-31,"semicircle","%8.5e"),
        "c_uc":([(151,166)],True,2**-29,"rad","%8.5e"),
        "e":([(167,167+8-1),(181,181+24-1)],False,2**-33,None,"%21.14e"),
        "c_us":([(211,226)],True,2**-29,"rad","%8.5e"),
        "A":([(227,227+8-1),(241,241+24-1)],False,lambda sqrtA:(sqrtA*2**-19)**2,"m","%21.6f"),
        "t_oe":([(271,286)],False,2**4,"s","%12d"),
        "fit":([(287,287)],False,None,None,"%1d"),
        "aodo": ([(288,288+5-1)], False,900,"s","%5d"),
    },
    3: {**tlm_struct, **how_struct,
        "c_ic": ([(61, 77-1)], True, 2**-29, "rad", "%8.5e"),
        "Omega_0": ([(77,77+8-1),(91,91+24-1)], True, 2 ** -31, "semicircle", "%17.10e"),
        "c_is": ([(121, 137-1)], True, 2 ** -29, "rad", "%8.5e"),
        "i_0": ([(137, 137 + 8 - 1), (151, 151 + 24 - 1)], True, 2 ** -31, "semicircle", "%17.10e"),
        "c_rc": ([(181, 181+16-1)], True, 2 ** -5, "m", "%8.5e"),
        "omega": ([(181+16,181+16+8-1), (211, 211 + 24 - 1)], False, 2 ** -33, None, "%17.10e"),
        "Omegad": ([(241,241+24-1)], True, 2 ** -29, "semicircle/s", "%17.10e"),
        "iode": ([(271, 271 + 8 - 1)], False, None, None, "%3d"),
        "idot": ([(279,279+14-1)], False, 2 ** -43, "s", "%8.5e"),
    },
}


def parse_l1ca_subframe(packet):
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
    units=[]
    fmts=[]
    subframe=get_bits(packet.dwrd,50,52)
    if subframe==2:
        print(2)
    if subframe in subframe_123:
        for name,(parts,signed,scale,unit,fmt) in subframe_123[subframe].items():
            names.append(name)
            value=get_multi_bits(packet.dwrd,parts,signed)
            if callable(scale):
                value=scale(value)
            elif scale is not None:
                value=scale*value
            values.append(value)
            units.append(unit)
            fmts.append(fmt)
        return namedtuple(f"subframe{subframe}", " ".join(names))._make(values),units,fmts
    else:
        return None,None,None

