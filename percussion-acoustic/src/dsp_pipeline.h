#pragma once
#include <stdint.h>
#include "inputs.h"

extern float *fft_complex;
extern float *fft_window;
extern float *magnitude;
extern int32_t *raw_i2s_buf;

void dsp_pipeline_init(void);
void fft_process_task_func(void *pvParameters);
