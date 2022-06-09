#ifndef bits_h
#define bits_h

#include <cstdint>

template <typename T>
inline T get_bits(T source, uint8_t b1, uint8_t b0) {
  T size=b1-b0+1;
  T mask=(1<<(size))-1;
  T result=(source>>b0) & mask;
  return result;
}

template <typename T>
inline constexpr T put_bits(T dest, uint8_t b1, uint8_t b0, uint32_t val) {
  T size=b1-b0+1;
  T mask=(1<<(size))-1;
  T mask_in_place=~(mask<<b0);
  T masked_out=dest & mask_in_place;
  T new_bits_in_place=(T(val) & mask)<<b0;
  T result=masked_out | new_bits_in_place;
  return result;
}

/**
 *
 * @tparam T Type of data to return
 * @param data data to sign-extend
 * @param sign_bit_pos If this bit is 1, the number is negative, and all bits above it should be set to 1 as well
 * @return sign-extended data cast to type T
 */
template <typename T>
inline constexpr T sign_extend(uint64_t data, size_t sign_bit_pos) {
  uint64_t sign_bit_mask=1<<sign_bit_pos;
  uint64_t bits_to_extend=64-sign_bit_pos-1;
  uint64_t extended_bits_mask=(uint64_t(1)<<(bits_to_extend+1))-1 << sign_bit_pos;
  if(data & sign_bit_mask) {
    return T(data | extended_bits_mask);
  } else {
    return T(data);
  }
}

inline void printBuf(uint8_t* buf, size_t n) {
  for(size_t i=0;i<n;i++) {
    if(i%16==0) printf("\n%08lx  ",i);
    if(i% 4==0) printf(" ");
    printf("%02x",buf[i]);
  }
}

#endif