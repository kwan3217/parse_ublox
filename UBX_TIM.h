//
// Created by jeppesen on 5/23/22.
//

#ifndef PARSE_UBLOX_UBX_TIM_H
#define PARSE_UBLOX_UBX_TIM_H

#include "UBloxPacket.h"

struct hp_time_t {
  time_t sec;
  double ssec;
};

class UBX_TIM_TP:public UBloxPacket {
public:
  static const uint8_t clsconst=0x0d;
  static const uint8_t idconst=0x01;
  uint32_t iTOW_ms;
  uint32_t towSubMS_2tm32;
  int32_t qErr;
  uint16_t week;
  struct flags_t {
    bool timeBaseUTC: 1;
    bool utc:1;
    unsigned int raim:2;
    bool qErrInvalid:1;
  };
  flags_t flags;
  struct refInfo_t {
    unsigned int timeRefGnss: 4;
    unsigned int utcStandard:4;
  };
  refInfo_t refInfo;

  UBX_TIM_TP(uint8_t* buf):UBloxPacket(buf) {
    size_t pos;
    pos=0;
    readField(iTOW_ms,buf+6,pos);
    readField(towSubMS_2tm32,buf+6,pos);
    readField(qErr,buf+6,pos);
    readField(week,buf+6,pos);
    readField(flags,buf+6,pos,1);
    readField(refInfo,buf+6,pos,1);
  }
  double tow() {
    double tow_ms=double(iTOW_ms)+double(towSubMS_2tm32)/(uint64_t(1)<<32);
    return tow_ms/1000;
  }
  void print() {
    UBloxPacket::print();
    printf("\nweek:t=%4d:%24.14f\n",week, tow());
  }
  hp_time_t get() {
    time_t gps_epoch=315964800;
    time_t sec=gps_epoch+week*7*86400+iTOW_ms/1000;
    double ssec=(double(iTOW_ms%1000)+double(towSubMS_2tm32)/(uint64_t(1)<<32))/1000;
    while(ssec<0) {
      sec-=1;
      ssec+=1;
    }
    while(ssec>1) {
      sec+=1;
      ssec-=1;
    }
    return hp_time_t{sec,ssec};
  }
  static std::unique_ptr<Packet> read(uint8_t* buf) {return std::make_unique<UBX_TIM_TP>(buf);}
};

extern const char* TIMid[];
extern const packetFactory TIM[];


#endif //PARSE_UBLOX_UBX_TIM_H
