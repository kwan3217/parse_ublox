//
// Created by jeppesen on 4/5/22.
//

#include <cstdlib>
#include "Packet.h"
#include "UBloxPacket.h"
#include "NMEAPacket.h"
#include "RTCM3Packet.h"

packet_result read_packet(uint8_t* packet, FILE* inf) {
  bool done=false;
  size_t skip=0;
  packet_result result;
  while(!done) {
    size_t pos=ftell(inf);
    fread(packet, 1, 1, inf);
    switch (packet[0]) {
      case '$':
        result=packet_result{NMEA, nmea_read(packet, inf)};
        done=true;
        break;
      case 0xB5:
        fread(packet + 1, 1, 1, inf);
        if (packet[1] == '\x62') {
          result=packet_result{UBlox, ublox_read(packet, inf)};
          done=true;
        } else {
          skip+=2;
        }
        break;
      case 0xD3:
        result=packet_result{RTCM3, rtcm_read(packet, inf)};
        done=true;
        break;
      default:
        skip++;
    }
  }
  if(skip>0) {
    printf("Skipped %ld bytes before finding a packet\n",skip);
  }
  return result;
}


std::unique_ptr<Packet> Packet::read(FILE *inf) {
  uint8_t buf[2];
  fread(buf,1,1,inf);
  switch(buf[0]) {
    case '$':
      return NMEAPacket::read(inf);
      break;
    case 0xB5:
      fread(buf+1,1,1,inf);
      if(buf[1]=='\x62') {
        return UBloxPacket::read(buf,2,inf);
      } else {
        printf("Bad UBlox header second byte, expected %02x, saw %02x\n",0x62,buf[1]);
        exit(1);
      }
      break;
    case 0xD3:
      printf("RTCM3 packet, not yet handled\n");
      break;
    default:
      printf("Unrecognized packet start, saw %02x at %08lx\n",buf[0],ftell(inf));
      exit(2);
  }
  return std::make_unique<Packet>();
}
