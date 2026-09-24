// Build against the NKIOSDK 5.0.4 NKLCLIB.h supplied by Nodka.
// Keep the vendor's by-value union callback entirely inside C++.
#include "NKLCLIB.h"
#include <cstdint>
#include <mutex>

struct LightResult {
    int32_t sdk_return;
    uint32_t received, error, error_id, port, device, channel;
    uint32_t mode, brightness, on;
};

namespace {
std::mutex operation_mutex;
std::mutex result_mutex;
LightResult current{};

void open_callback(LC_CALLBACK_ARG_T value) {
    std::lock_guard<std::mutex> guard(result_mutex);
    const auto &v = value.openComCallbackArg;
    current.received = 1;
    current.error = v.error;
    current.error_id = v.errorId;
    current.port = v.portNum;
    current.device = v.devId;
}
void close_callback(LC_CALLBACK_ARG_T value) {
    std::lock_guard<std::mutex> guard(result_mutex);
    current.received = 1;
    current.error = value.closeComCallbackArg.error;
    current.error_id = value.closeComCallbackArg.errorId;
}
void set_callback(LC_CALLBACK_ARG_T value) {
    std::lock_guard<std::mutex> guard(result_mutex);
    current.received = 1;
    current.error = value.setPwmParamsCallbackArg.error;
    current.error_id = value.setPwmParamsCallbackArg.errorId;
    current.channel = value.setPwmParamsCallbackArg.chIdx;
}
void get_callback(LC_CALLBACK_ARG_T value) {
    std::lock_guard<std::mutex> guard(result_mutex);
    const auto &v = value.getPwmParamsCallbackArg;
    current.received = 1;
    current.error = v.error;
    current.error_id = v.errorId;
    current.channel = v.chIdx;
    current.mode = v.pwmMode;
    current.brightness = v.pwmValue;
    current.on = v.pwmOnOff;
}
template <typename Function>
void execute(LightResult *output, Function function) {
    std::lock_guard<std::mutex> operation_guard(operation_mutex);
    {
        std::lock_guard<std::mutex> guard(result_mutex);
        current = {};
    }
    // Non-Async SDK calls complete their callback before returning.
    const int code = function();
    std::lock_guard<std::mutex> guard(result_mutex);
    current.sdk_return = code;
    *output = current;
}
}

extern "C" {
int agv_light_init(const char *config) { return NKLC_LibraryInit(config); }
void agv_light_deinit() { NKLC_LibraryDeinit(); }
void agv_light_open(uint16_t port, LightResult *output) {
    execute(output, [=] { return NKLC_OpenDevice(port, open_callback); });
}
void agv_light_close(uint16_t port, LightResult *output) {
    execute(output, [=] { return NKLC_CloseDevice(port, close_callback); });
}
void agv_light_set(uint32_t device, uint8_t channel, uint8_t brightness,
                   uint8_t on, LightResult *output) {
    execute(output, [=] {
        return NKLC_SetPwmParams(device, channel, 0, brightness, 0, on, set_callback);
    });
}
void agv_light_get(uint32_t device, uint8_t channel, LightResult *output) {
    execute(output, [=] { return NKLC_GetPwmParams(device, channel, get_callback); });
}
}
