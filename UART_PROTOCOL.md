# STM32 F303 UART Communication Protocol

## Overview

This document describes the communication protocol for the MROV-25 STM32 F303 microcontroller via USB UART. The STM expects binary command packets to control 8 ESC motors and 4 servo motors.

## Hardware Configuration

- **Microcontroller**: STM32F303XE
- **UART Port**: USART2
- **Baud Rate**: 115200 bps
- **Data Bits**: 8
- **Stop Bits**: 1
- **Parity**: None
- **Flow Control**: None

## Packet Format

### Basic Structure
- **Total Packet Size**: 32 bytes
- **Data Type**: 8 signed 32-bit integers (int)
- **Byte Order**: Little-endian (standard on ARM)
- **Format**: Raw binary (NOT ASCII/text)

### Double Buffering
The STM uses DMA to receive data into a 64-byte circular buffer:
- **Buffer[0-31]**: Packet A
- **Buffer[32-63]**: Packet B

Packets are processed on DMA half-complete and complete callbacks, allowing continuous updates without gaps.

## Command Data Mapping

### Motor/Servo Indices in Packet

```
Index  Bytes      Device                              Value Range
0      0-3        ESC Motor 0: Front Right           1100-1900
1      4-7        ESC Motor 1: Front Right Top       1100-1900
2      8-11       ESC Motor 2: Back Right            1100-1900
3      12-15      ESC Motor 3: Back Right Top        1100-1900
4      16-19      ESC Motor 4: Back Left             1100-1900
5      20-23      ESC Motor 5: Back Left Top         1100-1900
6      24-27      ESC Motor 6: Front Left            1100-1900
7      28-31      ESC Motor 7: Front Left Top        1100-1900

8      32-35      Servo 0: Proximal Arm              1000-2000
9      36-39      Servo 1: Distal Arm                1000-2000
10     40-43      Servo 2: Wrist Flexion/Extension   1000-2000
11     44-47      Servo 3: Zed Camera                1000-2000
```

**Note**: Servo indices 8-11 are only processed after the `motors_armed_flag` is set (approximately 3 seconds after STM startup).

## Value Ranges and Clamping

### ESC Motors (Thruster Units)
- **1100**: Full reverse (backward)
- **1500**: Stop/Neutral
- **1900**: Full forward
- **Out-of-range behavior**: Values are clamped to [1100, 1900]
- **Clamping function** (from esc.c):
  ```c
  int clampESC(int val){
      int newVal = 1100 * (val < 1100) + val * (1 - (val < 1100));
      newVal = 1900 * (val > 1900) + val * (1 - (val > 1900));
      return newVal;
  }
  ```

### Servo Motors
- **Minimum**: 1000 (standard servo minimum)
- **Maximum**: 2000 (standard servo maximum)
- **Out-of-range behavior**: Values are clamped to [1000, 2000]
- **Clamping function** (from servo.c):
  ```c
  int clampVal(int val){
      int newVal = 1000 * (val < 1000) + val * (1 - (val < 1000));
      newVal = 2000 * (val > 2000) + val * (1 - (val > 2000));
      return newVal;
  }
  ```

## Initialization and Arming

1. **Startup**: When the STM initializes, it arms the ESCs by setting them to stop/neutral (1500 µs) for 3 seconds
2. **Motor Armed Flag**: After this period, `motors_armed_flag` is set to 1
3. **Before Arming**: Incoming UART packets are received but **not processed**
4. **After Arming**: Both ESC and servo commands are processed from incoming packets

## Implementation Details

### Processing Function
```c
int process(uint8_t* packet){
  int vals[RX_PACKET_SIZE];  // RX_PACKET_SIZE = 8 (8 integers)
  memcpy(vals, packet, sizeof(int) * RX_PACKET_SIZE);

  // Process ESC motors (indices 0-7)
  for (int i = 0; i < 8; i++){
    setESC(escs[i], vals[i]);
  }

  // Process servo motors (indices 8-11)
  for (int i = 8; i < 12; i++){
    setServo(servos[i-8], vals[i]);
  }
  return 1;
}
```

### DMA Callbacks
- **`HAL_UART_RxHalfCpltCallback`**: Processes packet A (first 32 bytes) when buffer is half-full
- **`HAL_UART_RxCpltCallback`**: Processes packet B (second 32 bytes) when buffer is completely full

Both callbacks check `motors_armed_flag` before processing.

## Example Packet Construction

To send a command controlling all motors:

### Python Example
```python
import struct
import serial

# Create packet with 12 integers (8 ESCs + 4 servos)
escs = [1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500]  # 1500 = stop, 1100 = reverse, 1900 = full forward
servos = [1500, 1500, 1500, 1500]  # Neutral for all servos (if armed)

# Pack all 12 values as little-endian signed 32-bit integers
packet = b''
for value in escs + servos:
    packet += struct.pack('<i', value)  # '<i' = little-endian signed int

# Send via serial
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
ser.write(packet)
ser.close()
```

### C Example
```c
#include <string.h>
#include <stdint.h>

int escs[12] = {1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 
                 1500, 1500, 1500, 1500};  // 8 ESCs + 4 servos

uint8_t packet[48];  // 12 * 4 bytes
memcpy(packet, escs, sizeof(escs));

// Send packet via UART
HAL_UART_Transmit(&huart2, packet, 48, HAL_MAX_DELAY);
```

## Timing Considerations

- **Update Hz**: Limited by communication timing and DMA processing
- **Double Buffering**: Allows overlap between receive and process cycles
- **Processing Delay**: Minimal; typically microseconds after packet reception

## Troubleshooting

### Motors Not Responding
1. **Check arming**: Verify 3+ seconds have passed since STM startup
2. **Check serial connection**: Verify baud rate is 115200
3. **Check packet format**: Ensure binary format, not ASCII
4. **Check value ranges**: ESCs must be 1100-1900; servos 1000-2000

### Incomplete Commands
1. Always send exactly 32 bytes per packet
2. Use double-buffering pattern: send packets 0, then packets 1, alternating
3. Verify little-endian byte order

### Serial Port Issues
- Use `115200` baud only
- On Linux: Check `/dev/ttyUSB0` or `/dev/ttyACM0` availability
- On Windows: Check COM port assignment in Device Manager

## Files Reference

- **Core/Src/main.c**: Main initialization, UART setup, DMA callbacks
- **Custom/Src/esc.c**: ESC control and clamping logic
- **Custom/Src/servo.c**: Servo control and clamping logic
- **Custom/Inc/esc.h**: ESC structure definition
- **Custom/Inc/servo.h**: Servo structure definition
