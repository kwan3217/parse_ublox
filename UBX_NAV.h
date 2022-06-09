//
// Created by jeppesen on 5/23/22.
//

#ifndef PARSE_UBLOX_UBX_NAV_H
#define PARSE_UBLOX_UBX_NAV_H

#include <cmath>
#include "UBloxPacket.h"
#include "NMEAPacket.h"

inline double encode_dm(double dd) {
  dd=fabs(dd);
  int d=floor(dd);
  double fd=dd-d;
  double m=fd*60;
  return d*100+m;
}

class UBX_NAV_PVT:public UBloxPacket {
public:
  static const uint8_t clsconst=0x01;
  static const uint8_t idconst=0x07;
  uint32_t iTOW_ms;
  uint16_t year;
  uint8_t month;
  uint8_t day;
  uint8_t hour;
  uint8_t min;
  uint8_t sec;
  struct valid_t {
    bool validDate: 1;
    bool validTime: 1;
    bool fullyResolved: 1;
    bool validMag: 1;
  };
  valid_t valid;
  uint32_t tAcc_ns;
  int32_t nano_ns;
  uint8_t fixType;
  struct flags_t {
    bool gnssFixOK:1;
    bool diffSoln:1;
    unsigned int psmState:3;
    bool headVehValid:1;
    unsigned int carrSoln:2;
  };
  flags_t flags;
  struct flags2_t {
    unsigned int pad:5;
    bool confirmedAvai:1;
    bool confirmedDate:1;
    bool confirmedTime:3;
  };
  flags2_t flags2;
  uint8_t numSV;
  int32_t lon_1em7deg;
  int32_t lat_1em7deg;
  int32_t height_mm;
  int32_t hMSL_mm;
  uint32_t hAcc_mm;
  uint32_t vAcc_mm;
  int32_t velN_mmps;
  int32_t velE_mmps;
  int32_t velD_mmps;
  int32_t gSpeed_mmps;
  int32_t headMot_1em5deg;
  uint32_t sAcc_mmps;
  uint32_t headAcc_1em5deg;
  uint16_t pdop_1em2;
  struct flags3_t {
    bool invalidL1h:1;
    unsigned int lastCorrectionAge:4;
  };
  flags3_t flags3;
  uint8_t res0A;
  uint32_t res0B;
  int32_t headVeh_1em5deg;
  int16_t magDec_1em2deg;
  uint16_t magAcc_1em2deg;
  UBX_NAV_PVT(uint8_t* buf):UBloxPacket(buf) {
    size_t pos;
    pos=0;
    readField(iTOW_ms,buf+6,pos);
    readField(year,buf+6,pos);
    readField(month,buf+6,pos);
    readField(day,buf+6,pos);
    readField(hour,buf+6,pos);
    readField(min,buf+6,pos);
    readField(sec,buf+6,pos);
    readField(valid,buf+6,pos);
    readField(tAcc_ns,buf+6,pos);
    readField(nano_ns,buf+6,pos);
    readField(fixType,buf+6,pos);
    readField(flags,buf+6,pos,1);
    readField(flags2,buf+6,pos,1);
    readField(numSV,buf+6,pos);
    readField(lon_1em7deg,buf+6,pos);
    readField(lat_1em7deg,buf+6,pos);
    readField(height_mm,buf+6,pos);
    readField(hMSL_mm,buf+6,pos);
    readField(hAcc_mm,buf+6,pos);
    readField(vAcc_mm,buf+6,pos);
    readField(velN_mmps,buf+6,pos);
    readField(velE_mmps,buf+6,pos);
    readField(velD_mmps,buf+6,pos);
    readField(gSpeed_mmps,buf+6,pos);
    readField(headMot_1em5deg,buf+6,pos);
    readField(sAcc_mmps,buf+6,pos);
    readField(headAcc_1em5deg,buf+6,pos);
    readField(pdop_1em2,buf+6,pos);
    readField(flags3,buf+6,pos);
    readField(res0A,buf+6,pos);
    readField(res0B,buf+6,pos);
    readField(headVeh_1em5deg,buf+6,pos);
    readField(magDec_1em2deg,buf+6,pos);
    readField(magAcc_1em2deg,buf+6,pos);
  }
  void print() {
    UBloxPacket::print();
    printf("\nt=%f %04d-%02d-%02dT%02d:%02d:%02d lat=%f lon=%f h=%f\n", double(iTOW_ms)/1000,year,month,day,hour,min,sec,float(lat_1em7deg)/1e7,float(lon_1em7deg)/1e7,float(hMSL_mm)/1000);
  }
  double lon() {return double(lon_1em7deg)*1e-7;}
  double lat() {return double(lat_1em7deg)*1e-7;}
  double height() {return double(height_mm)*1e-3;}
  double hMSL() {return double(hMSL_mm)*1e-3;}
  void GGA(FILE* ouf) {
    double latdm=encode_dm(lat());
    double londm=encode_dm(lon());
    char buf[256];
    int pos=sprintf(buf,"$GPGGA,%02d%02d%02d.000,",hour,min,sec);
    pos+=sprintf(buf+pos,"%.8lf,%c,",latdm,lat_1em7deg>0?'N':'S');
    pos+=sprintf(buf+pos,"%.8lf,%c,",londm,lon_1em7deg>0?'E':'W');
    pos+=sprintf(buf+pos,"%1d,%02d,%.2lf,",1,0,0.00);
    pos+=sprintf(buf+pos,"%.4lf,M,%.4lf,M,,,*",hMSL(),height()-hMSL());
    appendChecksum(buf,pos);
    fputs(buf,ouf);
  }
  void RMC(FILE* ouf) {
    double latdm=encode_dm(lat());
    double londm=encode_dm(lon());
    char buf[256];
    int pos=sprintf(buf,"$GPRMC,%02d%02d%02d.000,A,",hour,min,sec);
    pos+=sprintf(buf+pos,"%.8lf,%c,",latdm,lat_1em7deg>0?'N':'S');
    pos+=sprintf(buf+pos,"%.8lf,%c,",londm,lon_1em7deg>0?'E':'W');
    pos+=sprintf(buf+pos,"0.000,00.00,");
    pos+=sprintf(buf+pos,"%02d%02d%02d,,,A*",day,month,year%100);
    appendChecksum(buf,pos);
    fputs(buf,ouf);
  }
  static std::unique_ptr<Packet> read(uint8_t *buf) {return std::make_unique<UBX_NAV_PVT>(buf);}
};

