# # SPDX-FileCopyrightText: 2018 Kattni Rembor for Adafruit Industries
# #
# # SPDX-License-Identifier: MIT

# """CircuitPython Essentials PWM with variable frequency piezo example"""
# import time
# import board
# import pwmio

# # For the M0 boards:
# piezo = pwmio.PWMOut(board.D13, duty_cycle=0, frequency=100, variable_frequency=True)

# # For the M4 boards:
# # piezo = pwmio.PWMOut(board.A1, duty_cycle=0, frequency=440, variable_frequency=True)

# while True:
#     for f in (100, 200, 300):
#         piezo.frequency = f
#         print(f"on at {f}(true hz:{piezo.frequency}")
#         piezo.duty_cycle = 65535 // 2  # On 50%
#         time.sleep(15)  # On for 1/4 second
#         piezo.duty_cycle = 0  # Off
#         print(f"off at {f}(true hz:{piezo.frequency}")
#         time.sleep(15)  # Pause between notes
#     time.sleep(0.5)

# SPDX-FileCopyrightText: 2024 Tyeth Gundry
# SPDX-License-Identifier: MIT

#TODO: Add Adafruit IO feeds for BME688.
#TODO: Add scaled output to air quality feed from scaled air sensor (CO2/PM2.5/gas-ohms)
#TODO: swap to using rotary switch inputs ( max_events=1 ) with keypad.keys:
# https://docs.circuitpython.org/en/latest/shared-bindings/keypad/index.html#keypad.Keys

#NO LONGER TRUE, WAS FOR QTPY-S2, NOW ITSYBITSY ESP32 - different pinouts
# the dotstar should use SPI pins, they'll be natively better setup for it.
# Neopixel on A3, POT on A2, dotstar on gpio 35+36, tacho on MISO,  4PST on
# A0(GPIO18),A1(GPIO17),SDA (GPIO7),SCL, mosfet on TX (GPIO5)
#
# NeoPixel on A3 (GPIO8)
# Potentiometer on A2 (GPIO9)
# DotStar on SPI pins:
# Data on GPIO35 (SCK)
# Clock on GPIO36 (MOSI)
# Tachometer Input on MISO (GPIO37)
# 4PST Rotary Switch:
# Pole 1 on A0 (GPIO18)
# Pole 2 on A1 (GPIO17)
# Pole 3 on SDA (GPIO7)
# Pole 4 on SCL (GPIO8)
# MOSFET Output on TX (GPIO5)

import time
import board
from rainbowio import colorwheel
import neopixel
import asyncio
import analogio
import digitalio
import os
import busio
# import adafruit_dotstar as dotstar
import countio
import pwmio
import traceback
import sys
import math
import socketpool
import ssl
import wifi
import adafruit_requests

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

from adafruit_io.adafruit_io import IO_HTTP, AdafruitIO_RequestError
import sys
CIRCUITPYTHON_AIO_USERNAME=os.getenv("CIRCUITPY_AIO_USERNAME", "YOUR_USERNAME_HERE")
CIRCUITPYTHON_AIO_KEY=os.getenv("CIRCUITPY_AIO_KEY", 'YOUR_KEY')
ADAFRUIT_IO_USERNAME = os.getenv('ADAFRUIT_IO_USERNAME', CIRCUITPYTHON_AIO_USERNAME)
ADAFRUIT_IO_KEY = os.getenv('ADAFRUIT_IO_KEY', CIRCUITPYTHON_AIO_KEY)

STATUS_NEOPIXEL_PIN = board.NEOPIXEL
STATUS_NEOPIXEL_NUMPIXELS = 1
STATUS_NEOPIXEL_BRIGHTNESS = 0.01
try:
    STATUS_NEOPIXEL_BRIGHTNESS = float(str(os.getenv("STATUS_NEOPIXEL_BRIGHTNESS", STATUS_NEOPIXEL_BRIGHTNESS)))
    if STATUS_NEOPIXEL_BRIGHTNESS <= 0.005:
        STATUS_NEOPIXEL_BRIGHTNESS = 0.0079
