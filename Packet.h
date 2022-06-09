//
// Created by jeppesen on 4/5/22.
//

#ifndef PARSE_UBLOX_PACKET_H
#define PARSE_UBLOX_PACKET_H


#include <cstdio>
#include <cstdint>
#include <memory>

enum packet_type{NMEA,UBlox,RTCM3};
struct packet_result {
  packet_type type;
  size_t length;
};

packet_result read_packet(uint8_t* packet, FILE* inf);

class Packet {
public:
  static std::unique_ptr<Packet> read(FILE* inf);
  virtual void print() {};
};

typedef std::unique_ptr<Packet> (*packetFactory)(uint8_t* packet);


#endif //PARSE_UBLOX_PACKET_H
