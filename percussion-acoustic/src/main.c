#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "config.h"
#include "audio_i2s.h"
#include "dsp_pipeline.h"
#include "solenoid.h"
#include "inputs.h"
#include "storage_fat.h"
#include "led_status.h"
#include "state_machine.h"

static const char *TAG = "MAIN";

void app_main(void) {
    ESP_LOGI(TAG, "Starting UAM Firmware initialization");

    
    led_status_init();
    inputs_init();
    solenoid_init();
    
    dsp_pipeline_init();
    audio_i2s_init();
    
    
    esp_err_t err = storage_mount();
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Storage mount failed!");
        led_status_set_mode(LED_MODE_ERROR);
        
    }

    
    state_machine_init();

    
    
    xTaskCreate(fft_process_task_func, "dsp_task", 8192, NULL, 5, NULL);
    
    
    xTaskCreate(led_status_task_func, "led_task", 2048, NULL, 1, NULL);

    
    xTaskCreate(state_machine_task_func, "state_machine_task", 8192, NULL, 10, NULL);

    ESP_LOGI(TAG, "Initialization complete");
}
