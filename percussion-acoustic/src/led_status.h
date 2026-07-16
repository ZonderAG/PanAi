#pragma once

typedef enum {
    LED_MODE_IDLE,
    LED_MODE_BUSY,
    LED_MODE_ERROR
} led_mode_t;

void led_status_init(void);
void led_status_set_mode(led_mode_t mode);
void led_status_task_func(void *pvParameters);
