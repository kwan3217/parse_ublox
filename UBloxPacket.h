//
// Created by jeppesen on 4/5/22.
//

#ifndef PARSE_UBLOX_UBLOXPACKET_H
#define PARSE_UBLOX_UBLOXPACKET_H


#include <cstdint>
#include <cstring>
#include <vector>
#include <memory>
#include "Packet.h"
#include "L1CA.h"

size_t ublox_read(uint8_t* packet, FILE* inf);

enum gnss_t {
  GPS=0,
  SBAS=1,
  GAL=2,
  BDS=3,
  IMES=4,
  QZSS=5,
  GLO=6,
  NavID=7
};

enum gps_sig_t {
  g_L1CA=0,
  g_L2CL=3,
  g_L2CM=4,
  g_L5I=6,
  g_L5Q=7
};

enum gal_sig_t {
  E1C=0,
  E1B=2,
  E5aI=3,
  E5aQ=4,
  bI=5,
  bQ=6
};

enum bds_sig_t {
  B1I_D1=0,
  B1I_D2=1,
  B2I_D1=2,
  B2I_D2=3,
  B1C=5,
  B2a=7
};

enum qzss_sig_t {
  q_L1CA=0,
  q_L1S=1,
  q_L2CM=4,
  q_L2CL=5,
  q_L5I=8,
  q_L5Q=9
};

enum glo_sig_t {
  L1OF=0,
  L2OF=2
};

enum navic_sig_t {
  n_L5A=0
};

union sig_t {
  gps_sig_t gps_sig;
  gal_sig_t gal_sig;
  bds_sig_t bds_sig;
  qzss_sig_t qzss_sig;
  glo_sig_t glo_sig;
  navic_sig_t navic_sig;
};

class UBloxPacket:public Packet {
public:
  uint16_t magic;
  uint8_t cls;
  uint8_t id;
  uint16_t length;
  const static packetFactory* UBX[];
  const static char* UBXcls[256];
  const static char** UBXid[];
  static std::vector<uint16_t> histClsId;
  static std::vector<size_t>  histCount;
  static std::vector<size_t>  histSize;
  template <typename T>
  static void readField(T& field, uint8_t *buf, size_t& pos, size_t size=0) {
    if(size==0) size=sizeof(T);
//    printf("pos: %3lu   size: %3lu\n",pos,size);
    memcpy(&field,&buf[pos],size);
    pos+=size;
  }
  template <typename T>
  static T readField(char* buf, size_t& pos, size_t size=0) {
    T result;
    readField(result,buf,pos,size);
    return result;
  }
  template <typename T>
  static T readField(const char* fieldName, uint8_t *buf, size_t& pos, size_t size=0) {
    T result;
//    printf("field: %20s",fieldName);
    readField(result,buf,pos,size);
    return result;
  }
  void readHeader(uint8_t *buf, size_t& pos) {
    pos=0;
    readField(magic,buf,pos);
    readField(cls,buf,pos);
    readField(id,buf,pos);
    readField(length,buf,pos);
  }
  UBloxPacket(uint8_t *buf) {
    size_t pos=0;
    readHeader(buf,pos);
    uint16_t clsId=uint16_t(id)<<8 | uint16_t(cls);
    auto it=find(histClsId.begin(),histClsId.end(),clsId);
    if(it!=histClsId.end()) {
      //Found it, get the index
      size_t i=it-histClsId.begin();
      histCount[i]++;
      histSize[i]+=length+8; //include packet overhead
    } else {
      histClsId.push_back(clsId);
      histCount.push_back(1);
      histSize.push_back(length+8);
    }
  }
  static std::unique_ptr<uint8_t[]> readHelper(uint8_t* header, int header_len, FILE *inf);
  static std::unique_ptr<Packet> read(uint8_t* buf) {
    uint8_t cls=buf[2];
    uint8_t id=buf[3];
    if(UBX[cls]) {
      if(UBX[cls][id]) {
        return UBX[cls][id](buf);
      }
    }
    return std::make_unique<UBloxPacket>(buf);
  }
  static std::unique_ptr<Packet> read(uint8_t* header, int header_len, FILE* inf) {
    std::unique_ptr<uint8_t[]> buf=readHelper(header,header_len,inf);
    return read(buf.get());
  }
  void print() {
    if(UBXcls[cls]!=nullptr) {
      printf("UBX-%s-",UBXcls[cls]);
      if(UBXid[cls]!=nullptr && UBXid[cls][id]!=nullptr) {
        printf("%s", UBXid[cls][id]);
      } else {
        printf("0x%02x",id);
      }
    } else {
      printf("UBX-0x%02x-0x%02x", cls, id);
    }
    printf("  len=%4d*4+%1d+8=%5d+8=%5d",length/4,length%4,length,length+8);
  }
  static void printStats() {
    for(int i=0;i<histClsId.size();i++) {
      uint16_t clsId=histClsId[i];
      uint8_t cls=uint8_t((clsId>>0) & 0xff);
      uint8_t id =uint8_t((clsId>>8) & 0xff);
      printf("UBX-");
      if(UBXcls[cls]) {
        printf("%s-",UBXcls[cls]);
        if(UBXid[cls]!=nullptr && UBXid[cls][id]) {
          printf("%s",UBXid[cls][id]);
        } else {
          printf("0x%02x",id);
        }
      } else {
        printf("0x%02x-0x%02x",cls,id);
      }
      printf(": %ld packets, %ld bytes\n",histCount[i],histSize[i]);
    }
  }
  static uint32_t minutes;
  static uint32_t last_t;
};



#endif //PARSE_UBLOX_UBLOXPACKET_H
