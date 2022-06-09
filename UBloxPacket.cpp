//
// Created by jeppesen on 4/5/22.
//

#include <cstring>
#include "UBloxPacket.h"
#include "UBX_ESF.h"
#include "UBX_KWAN.h"
#include "UBX_MON.h"
#include "UBX_NAV.h"
#include "UBX_RXM.h"
#include "UBX_TIM.h"

size_t ublox_read(uint8_t* packet, FILE* inf) {
  fread(packet+2,4,1,inf);
  size_t lsb=packet[4] & 0xff;
  size_t msb=packet[5] & 0xff;
  size_t length=lsb | (msb<<8);
  fread(packet+6,length+2,1,inf);
  return length+8;
}
const packetFactory* UBloxPacket::UBX[]={
        //NAV2 packets are assumed to have the same format as NAV. We can parse the union of NAV and NAV2, but
        //any given receiver will only send a subset of that union as NAV or NAV2.
   //    x0       x1      x2      x3      x4      x5      x6      x7      x8      x9      xA      xB      xC      xD      xE      xF
        nullptr,NAV    ,RXM    ,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,TIM    ,nullptr,nullptr,  // 0x
        ESF    ,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 1x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,NAV    ,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 2x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 3x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,KWAN   ,nullptr,nullptr,nullptr,nullptr,  // 4x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 5x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 6x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 7x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 8x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 9x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // Ax
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // Bx
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // Cx
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // Dx
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // Ex
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr   // Fx
};

const char* UBloxPacket::UBXcls[]={
    //    x0       x1      x2      x3      x4      x5      x6      x7      x8      x9      xA      xB      xC      xD      xE      xF
        nullptr,"NAV"  ,"RXM"  ,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,"MON"  ,nullptr,nullptr,"TIM"  ,nullptr,nullptr,  // 0x
        "ESF"  ,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 1x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,"NAV2" ,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 2x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 3x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,"KWAN" ,nullptr,nullptr,nullptr,nullptr,  // 4x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 5x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 6x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 7x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 8x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 9x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // Ax
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // Bx
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // Cx
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // Dx
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // Ex
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr   // Fx
};

const char** UBloxPacket::UBXid[]={
     //    x0       x1      x2      x3      x4      x5      x6      x7      x8      x9      xA      xB      xC      xD      xE      xF
        nullptr,NAVid  ,RXMid  ,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,MONid  ,nullptr,nullptr,TIMid  ,nullptr,nullptr,  // 0x
        ESFid  ,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 1x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,NAVid  ,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 2x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 3x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,KWANid ,nullptr,nullptr,nullptr,nullptr,  // 4x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 5x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 6x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 7x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 8x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // 9x
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // Ax
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // Bx
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // Cx
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // Dx
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,  // Ex
        nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr   // Fx
};

std::unique_ptr<uint8_t[]> UBloxPacket::readHelper(uint8_t* header, int header_len, FILE *inf) {
  //Read the rest of the header
  uint8_t full_header[6];
  memcpy(full_header,header,header_len);
  fread(full_header+header_len,4,1,inf);
  header_len+=4;
  //Figure out the payload length
  uint16_t payload_len=((uint16_t(header[4]) & 0xFF) << 0) |
                       ((uint16_t(header[5]) & 0xFF) << 8) ;
  //Move the first part of the header into the buffer
  uint8_t* result=new uint8_t[8+payload_len];
  memcpy(result,full_header,header_len);
  //read the payload and checksum
  fread(result+header_len,payload_len+2,1,inf);
  return std::unique_ptr<uint8_t[]>(result);
}

uint32_t UBloxPacket::last_t=0;
uint32_t UBloxPacket::minutes=0;
std::vector<uint16_t> UBloxPacket::histClsId;
std::vector<size_t>  UBloxPacket::histCount;
std::vector<size_t>  UBloxPacket::histSize;
uint32_t UBX_KWAN_MAG::last_t=0;

