#pragma once
#include <stdint.h>
#include "driver/i2s_std.h"

extern i2s_chan_handle_t rx_handle;
extern int32_t *raw_i2s_buf;

void audio_i2s_init(void);
