#ifndef L1CA_h
#define L1CA_h

/*
 * # GPS L1C/A Nav Message description. Each field consists of:
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
 */
#include <cstddef>
#include <cstdint>
#include <limits>
#include "bits.h"

class NavMessage {
public:
  /**
   * Get a field from a 10-word L1CA message
   * @param words 10-word message
   * @param b0 starting bit number in entire 10-word message
   * @param b1 ending bit number in entire 10-word message
   * @return
   *
   * bits in the words are labeled as in the ICD -- lowest index word consists bits 1 (MSB) through 30 (LSB),
   * second word is bits 31 (MSB) through 60 (LSB) etc. Nav message consists of 30-bit words, but UBlox GPS
   * receiver packs them in the lowest 30 bits of a 32-bit word, with no information carried in the highest
   * two bits. Fields are not allowed to cross word boundaries -- use get_fields() for that.
   */
  template <typename T>
  static T get_field(uint32_t word, size_t b0, size_t b1, bool s=false) {
    b0 = 30 - b0;
    b1 = 30 - b1;
    uint64_t result=get_bits<uint32_t>(word, b0, b1);
    if(s) result=sign_extend<uint64_t>(result,b1-b0+1);
    return T(result);
  }
  template <typename T>
  static T get_field(std::vector<uint32_t> *words, uint32_t b0, uint32_t b1, bool s=false) {
    uint32_t i_word = (b0 - 1) / 30;
    return get_field<T>((*words)[i_word],(b0-1)%30+1,(b1-1)%30+1,s);
  }

  template <typename T>
  static T get_field(std::vector<uint32_t> *words, size_t b00, size_t b01, size_t b10, size_t b11, bool s=false) {
    uint64_t word0 = get_field<size_t>(words, b00, b01,false);
    size_t bits0=b01-b00+1;
    uint64_t word1 = get_field<size_t>(words, b10, b11,false);
    size_t bits1=b11-b10+1;
    uint64_t result=word0 << (b11 - b10 + 1) | word1;
    if(!s) return T(result);
    return sign_extend<T>(result,bits1+bits0-1);
  }

  static double scale(uint32_t field, int8_t amt) {
    if (amt < 0) {
      return double(field) / (uint64_t(1) << -amt);
    }
    return double(field) * (uint64_t(1) << amt);
  }
  static double scale(std::vector<uint32_t> *words, uint32_t b0, uint32_t b1, int8_t amt, bool s=false) {
    return scale(get_field<uint32_t>(words,b0,b1,s),amt);
  }
  static double scale(std::vector<uint32_t> *words, uint32_t b00, uint32_t b01, uint32_t b10, uint32_t b11, int8_t amt, bool s=false) {
    return scale(get_field<uint32_t>(words,b00,b01,b10,b11,s),amt);
  }
  virtual void print() {};
};

class L1CA:public NavMessage {
private:
  std::vector<uint32_t>* words;
public:
  uint8_t preamble;
  uint32_t tlm;
  bool integ_stat;
  uint32_t tow_count;
  bool alert;
  bool antispoof;
  uint8_t subframe;
  L1CA(std::vector<uint32_t>* Lwords):words(Lwords) {
    preamble = get_field<uint8_t>(words, 1, 8);
    tlm = get_field<uint32_t>(words, 9, 22);
    integ_stat = get_field<bool>(words, 24, 24);
    tow_count=get_field<uint32_t>(words,1+30,17+30);
    alert=get_field<bool>(words,1+18,1+18);
    antispoof=get_field<bool>(words,1+19,1+19);
    subframe=get_field<uint8_t>(words,20+30,22+30);
  }
  static L1CA* read(std::vector<uint32_t>* words);
  void print() {
    NavMessage::print();
    printf("\n");
    for(auto word:*words) {
      printf(" %06x",get_field<uint32_t>(word,1,24));
    }
    printf("\npreamble:   %02x\n",preamble);
    printf("tlm:        %x\n",tlm);
    printf("integ_stat: %d\n",integ_stat);
    printf("tow_count:  %d\n",tow_count);
    printf("alert:      %d\n",alert);
    printf("antispoof:  %d\n",antispoof);
    printf("subframe:   %d",subframe);
  }
};

