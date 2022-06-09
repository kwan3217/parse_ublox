//
// Created by jeppesen on 4/5/22.
//

#include "RTCM3Packet.h"

size_t rtcm_read(uint8_t *packet, FILE* inf) {
  fread(packet+1,2,1,inf);
  size_t msb=packet[1] & 0x03;
  size_t lsb=packet[2] & 0xff;
  size_t length=lsb | (msb<<8);
  fread(packet+3,length+3,1,inf);
  return length+6;
}
