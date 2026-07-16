#include "storage_fat.h"
#include "esp_vfs_fat.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "config.h"
#include "esp_rom_crc.h"
#include <string.h>
#include <sys/stat.h>

static const char *TAG = "STORAGE";

wl_handle_t s_wl_handle = WL_INVALID_HANDLE;
static uint32_t current_hit_id = 0;
static const char *NVS_NAMESPACE = "uam";
static const char *NVS_KEY_HIT_ID = "hit_id";

#pragma pack(push, 1)
typedef struct {
    uint8_t  magic[4];        
    uint8_t  format_version;  
    uint8_t  label;           
    uint8_t  data_format;     
    uint8_t  reserved0;
    uint32_t hit_id;
    uint32_t timestamp_ms;
    uint32_t sample_rate_hz;
    uint16_t fft_n;
    uint16_t bin_start;
    uint16_t bin_end;
    uint16_t num_bins;
    uint32_t crc32;
} hit_file_header_t;
#pragma pack(pop)

static void init_nvs_hit_id(void) {
    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        err = nvs_flash_init();
    }
    ESP_ERROR_CHECK(err);

    nvs_handle_t my_handle;
    err = nvs_open(NVS_NAMESPACE, NVS_READWRITE, &my_handle);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Error opening NVS handle!");
        return;
    }
    err = nvs_get_u32(my_handle, NVS_KEY_HIT_ID, &current_hit_id);
    switch (err) {
        case ESP_OK:
            ESP_LOGI(TAG, "Restored hit_id = %lu from NVS", current_hit_id);
            break;
        case ESP_ERR_NVS_NOT_FOUND:
            ESP_LOGI(TAG, "The value is not initialized yet, setting to 0!");
            current_hit_id = 0;
            break;
        default :
            ESP_LOGE(TAG, "Error reading hit_id from NVS");
    }
    nvs_close(my_handle);
}

static void save_nvs_hit_id(void) {
    nvs_handle_t my_handle;
    esp_err_t err = nvs_open(NVS_NAMESPACE, NVS_READWRITE, &my_handle);
    if (err == ESP_OK) {
        nvs_set_u32(my_handle, NVS_KEY_HIT_ID, current_hit_id);
        nvs_commit(my_handle);
        nvs_close(my_handle);
    }
}

esp_err_t storage_mount(void) {
    init_nvs_hit_id();

    const esp_vfs_fat_mount_config_t mount_config = {
        .max_files = 8,
        .format_if_mount_failed = true,
        .allocation_unit_size = CONFIG_WL_SECTOR_SIZE,
    };
    esp_err_t err = esp_vfs_fat_spiflash_mount_rw_wl("/data", "storage", &mount_config, &s_wl_handle);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to mount FATFS (%s)", esp_err_to_name(err));
        return err;
    }
    ESP_LOGI(TAG, "FATFS mounted");
    
    
    mkdir("/data/SHIFT", 0775);

    return ESP_OK;
}

esp_err_t storage_unmount(void) {
    if (s_wl_handle == WL_INVALID_HANDLE) return ESP_OK;
    esp_err_t err = esp_vfs_fat_spiflash_unmount_rw_wl("/data", s_wl_handle);
    if (err == ESP_OK) {
        s_wl_handle = WL_INVALID_HANDLE;
        ESP_LOGI(TAG, "FATFS unmounted");
    }
    return err;
}

void storage_fat_write_hit(int16_t *magnitude_db100, int num_bins, hit_label_t label) {
    current_hit_id++;
    save_nvs_hit_id();

    char filename[64];
    snprintf(filename, sizeof(filename), "/data/SHIFT/%c%06lu.BIN", 
             (label == LABEL_NORMAL) ? 'N' : 'D', 
             current_hit_id);

    FILE *f = fopen(filename, "wb");
    if (f == NULL) {
        ESP_LOGE(TAG, "Failed to open file for writing: %s", filename);
        return;
    }

    hit_file_header_t header = {
        .magic = {'U', 'A', 'M', '1'},
        .format_version = 1,
        .label = (uint8_t)label,
        .data_format = 2, 
        .reserved0 = 0,
        .hit_id = current_hit_id,
        .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000ULL),
        .sample_rate_hz = I2S_SAMPLE_RATE,
        .fft_n = FFT_N,
        .bin_start = BIN_START,
        .bin_end = BIN_END,
        .num_bins = num_bins,
    };

    header.crc32 = esp_rom_crc32_le(0, (uint8_t*)magnitude_db100, num_bins * sizeof(int16_t));

    fwrite(&header, sizeof(hit_file_header_t), 1, f);
    fwrite(magnitude_db100, sizeof(int16_t), num_bins, f);
    fclose(f);

    ESP_LOGI(TAG, "Wrote hit file: %s", filename);
}