except Exception as e:
    print(f"Failed to read brightness from settings.toml: {e}")
finally:
    print(f"Status NeoPixel Brightness: {STATUS_NEOPIXEL_BRIGHTNESS*100}% ({STATUS_NEOPIXEL_BRIGHTNESS})")

# #turn on neopixel power if required (on by default for most boards, sometimes called I2C_POWER or NEO_I2C_POWER)
# NEOPIXEL_POWER = digitalio.DigitalInOut(board.NEOPIXEL_POWER)
# NEOPIXEL_POWER.direction = digitalio.Direction.OUTPUT
# NEOPIXEL_POWER.value = True
status_neopixel = neopixel.NeoPixel(STATUS_NEOPIXEL_PIN, STATUS_NEOPIXEL_NUMPIXELS)#, brightness=STATUS_NEOPIXEL_BRIGHTNESS, auto_write=False, pixel_order=neopixel.GRB)
status_neopixel.brightness = STATUS_NEOPIXEL_BRIGHTNESS
status_neopixel[0] = (0, 255, 0)

# if feeds dont exist then create them if this is TRUE:
CREATE_FEEDS = True
FAN_SPEED_FEEDNAME = os.getenv("FAN_SPEED_FEEDNAME", "fan-speed3")
AIR_QUALITY_FEEDNAME = os.getenv("AIR_QUALITY_FEEDNAME", "ecda3bbc63d4-seeed-xiao-esp32c3-sen5x-ppm-2-dot-5")

NEOPIXEL_NUMPIXELS = 13  # Update this to match the number of LEDs.
SPEED = 0.05  # Increase to slow down the rainbow. Decrease to speed it up.
NEOPIXEL_BRIGHTNESS = 0.1 # 0.05  # A number between 0.0 and 1.0, where 0.0 is off, and 1.0 is max.
NEOPIXEL_PIN = board.D5  # This is the default pin on the 5x5 NeoPixel Grid BFF.
# POTENTIOMETER_PIN = board.A2 # control knob
FAN_TACHO_PIN = board.D12 #board.MISO
FAN_PWM_OUTPUT = board.D13 # 50% power always, vary frequency between 60-300Hz, but use 100Hz for 2secs from stopped then drop to desired level (if below 100 otherwise start at desired level).

#rotart switch pins: common[1]-resistor-ground, D7[2],D32[3],D33[4],D14[5]
ROTARY_SWITCH_PINS = [board.D7, board.D32, board.D33, board.D14] # 4PST rotary switch - Off, Low, Medium, High
switch_pins = []

# DOTSTAR_NUMPIXELS=24
# DOTSTAR_DATA_PIN = board.D35
# DOTSTAR_CLOCK_PIN = board.D36
# DOTSTAR_BRIGHTNESS = 0.5

# Set up tachometer on MISO (GPIO37)
tach_counter = countio.Counter(FAN_TACHO_PIN)

FAN_SPEED_PWM_FREQUENCY = 300
fan_speed = 0
fan_pwm_output = pwmio.PWMOut(FAN_PWM_OUTPUT, frequency=FAN_SPEED_PWM_FREQUENCY, duty_cycle=0, variable_frequency=True)

neopixels = neopixel.NeoPixel(NEOPIXEL_PIN, NEOPIXEL_NUMPIXELS, brightness=NEOPIXEL_BRIGHTNESS, auto_write=False, pixel_order=neopixel.GRB)

# # DotStar setup
# dots = dotstar.DotStar(clock=DOTSTAR_CLOCK_PIN, data=DOTSTAR_DATA_PIN, n=DOTSTAR_NUMPIXELS, brightness=DOTSTAR_BRIGHTNESS, auto_write=False, pixel_order=dotstar.BGR)

# #Input potentiometer for manual speed / noise adjustment
# potentiometer = analogio.AnalogIn(POTENTIOMETER_PIN)

CURRENT_AIR_QUALITY_MULITPLIER = 100

