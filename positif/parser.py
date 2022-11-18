import argparse
import os
from functools import partial
import tomllib
from positif.parameters import FILM_STOCKS, CURVES


CHANNEL_LOWER = -0.5
CHANNEL_UPPER = 0.5
MID_LEVEL_LOWER = 0.1
MID_LEVEL_UPPER = 0.9
TEMPERATURE_LOWER = 1000.0
TEMPERATURE_UPPER = 40000.0


def bound_float_type(arg, lower, upper):
    try:
        f = float(arg)
    except ValueError:
        raise argparse.ArgumentTypeError("Must be a floating point number")

    if lower <= f <= upper:
        return f
    else:
        raise argparse.ArgumentTypeError(f"Argument must be between {lower:.2f} and {upper:.2f} (inclusive)")


def existing_directory_type(arg):
    try:
        d = str(arg)
    except ValueError:
        raise argparse.ArgumentTypeError("Must be a string containing a valid path to a directory")

    if os.path.isdir(d):
        return d
    else:
        raise argparse.ArgumentTypeError("Argument must a valid path to existing directory")


def existing_file_or_directory_type(arg):
    try:
        d = str(arg)
    except ValueError:
        raise argparse.ArgumentTypeError("Must be a string containing a valid path to a file or directory")

    if os.path.isdir(d) or os.path.isdir(os.path.dirname(d)):
        return d
    else:
        raise argparse.ArgumentTypeError("Argument must be a valid path and the parent directory must exist")


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Convert digital camera capture of a film negative to a positive image using film-specific curves")
    parser.add_argument("--raw",
                        type=existing_file_or_directory_type,
                        help="name of DSLR RAW file or directory containing RAW files",
                        required=True)

    parser.add_argument("--film",
                        type=str,
                        choices=FILM_STOCKS,
                        help=f"colour negative film. Supported film stocks are: {FILM_STOCKS}",
                        required=True)

    parser.add_argument("--format",
                        type=str,
                        help="extension of RAW IMAGE files, e.g. ARW, CR2, NEF, etc. "
                             "Must be supplied if --raw is a directory",
                        default="",
                        required=False)

    parser.add_argument("--downsample",
                        type=int,
                        choices=(1, 2, 3, 4, 5, 6, 8, 10, 16),
                        help="(optional) downsample the output image by the specified factor",
                        default=1,
                        required=False)

    bounded_mid_level = partial(bound_float_type, lower=MID_LEVEL_LOWER, upper=MID_LEVEL_UPPER)
    parser.add_argument("--mid-level",
                        type=bounded_mid_level,
                        help=f"(optional) relative middle level, "
                             f"from {MID_LEVEL_LOWER:.2f} to {MID_LEVEL_UPPER}. "
                             "If not defined, it is calculated automatically",
                        default=None,
                        required=False)

    bounded_channel = partial(bound_float_type, lower=CHANNEL_LOWER, upper=CHANNEL_UPPER)
    parser.add_argument("--red",
                        type=bounded_channel,
                        help="(optional) red channel correction, "
                             f"from {CHANNEL_LOWER:.2f} to {CHANNEL_UPPER:.2f}. Default is 0.",
                        default=None,
                        required=False)

    parser.add_argument("--green",
                        type=bounded_channel,
                        help="(optional) green channel correction, "
                             f"from {CHANNEL_LOWER:.2f} to {CHANNEL_UPPER:.2f}. Default is 0.",
                        default=None,
                        required=False)

    parser.add_argument("--blue",
                        type=bounded_channel,
                        help="(optional) green channel correction, "
                             f"from {CHANNEL_LOWER:.2f} to {CHANNEL_UPPER:.2f}. Default is 0.",
                        default=None,
                        required=False)

    bounded_temperature = partial(bound_float_type, lower=TEMPERATURE_LOWER, upper=TEMPERATURE_UPPER)
    parser.add_argument("--temperature",
                        type=bounded_temperature,
                        help="(optional) white balance temperature in Kelvin, "
                             f"from {TEMPERATURE_LOWER:.1f} to {TEMPERATURE_UPPER:.1f}. "
                             "If omitted, the correction is not applied ",
                        default=None,
                        required=False)

    parser.add_argument("--output",
                        type=existing_file_or_directory_type,
                        help="name of the output TIFF file or directory",
                        required=True)

    parser.add_argument('--flip',
                        help="(optional) flip the image horizontally. Disabled by default.",
                        action='store_true')

    a = parser.parse_args()
    if os.path.isdir(a.raw) and a.format == "":
        print(f'Warning: file format must be specified (e.g. "ARW", "CR2", "NEF", etc.)')

    a.curves = CURVES[a.film]    # append `curves` attribute to Arguments Namespace
    config_fn = os.path.join(a.curves, "defaults.toml")
    if os.path.isfile(config_fn):
        with open(config_fn, "rb") as f:
            configuration = tomllib.load(f)

        if a.mid_level is None:
            if "exposure" in configuration and "mid-level" in configuration["exposure"]:
                value = configuration["exposure"]["mid-level"]
                a.mid_level = None if value == "auto" else value
            else:
                a.mid_level = None

        if a.red is None:
            if "channels" in configuration and "red" in configuration["channels"]:
                a.red = configuration["channels"]["red"]
            else:
                a.red = 0.0

        if a.green is None:
            if "channels" in configuration and "green" in configuration["channels"]:
                a.green = configuration["channels"]["green"]
            else:
                a.green = 0.0

        if a.blue is None:
            if "channels" in configuration and "blue" in configuration["channels"]:
                a.blue = configuration["channels"]["blue"]
            else:
                a.blue = 0.0

        if a.temperature is None:
            if "white-balance" in configuration and "temperature" in configuration["white-balance"]:
                value = configuration["white-balance"]["temperature"]
                a.temperature = 0.0 if value == "auto" else value
            else:
                a.temperature = 0.0

        if not a.flip:
            if "orientation" in configuration and "flip" in configuration["orientation"]:
                a.flip = configuration["orientation"]["flip"]
    return a





