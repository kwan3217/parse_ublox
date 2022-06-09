//
// Created by jeppesen on 5/23/22.
//

#ifndef PARSE_UBLOX_UBX_ESF_H
#define PARSE_UBLOX_UBX_ESF_H

#include "UBloxPacket.h"

class UBX_ESF_MEAS:public UBloxPacket {
public:
  uint32_t timeTag;
  struct flags_t {
    unsigned int timeMarkSent: 2;
    bool timeMarkEdge: 1;
    bool calibTtagValid: 1;
    unsigned int numMeas: 5;
  };
  flags_t flags;
  uint16_t id;
  std::vector<int32_t> dataField;
  std::vector<uint8_t> dataType;
  uint32_t calibTtag;
  UBX_ESF_MEAS(uint8_t* buf):UBloxPacket(buf) {
    size_t pos=0;
    readField(timeTag,buf+6,pos);
    uint16_t Lflags;
    readField(Lflags,buf+6,pos);
    flags.timeMarkSent  =(Lflags>> 0) & 0b00011;
    flags.timeMarkEdge  =(Lflags>> 2) & 0b00001;
    flags.calibTtagValid=(Lflags>> 3) & 0b00001;
    flags.numMeas       =(Lflags>>11) & 0b11111;
    readField(id,buf+6,pos);
    for(uint8_t iMeas=0;iMeas<flags.numMeas;iMeas++) {
      uint32_t data;
      readField(data,buf+6,pos);
      dataField.push_back(sign_extend<int32_t>(data & 0xFFFFFF,23));
      dataType.push_back((data>>24) & 0b111111);
    }
    if(flags.calibTtagValid) {
      readField(calibTtag,buf+6,pos);
    }
  }
  void print() {
    UBloxPacket::print();
    printf("\ntimeTag: %d\n",timeTag);
    printf("id: %d\n",id);
    printf("type  name raw    scaled       units\n");
    printf("----- ---- ------ ------------ -----\n");
    for(size_t i=0;i<flags.numMeas;i++) {
      uint8_t type=dataType[i];
      printf("%5d %4s %06x %12.6f %s\n",type,typeName[type],dataField[i]&0xFFFFFF,double(dataField[i])*typeScale[type],typeUnit[dataType[i]]);
    }
  }
  static std::unique_ptr<Packet> read(uint8_t* buf) {
    return std::make_unique<UBX_ESF_MEAS>(buf);
  };
  static const char *typeName[19];
  static const char *typeUnit[19];
  static const double typeScale[19];
};

extern const packetFactory ESF[];
extern const char* ESFid[];

#endif //PARSE_UBLOX_UBX_ESF_H
