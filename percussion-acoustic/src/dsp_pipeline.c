#include "dsp_pipeline.h"
#include "config.h"
#include "esp_dsp.h"
#include "esp_log.h"
#include "esp_heap_caps.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "storage_fat.h"
#include "state_machine.h"
#include <math.h>

static const char *TAG = "DSP";

float *fft_complex = NULL;
float *fft_window = NULL;
float *magnitude = NULL;
int32_t *raw_i2s_buf = NULL;

void dsp_pipeline_init(void) {
    ESP_LOGI(TAG, "Allocating DSP buffers in PSRAM");
    raw_i2s_buf = (int32_t *)heap_caps_malloc(FFT_N * sizeof(int32_t), MALLOC_CAP_SPIRAM);
    fft_complex = (float *)heap_caps_malloc(2 * FFT_N * sizeof(float), MALLOC_CAP_SPIRAM);
    fft_window = (float *)heap_caps_malloc(FFT_N * sizeof(float), MALLOC_CAP_SPIRAM);
    magnitude = (float *)heap_caps_malloc((FFT_N/2 + 1) * sizeof(float), MALLOC_CAP_SPIRAM);

    assert(raw_i2s_buf && fft_complex && fft_window && magnitude);

    ESP_ERROR_CHECK(dsps_fft2r_init_fc32(NULL, FFT_N));
    dsps_wind_hann_f32(fft_window, FFT_N);
}

void fft_process_task_func(void *pvParameters) {
    while (1) {
        hit_label_t label;
        if (xQueueReceive(dsp_queue, &label, portMAX_DELAY) == pdTRUE) {
            ESP_LOGI(TAG, "Processing FFT");

            
            for (int i = 0; i < FFT_N; i++) {
                int32_t s24 = raw_i2s_buf[i] >> 8;
                float norm = (float)s24 / 8388608.0f;
                fft_complex[2*i + 0] = norm * fft_window[i];
                fft_complex[2*i + 1] = 0.0f;
            }

            
            dsps_fft2r_fc32(fft_complex, FFT_N);
            dsps_bit_rev_fc32(fft_complex, FFT_N);

            
            
            int16_t *mag_int16 = (int16_t *)magnitude; 
            for (int k = BIN_START; k <= BIN_END; k++) {
                float re = fft_complex[2*k + 0];
                float im = fft_complex[2*k + 1];
                float amp = sqrtf(re*re + im*im);
                float db = (amp > 1e-6f) ? 20.0f * log10f(amp) : -120.0f;
                mag_int16[k - BIN_START] = (int16_t)(db * 100.0f); 
            }

            storage_fat_write_hit(mag_int16, NUM_CROPPED_BINS, label);
            
            
            state_machine_notify_done();
        }
    }
}
