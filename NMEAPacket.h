//
// Created by jeppesen on 4/5/22.
//

#ifndef PARSE_UBLOX_NMEAPACKET_H
#define PARSE_UBLOX_NMEAPACKET_H


#include "Packet.h"

size_t nmea_read(uint8_t *packet, FILE* inf);

class NMEAPacket: public Packet {
public:
  static std::unique_ptr<Packet> read(FILE* inf);
};

inline void appendChecksum(char* buf, int len) {
  char cksum=0;
  for(int i=1;i<len-1;i++) {
    cksum^=buf[i];
  }
  sprintf(buf+len,"%02X\r\n",cksum);
}


#endif //PARSE_UBLOX_NMEAPACKET_H
