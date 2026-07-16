#include "state_machine.h"
#include "config.h"
#include "uart_comm.h"
#include "solenoid.h"
#include "audio_i2s.h"
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
    STATE_STRIKE,
    STATE_DEADTIME,
    STATE_ACQUIRE,
    STATE_WAIT_PROCESS
} system_state_t;

QueueHandle_t dsp_queue;
static SemaphoreHandle_t process_done_sem;

void state_machine_init(void) {
    dsp_queue = xQueueCreate(2, sizeof(uint8_t));
    process_done_sem = xSemaphoreCreateBinary();
}

void state_machine_notify_done(void) {
    xSemaphoreGive(process_done_sem);
}

void state_machine_task_func(void *pvParameters) {
    system_state_t current_state = STATE_BOOT_INIT;
    uint8_t dummy_item = 0;

    while (1) {
        switch (current_state) {
            case STATE_BOOT_INIT:
                ESP_LOGI(TAG, "Boot Init");
                current_state = STATE_IDLE;
                break;

            case STATE_IDLE:
                led_status_set_mode(LED_MODE_IDLE);
                if (uart_comm_check_strike_cmd()) {
                    current_state = STATE_STRIKE;
                } else {
                    vTaskDelay(pdMS_TO_TICKS(10));
                }
                break;

            case STATE_STRIKE:
                ESP_LOGI(TAG, "Strike");
                led_status_set_mode(LED_MODE_BUSY);
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
                    xQueueSend(dsp_queue, &dummy_item, portMAX_DELAY);
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
        }
    }
}