class UBX_NAV_HPPOSECEF:public UBloxPacket {
public:
  uint8_t version;
  uint8_t res0A;
  uint8_t res0B;
  uint8_t res0C;
  uint32_t iTOW_ms;
  int32_t ecefX_1em2m;
  int32_t ecefY_1em2m;
  int32_t ecefZ_1em2m;
  int8_t ecefXHp_1em4m;
  int8_t ecefYHp_1em4m;
  int8_t ecefZHp_1em4m;
  struct flags_t {
    bool invalidEcef: 1;
  };
  flags_t flags;
  uint32_t pAcc_1em4m;
  UBX_NAV_HPPOSECEF(uint8_t* buf):UBloxPacket(buf) {
    size_t pos;
    pos=0;
    readField(version,buf+6,pos);
    readField(res0A,buf+6,pos);
    readField(res0B,buf+6,pos);
    readField(res0C,buf+6,pos);
    readField(iTOW_ms,buf+6,pos);
    readField(ecefX_1em2m,buf+6,pos);
    readField(ecefY_1em2m,buf+6,pos);
    readField(ecefZ_1em2m,buf+6,pos);
    readField(ecefXHp_1em4m,buf+6,pos);
    readField(ecefYHp_1em4m,buf+6,pos);
    readField(ecefZHp_1em4m,buf+6,pos);
    readField(flags,buf+6,pos,1);
    readField(pAcc_1em4m,buf+6,pos);
  }
  double ecefX() {return (double(ecefX_1em2m)*100+double(ecefXHp_1em4m))/1e4;}
  double ecefY() {return (double(ecefY_1em2m)*100+double(ecefYHp_1em4m))/1e4;}
  double ecefZ() {return (double(ecefZ_1em2m)*100+double(ecefZHp_1em4m))/1e4;}
  void print() {
    UBloxPacket::print();
    printf("\nt=%f x=%13.4f y=%13.4f z=%13.4f\n", double(iTOW_ms)/1000,ecefX(),ecefY(),ecefZ());
    printf("pAcc: %.4f\n",double(pAcc_1em4m)/1e4);
  }
  static std::unique_ptr<Packet> read(uint8_t *buf) {return std::make_unique<UBX_NAV_HPPOSECEF>(buf);}
};

