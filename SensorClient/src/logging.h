#include "Arduino.h"
#include <ezTime.h>
#include <CircularBuffer.h>

typedef struct
{
    time_t epoch;
    char message[75];
} LogData;

CircularBuffer<LogData, 45> log_buffer;
LogData log_record;

void log_printf(const char *format, ...)
{
    LogData new_value{UTC.now()};
    va_list arg;
    va_start(arg, format);
    vsnprintf(new_value.message, sizeof(new_value.message), format, arg);
    va_end(arg);
    Serial.print(new_value.message);
    log_buffer.push(new_value);
}
void log_print(const char *str)
{
    LogData new_value{UTC.now()};
    snprintf(new_value.message, sizeof(new_value.message), "%s", str);
    Serial.print(new_value.message);
    log_buffer.push(new_value);
}
void log_print(const String str)
{
    log_print(str.c_str());
}
void log_println(const char *str)
{
    LogData new_value{UTC.now()};
    snprintf(new_value.message, sizeof(new_value.message), "%s", str);
    Serial.println(new_value.message);
    log_buffer.push(new_value);
}
void log_println(const String str)
{
    log_println(str.c_str());
}
