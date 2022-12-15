import struct
import rawpy
from scipy.interpolate import splev, splrep
import scipy.ndimage
import numpy as np
import positif.parameters as params
import tomllib


DATA_TYPES = {8: np.uint8, 16: np.uint16}


def negative_range(im,
                   bin_width=params.HISTOGRAM_BIN_WIDTH,
                   threshold=params.HISTOGRAM_THRESHOLD,
                   base_level=np.log10(2 ** params.BPS - 1)):
    height, width, _ = im.shape
    bins = np.arange(0, 2 ** params.BPS, bin_width)
    lower = bins[-1]
    upper = bins[0]
    for channel in range(im.shape[2]):
        h, b = np.histogram(im[:, :, channel].flatten(), bins=bins)
        th = threshold * np.max(h)
        ind0 = np.argmax(h[1:] > th) + 1
        ind1 = len(h) - 1 - np.argmax(h[::-1] > th)
        lower = min(lower, b[ind0])
        upper = max(upper, b[ind1])
    return np.log10(lower) - base_level, np.log10(upper) - base_level


def read_film_curve(filename):
    fmt = "<iiiidd"
    with open(filename, "rb") as fid:
        buffer = fid.read(struct.calcsize(fmt))
        order, n_red, n_green, n_blue, r0, r1 = struct.unpack(fmt, buffer)
        data = fid.read()
        elements = np.frombuffer(data)

    kr0, kr1 = 0, n_red // 2
    kg0, kg1 = n_red, n_red + n_green // 2
    kb0, kb1 = n_red + n_green, n_red + n_green + n_blue // 2
    result = {"lower": r0,
              "upper": r1,
              "red": (elements[kr0:kr1], elements[kr1:kg0], order),
              "green": (elements[kg0:kg1], elements[kg1:kb0], order),
              "blue": (elements[kb0: kb1], elements[kb1:], order)
              }
    return result


def convert(im, curve_file,
            contrast_correction=0.0,
            red_correction=0.0,
            green_correction=0.0,
            blue_correction=0.0,
            temperature_correction=None,
            bits_per_sample=params.BPS):

    film_data = read_film_curve(curve_file)
    cc = contrast_correction * np.log10(2)
    film_data["lower"] -= cc / 2
    film_data["upper"] += cc / 2
    df = film_data["upper"] - film_data["lower"]

    negative_lower, negative_upper = negative_range(im)
    dn = negative_upper - negative_lower

    max_level = 2 ** bits_per_sample - 1
    x = np.arange(1, max_level + 1)
    y = np.log10(x) - np.log10(max_level)
    zr = film_data["lower"] + df/dn * (y - red_correction - negative_lower)
    zg = film_data["lower"] + df/dn * (y - green_correction - negative_lower)
    zb = film_data["lower"] + df/dn * (y - blue_correction - negative_lower)

    nn = len(x) + 1
    lut_red = np.ones(nn)
    lut_green = np.ones(nn)
    lut_blue = np.ones(nn)

    lut_red[1:] = splev(zr, film_data["red"], ext=3)
    lut_green[1:] = splev(zg, film_data["green"], ext=3)
    lut_blue[1:] = splev(zb, film_data["blue"], ext=3)

    if temperature_correction is not None:
        lut_red *= temperature_correction[0]
        lut_green *= temperature_correction[1]
        lut_blue *= temperature_correction[2]

    dst = np.empty_like(im, dtype=float)
    dst[:, :, 0] = lut_red[im[:, :, 0]]
    dst[:, :, 1] = lut_green[im[:, :, 1]]
    dst[:, :, 2] = lut_blue[im[:, :, 2]]

    dst_max = np.max(dst)
    if dst_max > 1.0:
        dst = dst / dst_max

    dst_scaled = np.clip(dst * max_level, 0, max_level)
    neg = (negative_lower, negative_upper)
    film = (film_data["lower"], film_data["upper"])
    return dst_scaled.astype(DATA_TYPES[bits_per_sample]), neg, film


def read_raw(filename, bits_per_sample=params.BPS, user_wb=None, region=None, flip=True, downsample=1):
    with rawpy.imread(filename) as raw:
        kwargs = dict()
        if user_wb is not None:
            kwargs["user_wb"] = user_wb
        else:
            kwargs["use_camera_wb"] = True
        im = raw.postprocess(output_color=rawpy.ColorSpace.raw,
                             gamma=(1.0, 1.0),
                             output_bps=bits_per_sample,
                             no_auto_bright=True,
                             **kwargs)
        if region is not None:
            y0, x0, y1, x1 = region
            im = im[y0:y1, x0:x1, :]
        if flip:
            im = im[:, ::-1, :]
        if downsample > 1:
            factor = 1.0 / downsample
            im = scipy.ndimage.zoom(im, (factor, factor, 1))
        return im


def white_correction(temp, datafile=params.TEMPERATURE_CORRECTIONS):
    if temp > 0.0:
        data = np.fromfile(datafile)
        n = len(data) // 4
        corrections = data.reshape((n, 4))
        rc_tck = splrep(corrections[:, 0], corrections[:, 1], k=1, s=0)
        gc_tck = splrep(corrections[:, 0], corrections[:, 2], k=1, s=0)
        bc_tck = splrep(corrections[:, 0], corrections[:, 3], k=1, s=0)
        rc = splev(temp, rc_tck, ext=3)
        gc = splev(temp, gc_tck, ext=3)
        bc = splev(temp, bc_tck, ext=3)
        return np.hstack((rc, gc, bc))
    return None


def apply_gamma(x):
    info = np.iinfo(x.dtype)
    y = x.flatten() / info.max
    threshold = 0.018
    y[y < threshold] = 4.5 * y[y < threshold]
    y[y >= threshold] = 1.099 * y[y >= threshold] ** 0.45 - 0.099
    z = info.max * np.reshape(y, x.shape)
    return z.astype(dtype=x.dtype)


def read_config(config_fn):
    with open(config_fn, "rb") as f:
        configuration = tomllib.load(f)
        film_curves = configuration["film-curves"]
    return tuple(film_curves.keys()), film_curves
