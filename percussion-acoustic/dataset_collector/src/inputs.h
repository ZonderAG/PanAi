#pragma once
#include <stdbool.h>

typedef enum { LABEL_NORMAL = 0, LABEL_DEFECT = 1 } hit_label_t;

void inputs_init(void);
bool inputs_is_trigger_pressed(void);
bool inputs_is_upload_mode_pressed(void);
hit_label_t inputs_read_current_label(void);
