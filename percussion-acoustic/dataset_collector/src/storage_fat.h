#pragma once
#include <stdint.h>
#include "esp_err.h"
#include "inputs.h"
#include "wear_levelling.h"

extern wl_handle_t s_wl_handle;

esp_err_t storage_mount(void);
esp_err_t storage_unmount(void);
void storage_fat_write_hit(int16_t *magnitude_db100, int num_bins, hit_label_t label);
