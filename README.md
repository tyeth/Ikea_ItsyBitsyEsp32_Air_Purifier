# ItsyBitsy ESP32 IKEA Fornuftig Air Cleaner v2 Noise Adjustable

This project integrates air quality data from Adafruit IO (using the Good-enough Air Quality project) with a custom air quality monitoring and adjustment system developed using CircuitPython on a microcontroller platform. It aims to provide a real-time air quality monitoring and adjustment solution, enhancing environmental conditions based on air quality data, while respecting desired noise levels.


See matching write-up / photos / note on Adafruit-Playground:

[https://adafruit-playground.com/u/tyeth/pages/ikea-fornufig-air-purifier-v2-custom-fan-speed-controller-blinkenlights](https://adafruit-playground.com/u/tyeth/pages/ikea-fornufig-air-purifier-v2-custom-fan-speed-controller-blinkenlights)

## Installation

### Prerequisites

- CircuitPython compatible microcontroller (e.g., Adafruit ItsyBitsy ESP32)
- Required libraries from the [CircuitPython Library Bundle](https://circuitpython.org/libraries):
  - 'adafruit_connection_manager'
  - 'adafruit_io'
  - 'adafruit_minimqtt'
  - 'adafruit_pixelbuf'
  - 'adafruit_requests'
  - 'adafruit_ticks'
  - 'asyncio'
  - 'neopixel'

Example dependency install with circup using web workflow:
```shell
C:\Users\tyeth>circup --host 192.168.0.232 --password password install --auto
Found device at http://:password@192.168.0.232, running CircuitPython 9.0.2.
Downloading latest bundles for adafruit/Adafruit_CircuitPython_Bundle (20240402).
py:
Extracting:  [####################################]  100%
8.x-mpy:
Extracting:  [####################################]  100%
9.x-mpy:
Extracting:  [####################################]  100%

OK

Auto file: code.py
Auto file path: C:\Users\tyeth\AppData\Local\adafruit\circup\code.tmp.py
Searching for dependencies for: ['adafruit_io', 'adafruit_requests', 'asyncio', 'neopixel']
Ready to install: ['adafruit_connection_manager', 'adafruit_io', 'adafruit_minimqtt', 'adafruit_pixelbuf', 'adafruit_requests', 'adafruit_ticks', 'asyncio', 'neopixel']

Installed 'adafruit_connection_manager'.
Installed 'adafruit_io'.
Installed 'adafruit_minimqtt'.
Installed 'adafruit_pixelbuf'.
Installed 'adafruit_requests'.
Installed 'adafruit_ticks'.
Installed 'asyncio'.
Installed 'neopixel'.
```

### Setup

1. Ensure your microcontroller is running the latest version of CircuitPython.
2. Clone this repository to your local machine.
3. Copy `code.py` and `settings.toml` to the root of your microcontroller's filesystem.
4. Install the necessary CircuitPython libraries by copying them from the Library Bundle to the `lib` folder on your microcontroller,
or using `circup` the circuitpython package manager

## Usage

After installing the project files and necessary libraries on your microcontroller, reset the device to start the program. The device will:

- Connect to WiFi using credentials specified in `settings.toml` (ensure this file is updated with your network information).
- Fetch air quality data from the Good-enough Air Quality project or another specified source and scale fan speed accordingly.
- Use onboard sensors and outputs (LEDs etc.) to indicate air quality status and adjustments being made.
- Listen to Control Dial for requested Maximum Noise Level, and scale fan speed accordingly.

Monitor serial output for logs and diagnostics.

### Configuration

Edit `settings.toml` to include your settings (like wifi details). Below is a list of variables you need to set:

- `ADAFRUIT_IO_USERNAME` - Your Adafruit IO username.
- `ADAFRUIT_IO_KEY` - Your Adafruit IO key.
- `STATUS_NEOPIXEL_BRIGHTNESS` - Brightness of the status NeoPixel (range 0.0 to 1.0).
- `FAN_SPEED_FEEDNAME` - Feed name for fan speed in Adafruit IO.
- `AIR_QUALITY_FEEDNAME` - Feed name for air quality in Adafruit IO.
- `NOISE_LEVEL_1_MAX_FAN_FREQUENCY`, `NOISE_LEVEL_2_MAX_FAN_FREQUENCY`, `NOISE_LEVEL_3_MAX_FAN_FREQUENCY` - Maximum fan frequencies for noise levels 1, 2, and 3.

Ensure you replace placeholders (e.g., `YOUR_USERNAME_HERE`) with actual values.

## Dependencies

This project depends on several external libraries and services:

- [CircuitPython](https://circuitpython.org/) for programming the microcontroller.
- [Adafruit IO](https://io.adafruit.com/) for online data logging and retrieval.
- [Good-enough Air Quality project](https://github.com/good-enough-technology/Good-Enough_Air-Quality-Device_CO2-SCD4x_PM-SEN5x_CircuitPython) or another air quality data source.
- Various CircuitPython libraries as mentioned in the prerequisites.

## Contributing

We welcome contributions to this project. Please follow these steps to contribute:

1. Fork the project repository.
2. Create a new branch for your feature or bug fix.
3. Commit your changes with clear, descriptive commit messages.
4. Push your branch and submit a pull request against the main project.
5. Ensure your code adheres to the project's coding standards and properly documents any new functionality.

For major changes, please open an issue first to discuss what you would like to change. Please make sure to update tests as appropriate.

## License

This project is currently unlicensed
