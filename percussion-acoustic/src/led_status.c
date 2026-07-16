#include "led_status.h"
#include "config.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static led_mode_t current_mode = LED_MODE_IDLE;

void led_status_init(void) {
    gpio_config_t io_conf = {
        .intr_type = GPIO_INTR_DISABLE,
        .mode = GPIO_MODE_OUTPUT,
        .pin_bit_mask = (1ULL << LED_STATUS_GPIO) | (1ULL << LED_UPLOAD_GPIO),
        .pull_down_en = 0,
        .pull_up_en = 0
    };
    gpio_config(&io_conf);
    
    gpio_set_level(LED_STATUS_GPIO, 1);
    gpio_set_level(LED_UPLOAD_GPIO, 0);
}

void led_status_set_mode(led_mode_t mode) {
    current_mode = mode;
}

void led_status_task_func(void *pvParameters) {
    int toggle = 0;
    while (1) {
        switch (current_mode) {
            case LED_MODE_IDLE:
                gpio_set_level(LED_STATUS_GPIO, 1);
                vTaskDelay(pdMS_TO_TICKS(100));
                break;
            case LED_MODE_BUSY:
                gpio_set_level(LED_STATUS_GPIO, toggle);
                toggle = !toggle;
                vTaskDelay(pdMS_TO_TICKS(100)); 
                break;
            case LED_MODE_ERROR:
                gpio_set_level(LED_STATUS_GPIO, toggle);
                toggle = !toggle;
                vTaskDelay(pdMS_TO_TICKS(50)); 
                break;
        }
    }
}
