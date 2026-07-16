#pragma once

#include "driver/gpio.h"
#include "driver/uart.h"

#define MCLK_GPIO GPIO_NUM_17
#define BCLK_GPIO GPIO_NUM_16
#define WS_GPIO   GPIO_NUM_15
#define DIN_GPIO  GPIO_NUM_18

#define SOLENOID_GPIO        GPIO_NUM_4

#define LED_STATUS_GPIO GPIO_NUM_8
#define LED_UPLOAD_GPIO GPIO_NUM_9

#define UART_PORT UART_NUM_0
#define UART_TX_PIN UART_PIN_NO_CHANGE
#define UART_RX_PIN UART_PIN_NO_CHANGE

#define SOLENOID_PULSE_MS 20
#define DEADTIME_MS       5

#define I2S_SAMPLE_RATE 48000
#define FFT_N           4096

#define BIN_FREQ_LO_HZ  1000
#define BIN_FREQ_HI_HZ  20000
#define BIN_RESOLUTION  ((float)I2S_SAMPLE_RATE / FFT_N)
#define BIN_START       ((int)(BIN_FREQ_LO_HZ / BIN_RESOLUTION))
#define BIN_END         ((int)(BIN_FREQ_HI_HZ / BIN_RESOLUTION))
#define NUM_CROPPED_BINS (BIN_END - BIN_START + 1)
