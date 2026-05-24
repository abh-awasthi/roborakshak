# Hardware Setup

## Components
- Raspberry Pi 4 Model B
- L298N motor driver
- 4 BO motors
- Pi Camera
- LM2596 Buck Converter
- 12V Li-ion battery

## GPIO Mapping

| Raspberry Pi | L298N |
|---|---|
| GPIO5 (Pin 29) | IN1 |
| GPIO6 (Pin 31) | IN2 |
| GPIO13 (Pin 33) | IN3 |
| GPIO19 (Pin 35) | IN4 |
| GND | GND |

## Power Connections

Battery + → L298N 12V
Battery - → L298N GND

LM2596 OUT+ → Pi Pin 2
LM2596 OUT- → Pi Pin 6
