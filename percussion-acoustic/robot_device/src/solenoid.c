#include "solenoid.h"
#include "config.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

void solenoid_init(void) {
    gpio_config_t io_conf = {
        .intr_type = GPIO_INTR_DISABLE,
        .mode = GPIO_MODE_OUTPUT,
        .pin_bit_mask = (1ULL << SOLENOID_GPIO),
        .pull_down_en = 0,
        .pull_up_en = 0
    };
    gpio_config(&io_conf);
    gpio_set_level(SOLENOID_GPIO, 0);
}

void solenoid_strike(void) {
    gpio_set_level(SOLENOID_GPIO, 1);
    vTaskDelay(pdMS_TO_TICKS(SOLENOID_PULSE_MS));
    gpio_set_level(SOLENOID_GPIO, 0);
}
