#include "Arduino.h"
#include <CircularBuffer.h>
#include <ezTime.h>

typedef struct {
  time_t epoch;
  char message[75];
} LogData;

CircularBuffer<LogData, 35> log_buffer;
LogData log_record;

void log_header_printf(String &web_debug_info_header, const char *format, ...) {
  char message[100];

  va_list arg;
  va_start(arg, format);
  vsnprintf(message, sizeof(message), format, arg);
  va_end(arg);

  String str_message = String(message);
  str_message.replace("\n", "");
  web_debug_info_header +=
      "<b>" + UTC.dateTime() + " - " + str_message + "</b><br>\n";
}

void log_printf(const char *format, ...) {
  LogData new_value{UTC.now()};
  va_list arg;
  va_start(arg, format);
  vsnprintf(new_value.message, sizeof(new_value.message), format, arg);
  va_end(arg);
  Serial.print(new_value.message);
  log_buffer.push(new_value);
}

void log_print(const char *str) {
  LogData new_value{UTC.now()};
  snprintf(new_value.message, sizeof(new_value.message), "%s", str);
  Serial.print(new_value.message);
  log_buffer.push(new_value);
}
void log_print(const String str) { log_print(str.c_str()); }

void log_println(const char *str) {
  LogData new_value{UTC.now()};
  snprintf(new_value.message, sizeof(new_value.message), "%s", str);
  Serial.println(new_value.message);
  log_buffer.push(new_value);
}
void log_println(const String str) { log_println(str.c_str()); }
