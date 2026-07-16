#include "state_machine.h"
#include "config.h"
#include "inputs.h"
#include "solenoid.h"
#include "audio_i2s.h"
#include "storage_fat.h"
#include "usb_msc.h"
#include "led_status.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "driver/i2s_std.h"

static const char *TAG = "STATE_MACHINE";

typedef enum {
    STATE_BOOT_INIT,
    STATE_IDLE,
    STATE_DEBOUNCE,
    STATE_STRIKE,
    STATE_DEADTIME,
    STATE_ACQUIRE,
    STATE_WAIT_PROCESS,
    STATE_SAFE_UNMOUNT,
    STATE_USB_MSC_MODE,
    STATE_REMOUNT
} system_state_t;

QueueHandle_t dsp_queue;
static SemaphoreHandle_t process_done_sem;

void state_machine_init(void) {
    dsp_queue = xQueueCreate(2, sizeof(hit_label_t));
    process_done_sem = xSemaphoreCreateBinary();
}

void state_machine_notify_done(void) {
    xSemaphoreGive(process_done_sem);
}

void state_machine_task_func(void *pvParameters) {
    system_state_t current_state = STATE_BOOT_INIT;
    bool in_msc_mode = false;
    hit_label_t current_label;

    while (1) {
        switch (current_state) {
            case STATE_BOOT_INIT:
                ESP_LOGI(TAG, "Boot Init");
                current_state = STATE_IDLE;
                break;

            case STATE_IDLE:
                led_status_set_mode(LED_MODE_IDLE);
                if (inputs_is_upload_mode_pressed()) {
                    current_state = STATE_SAFE_UNMOUNT;
                } else if (inputs_is_trigger_pressed()) {
                    current_state = STATE_DEBOUNCE;
                } else {
                    vTaskDelay(pdMS_TO_TICKS(10));
                }
                break;

            case STATE_DEBOUNCE:
                vTaskDelay(pdMS_TO_TICKS(DEBOUNCE_MS));
                if (inputs_is_trigger_pressed()) {
                    current_state = STATE_STRIKE;
                } else {
                    current_state = STATE_IDLE;
                }
                break;

            case STATE_STRIKE:
                ESP_LOGI(TAG, "Strike");
                led_status_set_mode(LED_MODE_BUSY);
                current_label = inputs_read_current_label();
                solenoid_strike();
                current_state = STATE_DEADTIME;
                break;

            case STATE_DEADTIME:
                vTaskDelay(pdMS_TO_TICKS(DEADTIME_MS));
                current_state = STATE_ACQUIRE;
                break;

            case STATE_ACQUIRE:
                ESP_LOGI(TAG, "Acquiring I2S data");
                size_t bytes_read;
                esp_err_t err = i2s_channel_read(rx_handle, raw_i2s_buf, FFT_N * sizeof(int32_t), &bytes_read, portMAX_DELAY);
                if (err == ESP_OK) {
                    xQueueSend(dsp_queue, &current_label, portMAX_DELAY);
                    current_state = STATE_WAIT_PROCESS;
                } else {
                    ESP_LOGE(TAG, "I2S Read Error");
                    led_status_set_mode(LED_MODE_ERROR);
                    vTaskDelay(pdMS_TO_TICKS(1000));
                    current_state = STATE_IDLE;
                }
                break;

            case STATE_WAIT_PROCESS:
                
                if (xSemaphoreTake(process_done_sem, pdMS_TO_TICKS(1000)) == pdTRUE) {
                    current_state = STATE_IDLE;
                } else {
                    ESP_LOGE(TAG, "DSP Processing Timeout");
                    led_status_set_mode(LED_MODE_ERROR);
                    vTaskDelay(pdMS_TO_TICKS(1000));
                    current_state = STATE_IDLE;
                }
                break;

            case STATE_SAFE_UNMOUNT:
                ESP_LOGI(TAG, "Safe unmount for MSC");
                storage_unmount();
                current_state = STATE_USB_MSC_MODE;
                break;

            case STATE_USB_MSC_MODE:
                if (!in_msc_mode) {
                    usb_msc_enter_mode(s_wl_handle);
                    in_msc_mode = true;
                    
                    vTaskDelay(pdMS_TO_TICKS(500));
                }

                
                if (inputs_is_upload_mode_pressed()) {
                    usb_msc_exit_mode();
                    in_msc_mode = false;
                    vTaskDelay(pdMS_TO_TICKS(500)); 
                    current_state = STATE_REMOUNT;
                } else {
                    vTaskDelay(pdMS_TO_TICKS(100));
                }
                break;

            case STATE_REMOUNT:
                ESP_LOGI(TAG, "Remounting FATFS");
                if (storage_mount() == ESP_OK) {
                    current_state = STATE_IDLE;
                } else {
                    current_state = STATE_SAFE_UNMOUNT; 
                    led_status_set_mode(LED_MODE_ERROR);
                    vTaskDelay(pdMS_TO_TICKS(1000));
                }
                break;
        }
    }
}