class L1CA_1:public L1CA{
public:
  uint16_t wn; //week
  uint8_t msg_on_l2;
  double ura; //m
  uint8_t sv_health;
  uint16_t iodc;
  double t_gd; //s
  double t_oc; //s
  double a_f2; //s/s**2
  double a_f1; //s/s
  double a_f0; //s
  static double nominal_ura(uint32_t N) {
    if(N==1) return 2.8;
    if(N==3) return 5.7;
    if(N==5) return 11.3;
    if(N==15) return std::numeric_limits<double>::infinity();
    if(N<=6) return double(1<<(1+N/2));
    return double(1<<(N-2));
  }
  L1CA_1(std::vector<uint32_t>* words):L1CA(words) {
    wn=get_field<uint16_t>(words,61,70);
    msg_on_l2=get_field<uint8_t>(words,71,72);
    ura=nominal_ura(get_field<uint32_t>(words,73,76));
    sv_health=get_field<uint8_t>(words,77,82);
    iodc=get_field<uint16_t>(words,83,84,211,218);
    t_gd=scale(words,197,197+8-1,-31,true);
    t_oc=scale(words,219,219+16-1,4);
    a_f2=scale(words,241,241+8-1,-55,true);
    a_f1=scale(words,241+8,241+8+16-1,-43,true);
    a_f0=scale(words,271,271+22-1,-31,true);
  }
  void print() {
    L1CA::print();
    printf(" (clock)\n");
    printf("wn:         %d\n",wn);
    printf("msg_on_l2:  %d\n",msg_on_l2);
    printf("ura:        %f m\n",ura);
    printf("sv_health:  %d\n",sv_health);
    printf("iodc:       %d\n",iodc);
    printf("t_gd:       %e s\n",t_gd);
    printf("t_oc:       %e s\n",t_oc);
    printf("a_f2:       %e s/s**2\n",a_f2);
    printf("a_f1:       %e s/s\n",a_f1);
    printf("a_f0:       %e s\n",a_f0);
  }
};
class L1CA_2:public L1CA {
public:
  uint8_t iode;
  double c_rs; //m
  double delta_n; //semicircle/s
  double M_0; //semicircle
  double c_uc; //radian
  double e;
  double c_us; //radian
  double sqrtA,A; //m, store sqrtA as transmitted since it is used as-is in relativistic time correction
  double t_oe; //s
  bool fit;
  double aodo; //s
  L1CA_2(std::vector<uint32_t>* words):L1CA(words) {
    iode=get_field<uint8_t>(words,61,68);
    c_rs=scale(words,69,69+16-1,-5,true);
    delta_n=scale(words,91,106,-43,true);
    M_0=scale(words,107,107+8-1,121,121+24-1,-31,true);
    c_uc=scale(words,151,166,-29,true);
    e=scale(words,167,167+8-1,181,181+24-1,-33);
    c_us=scale(words,211,226,-29,true);
    sqrtA=scale(words,227,227+8-1,241,241+24-1,-19);A=sqrtA*sqrtA;
    t_oe=scale(words,271,286,4);
    fit=get_field<bool>(words,287,287);
    aodo=900*get_field<uint32_t>(words,288,288+5-1);
  }

  void print() {
    L1CA::print();
    printf(" (ephemeris A)\n");
    printf("iode:         %3d\n",iode);
    printf("c_rs:         %8.5e\n",c_rs);
    printf("delta_n:      %8.5e\n",delta_n);
    printf("M_0:          %8.5e\n",M_0);
    printf("c_uc:         %8.5e\n",c_uc);
    printf("e:            %21.14e\n",e);
    printf("c_us:         %8.5e\n",c_us);
    printf("A:            %21.6f\n",A);
    printf("t_oe:         %12f\n",t_oe);
    printf("fit:          %1d\n",fit);
    printf("aodo:         %5.0f\n",aodo);
  }
};
class L1CA_3:public L1CA{
public:
  double c_ic; //rad
  double Omega_0; //semicircle
  double c_is; //rad
  double i_0; //semicircle
  double c_rc; //m
  double omega;
  double Omegad; //semicircle/s
  uint8_t iode;
  double idot; //s
  L1CA_3(std::vector<uint32_t>* words):L1CA(words) {
    c_ic=scale(words,61, 77-1,-29,true);
    Omega_0=scale(words,77,77+8-1,91,91+24-1,-31,true);
    c_is=scale(words,121, 137-1,-29,true);
    i_0=scale(words,137, 137 + 8 - 1, 151, 151 + 24 - 1,-31,true);
    c_rc=scale(words,181, 181+16-1,-5,true);
    omega=scale(words,181+16,181+16+8-1, 211, 211 + 24 - 1,-33,true);
    Omegad=scale(words,241,241+24-1,-29,true);
    iode=get_field<uint8_t>(words,271, 271 + 8 - 1);
    idot=scale(words,279,279+14-1,-43,true);
  }
  void print() {
    L1CA::print();
    printf(" (ephemeris B)\n");
    printf("c_ic:      %8.5e\n",c_ic);
    printf("Omega_0:   %17.10e\n",Omega_0);
    printf("c_is:      %8.5e\n",c_is);
    printf("i_0:       %17.10e\n",i_0);
    printf("c_rc:      %8.5e\n",c_rc);
    printf("omega:     %17.10e\n",omega);
    printf("Omegad:    %17.10e\n",Omegad);
    printf("iode:      %3d\n",iode);
    printf("idot:      %8.5e\n",idot);
  }
};

class L1CA_Alm:public L1CA {
public:
  uint8_t data_id;
  uint8_t sv_id;
  double e;
  double t_oa; //s
  double delta_i,i; //semicircles
  double Omegad; //semicircle
  uint8_t sv_health; //m
  double sqrtA,A;
  double Omega_0; //semicircle/s
  double omega;
  double M_0;
  double a_f0;
  double a_f1;
  uint8_t svid;
  uint8_t page;
  L1CA_Alm(std::vector<uint32_t> * words):L1CA(words) {
    data_id=get_field<uint8_t>(words,61,62);
    sv_id=get_field<uint8_t>(words,63,68);
    e = scale(words, 69, 69+16-1, -21);
    t_oa=scale(words, 91,91+8-1, 12);
    delta_i=scale(words, 99,99+16-1, -19);
    Omegad=scale(words, 121,121+16-1, -38);
    sv_health=get_field<uint8_t>(words, 121+16,121+16+8-1);
    sqrtA=scale(words, 151,151+24-1, -11);A=sqrtA*sqrtA;
    Omega_0=scale(words, 181, 181+24-1, -23);
    omega=scale(words, 211, 211+24-1,-23);
    M_0=scale(words, 241,241+24-1, -32);
    a_f0=scale(words,271,271+8-1,290,290+3-1,-20);
    a_f1=scale(words,279,279+11-1,-38);
  }

  void print() {
    L1CA::print();
  }
};
inline L1CA* L1CA::read(std::vector<uint32_t>* words) {
  uint8_t subframe=L1CA::get_field<uint8_t>(words,20+30,22+30);
  switch(subframe) {
    case 1:return new L1CA_1(words);
    case 2:return new L1CA_2(words);
    case 3:return new L1CA_3(words);
    case 4:
    case 5:return new L1CA_Alm(words);
  }
  return nullptr;
}


#endif