CURRENT_NOISE_LEVEL = 1

async def read_rotary_switch(read_interval=1):
    global ROTARY_SWITCH_PINS, CURRENT_NOISE_LEVEL, switch_pins
    for i in range(4):
        print(f"setup rotary pin {i+1}: {ROTARY_SWITCH_PINS[i]}")
        newpin = digitalio.DigitalInOut(ROTARY_SWITCH_PINS[i])
        newpin.direction = digitalio.Direction.INPUT
        newpin.pull = digitalio.Pull.UP
        switch_pins.append(newpin)
        print(f"Rotary position #{i+1}: {switch_pins[i].value}")
    while True:
        for i in range(4):
            if not switch_pins[i].value:
                if CURRENT_NOISE_LEVEL != i:
                    CURRENT_NOISE_LEVEL = i
                    print()
                    print(f"Rotary switch position: {i} [Current noise level]")
                    # publish new fan_speed to Adafruit IO
                    await publish_new_fan_speed(i)
        await asyncio.sleep(read_interval)


async def fan_speed_control():
    global fan_speed, FAN_SPEED_PWM_FREQUENCY, CURRENT_NOISE_LEVEL, CURRENT_AIR_QUALITY_MULITPLIER, fan_pwm_output
    FAN_SPEED_PWM_FREQUENCY = 100
    NOISE_LEVEL_1_MAX_FAN_FREQUENCY = os.getenv("NOISE_LEVEL_1_MAX_FAN_FREQUENCY", 140)
    NOISE_LEVEL_2_MAX_FAN_FREQUENCY = os.getenv("NOISE_LEVEL_2_MAX_FAN_FREQUENCY", 220)
    NOISE_LEVEL_3_MAX_FAN_FREQUENCY = os.getenv("NOISE_LEVEL_3_MAX_FAN_FREQUENCY", 300)
    while True:
        # 16-bit PWM 50% duty cycle
        FAN_SPEED_PWM_DUTY_CYCLE = 32768
        clean_fan_speed = min(3, max(0, fan_speed))
        print(f"freq: {fan_pwm_output.frequency}({FAN_SPEED_PWM_FREQUENCY}), clean_fan_speed: {clean_fan_speed}, CURRENT_NOISE_LEVEL: {CURRENT_NOISE_LEVEL}, CURRENT_AIR_QUALITY_MULITPLIER: {CURRENT_AIR_QUALITY_MULITPLIER}")
        #if clean_fan_speed doesn't match current_noise_level, adjust noise level to match
        if clean_fan_speed != CURRENT_NOISE_LEVEL:
            CURRENT_NOISE_LEVEL = clean_fan_speed
            print(f"Adjusting noise level to match online fan speed: {CURRENT_NOISE_LEVEL}")
        if clean_fan_speed == 0 or CURRENT_NOISE_LEVEL == 0 or CURRENT_AIR_QUALITY_MULITPLIER == 0:
            # Turn off the fan
            FAN_SPEED_PWM_FREQUENCY = 0
            FAN_SPEED_PWM_DUTY_CYCLE = 0
        else:
            # if fan was off, start at 100Hz wait 2 seconds then drop to desired level
            if FAN_SPEED_PWM_FREQUENCY == 0:
                FAN_SPEED_PWM_FREQUENCY = 100
                FAN_SPEED_PWM_DUTY_CYCLE = 32768
                fan_pwm_output.duty_cycle = FAN_SPEED_PWM_DUTY_CYCLE
                fan_pwm_output.frequency = FAN_SPEED_PWM_FREQUENCY
                await asyncio.sleep(2)
            # Set the fan frequency based on the air quality and noise level, lowest 60Hz, highest based on noise level
            if clean_fan_speed == 1:
                range = NOISE_LEVEL_1_MAX_FAN_FREQUENCY - 60
            elif clean_fan_speed == 2:
                range = NOISE_LEVEL_2_MAX_FAN_FREQUENCY - 60
            elif clean_fan_speed == 3:
                range = NOISE_LEVEL_3_MAX_FAN_FREQUENCY - 60
            else:
                range = 0
            air_adjust = (CURRENT_AIR_QUALITY_MULITPLIER / 100) * range
            FAN_SPEED_PWM_FREQUENCY = 60 + air_adjust
        fan_pwm_output.duty_cycle = FAN_SPEED_PWM_DUTY_CYCLE
        fan_pwm_output.frequency = math.floor(FAN_SPEED_PWM_FREQUENCY if FAN_SPEED_PWM_FREQUENCY > 0 else 100)
        await asyncio.sleep(1)


