#pragma once
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"

extern QueueHandle_t dsp_queue;

void state_machine_init(void);
void state_machine_task_func(void *pvParameters);
void state_machine_notify_done(void);
