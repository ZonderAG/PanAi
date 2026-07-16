#pragma once
#include <stdbool.h>
#include <stdint.h>

void uart_comm_init(void);
bool uart_comm_check_strike_cmd(void);
void uart_comm_send_spectrum(int16_t *data, uint16_t length);