async def rainbow_cycle(wait, pixels):
    while True:
        for color in range(255):
            for pixel in range(len(pixels)):  # pylint: disable=consider-using-enumerate
                pixel_index = (pixel * 256 // len(pixels)) + color * 5
                pixels[pixel] = colorwheel(pixel_index & 255)
            pixels.show()
            await asyncio.sleep(wait)


async def get_io_feed(feed_name, feed_key):
    global ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY, CREATE_FEEDS
    io = IO_HTTP(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY, requests)
    feed = None
    try:
        feed = io.get_feed(feed_key)
    except AdafruitIO_RequestError:
        if CREATE_FEEDS:
            try:
                feed = io.create_and_get_feed(feed_key)
            except AdafruitIO_RequestError as e:
                print(f"Failed to create {feed_name} feed {feed_key}: {e}")
        else:
            print(f"Failed to fetch {feed_name} feed {feed_key}")
    return feed


async def publish_new_fan_speed(fan_speed):
    try:
        io = IO_HTTP(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY, requests)
        fan_speed_feed = await get_io_feed("Fan Speed", FAN_SPEED_FEEDNAME)
        if fan_speed_feed:
            print(f"Publishing new fan speed: {fan_speed}")
            io.send_data(fan_speed_feed["key"], fan_speed)
    except Exception as e:
        print(f"Failed to publish new fan speed")
        print(sys.print_exception(e))


async def monitor_feeds(feed_polling_interval=5):
    global fan_speed, CURRENT_AIR_QUALITY_MULITPLIER, FAN_SPEED_FEEDNAME, AIR_QUALITY_FEEDNAME
    while True:
        if not ADAFRUIT_IO_USERNAME or not ADAFRUIT_IO_KEY or ADAFRUIT_IO_KEY == "YOUR_KEY":
            print("No Adafruit IO username or key found, skipping feed monitoring")
            await asyncio.sleep(feed_polling_interval)
            continue
        try:
            fanspeed_feed = await get_io_feed("Fan Speed", FAN_SPEED_FEEDNAME)
            # Process fan_speed feed
            if fanspeed_feed:
                new_fan_speed = fanspeed_feed["last_value"]
                # Process new_fan_speed
                if isinstance(new_fan_speed, str):
                    if new_fan_speed.lower() == "off":
                        fan_speed = 0
                    else:
                        try:
                            fan_speed = int(new_fan_speed)
                            fan_speed = min(3, max(0, fan_speed))
                            print(f"fan_speed: {fan_speed}")
                        except ValueError:
                            print(f"fan_speed feed ({FAN_SPEED_FEEDNAME}) value is not a number: {new_fan_speed}")
                elif isinstance(new_fan_speed, int) or isinstance(new_fan_speed, float):
                    fan_speed = math.floor(min(3, max(0, new_fan_speed)))
                    print(f"fan_speed: {fan_speed}")
                else:
                    print(f"fan_speed feed ({FAN_SPEED_FEEDNAME}) value is not a number: {new_fan_speed}")
        except Exception as e:
            print(f"Error monitoring fan_speed feed: {e}")
        
        try:
            airquality_feed = await get_io_feed("Air Quality", AIR_QUALITY_FEEDNAME)
            if airquality_feed:
                new_air_quality = airquality_feed["last_value"]
                print(f"air_quality: {new_air_quality}")
                if isinstance(new_air_quality, str):
                    if new_air_quality.lower() == "off":
                        CURRENT_AIR_QUALITY_MULITPLIER = 0
                        print(f"new air_quality: {CURRENT_AIR_QUALITY_MULITPLIER}")
                    else:
                        try:
                            new_air_multiplier = float(new_air_quality)
                            new_air_multiplier = min(100, max(0, new_air_multiplier))
                            CURRENT_AIR_QUALITY_MULITPLIER = new_air_multiplier
                            print(f"new CURRENT_AIR_QUALITY_MULITPLIER: {CURRENT_AIR_QUALITY_MULITPLIER}")
                        except ValueError:
                            print(f"air_quality feed ({AIR_QUALITY_FEEDNAME}) value is not a number: {new_air_quality}")
                elif isinstance(new_air_quality, int) or isinstance(new_air_quality, float):
                    CURRENT_AIR_QUALITY_MULITPLIER = min(100, max(0, new_air_quality))
                    print(f"new CURRENT_AIR_QUALITY_MULITPLIER: {CURRENT_AIR_QUALITY_MULITPLIER}")
                else:
                    print(f"air_quality feed ({AIR_QUALITY_FEEDNAME}) value is not a number: {new_air_quality}")
        except Exception as e:
            print(f"Error monitoring air quality feed: {e}")
        await asyncio.sleep(feed_polling_interval)


async def set_fan_frequency(fan_change_interval=1):
    global fan_pwm_output, FAN_SPEED_PWM_FREQUENCY
    while True:
        print(f"current fan frequency: {FAN_SPEED_PWM_FREQUENCY}")
        new_frequency = 100 if FAN_SPEED_PWM_FREQUENCY == 0 else math.floor(FAN_SPEED_PWM_FREQUENCY)
        fan_pwm_output.frequency = int(new_frequency)
        print(f"new fan frequency: {fan_pwm_output.frequency} (should be {new_frequency})")
        await asyncio.sleep(fan_change_interval)


async def read_tachometer(interval=5):
    global tach_counter
    first_time = True
    while True:
        revolutions = tach_counter.count
        # Reset the counter after reading
        tach_counter.reset()
        if not first_time:
            print("Tachometer count:", revolutions, "RPM:", revolutions * (60 / interval))
        else:
            print("First time reading tachometer, skipping value")
            first_time = False
        # Add appropriate delay based on how often you want to read the tachometer
        await asyncio.sleep(interval)


async def other_tasks(interval=1):
    # Do what you want in this task, print . to show it's still running
    while True:
        print(".", end="") 
        await asyncio.sleep(interval)


async def read_potentiometer(interval=1):
    global potentiometer
    while True:
        print(f" potentiometer.value: {potentiometer.value} ", end="")
        await asyncio.sleep(interval)


async def main_loop():
    global SPEED, rainbow_cycle, other_tasks, neopixels
    while True:
        print("Hello")
        neopixel_task = asyncio.create_task(rainbow_cycle(SPEED, neopixels))
        # dotstar_task = asyncio.create_task(rainbow_cycle(SPEED, dots))
        tachometer_task = asyncio.create_task(read_tachometer())
        rotary_switch_task = asyncio.create_task(read_rotary_switch())
        monitor_feeds_task = asyncio.create_task(monitor_feeds())
        fan_speed_control_task = asyncio.create_task(fan_speed_control())
        fan_freqency_task = asyncio.create_task(set_fan_frequency())
        other_tasks = asyncio.create_task(other_tasks())
        # potentiometer_task = asyncio.create_task(read_potentiometer())
        await asyncio.gather(
            other_tasks,
            tachometer_task,
            # potentiometer_task,
            rotary_switch_task,
            monitor_feeds_task,
            fan_freqency_task,
            fan_speed_control_task,
            neopixel_task
        )#, dotstar_task)
        await asyncio.sleep(1)
        print("Shouldnt get here")

# while True:
#     rainbow_cycle(SPEED)
print("Starting")
asyncio.run(main_loop())
print("Done")
