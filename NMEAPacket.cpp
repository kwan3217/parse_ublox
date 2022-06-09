//
// Created by jeppesen on 4/5/22.
//

#include "NMEAPacket.h"

size_t nmea_read(uint8_t *packet, FILE* inf) {
  size_t ptr=1;
  fread(packet+ptr,1,1,inf);
  while(packet[ptr]!='*') {
    ptr++;
    fread(packet+ptr,1,1,inf);
  }
  ptr++;
  fread(packet+ptr,1,2,inf);
  if(packet[ptr]!='\x0d') {
    ptr+=2;
    fread(packet+ptr,1,2,inf);
  }
  return ptr+2;
}

std::unique_ptr<Packet> NMEAPacket::read(FILE *inf) {
  return nullptr;
}