class UBX_NAV_HPPOSLLH:public UBloxPacket {
public:
  static const uint16_t clsconst=0x01;
  static const uint16_t idconst=0x14;
  uint8_t version;
  uint8_t res0A;
  uint8_t res0B;
  struct flags_t {
    bool invalidLlh: 1;
  };
  flags_t flags;
  uint32_t iTOW_ms;
  int32_t lon_1em7deg;
  int32_t lat_1em7deg;
  int32_t height_1em3m;
  int32_t hMSL_1em3m;
  int8_t lonHp_1em9deg;
  int8_t latHp_1em9deg;
  int8_t heightHp_1em4m;
  int8_t hMSLHp_1em4m;
  uint32_t hAcc_1em4m;
  uint32_t vAcc_1em4m;
  UBX_NAV_HPPOSLLH(uint8_t* buf):UBloxPacket(buf) {
    size_t pos;
    pos=0;
    readField(version,buf+6,pos);
    readField(res0A,buf+6,pos);
    readField(res0B,buf+6,pos);
    readField(flags,buf+6,pos,1);
    readField(iTOW_ms,buf+6,pos);
    readField(lon_1em7deg,buf+6,pos);
    readField(lat_1em7deg,buf+6,pos);
    readField(height_1em3m,buf+6,pos);
    readField(hMSL_1em3m,buf+6,pos);
    readField(lonHp_1em9deg,buf+6,pos);
    readField(latHp_1em9deg,buf+6,pos);
    readField(heightHp_1em4m,buf+6,pos);
    readField(hMSLHp_1em4m,buf+6,pos);
    readField(hAcc_1em4m,buf+6,pos);
    readField(vAcc_1em4m,buf+6,pos);
  }
  double lon() {return (double(lon_1em7deg)*100+double(lonHp_1em9deg))/1e9;}
  double lat() {return (double(lat_1em7deg)*100+double(latHp_1em9deg))/1e9;}
  double height() {return (double(height_1em3m)*10+double(heightHp_1em4m))/1e4;}
  double hMSL() {return (double(hMSL_1em3m)*10+double(hMSLHp_1em4m))/1e4;}
  void print() {
    UBloxPacket::print();
    printf("\nt=%f lon=%14.9f lat=%14.9f height=%10.4f\n", double(iTOW_ms)/1000,lon(),lat(),height());
    printf("hAcc: %.4f\n",double(hAcc_1em4m)/1e4);
    printf("vAcc: %.4f\n",double(vAcc_1em4m)/1e4);
  }
  static std::unique_ptr<Packet> read(uint8_t *buf) {return std::make_unique<UBX_NAV_HPPOSLLH>(buf);}
  void GGA(FILE* ouf) {
    int d=iTOW_ms/86400'000;
    int hms=iTOW_ms%86400'000;
    int h=hms/3600'000;
    int ms=hms%3600'000;
    int m=ms/60'000;
    double s=double(ms%60'000)/1000;
    double latdm=encode_dm(lat());
    double londm=encode_dm(lon());
    char buf[256];
    int pos=sprintf(buf,"$GPGGA,%02d%02d%06.3lf,",h,m,s);
    pos+=sprintf(buf+pos,"%.8lf,%c,",latdm,lat_1em7deg>0?'N':'S');
    pos+=sprintf(buf+pos,"%.8lf,%c,",londm,lon_1em7deg>0?'E':'W');
    pos+=sprintf(buf+pos,"%1d,%02d,%.2lf,",1,0,0.00);
    pos+=sprintf(buf+pos,"%.4lf,M,%.4lf,M,,,*",hMSL(),height()-hMSL());
    appendChecksum(buf,pos);
    fputs(buf,ouf);
  }
};

class UBX_NAV_EOE:public UBloxPacket {
public:
  uint32_t iTOW_ms;
  UBX_NAV_EOE(uint8_t* buf):UBloxPacket(buf) {
    size_t pos;
    pos=0;
    readField(iTOW_ms,buf+6,pos);
  }
  void print() {
    UBloxPacket::print();
    printf("\nt=%11.3f", double(iTOW_ms)/1000);
  }
  static std::unique_ptr<Packet> read(uint8_t *buf) {return std::make_unique<UBX_NAV_EOE>(buf);}
};

extern const char* NAVid[];
extern const packetFactory NAV[];


#endif //PARSE_UBLOX_UBX_NAV_H
