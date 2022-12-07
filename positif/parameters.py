HISTOGRAM_BIN_WIDTH = 16
HISTOGRAM_THRESHOLD = 0.01
HISTOGRAM_BORDER_HEIGHT = 0.15
HISTOGRAM_BORDER_WIDTH = 0.20
ORDER = 3
BPS = 16

TEMPERATURE_CORRECTIONS = "curves/temperature.bin"

CURVES = {"Ektar": "./curves/ektar",
          "Portra160": "./curves/portra160"}

FILM_STOCKS = tuple(CURVES.keys())
