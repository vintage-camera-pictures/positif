import os
import glob
import imageio.v3 as iio
import rawpy
from scipy.interpolate import splev, splrep
import numpy as np
from positif.parser import parse_arguments
from positif.parameters import ORDER, BPS, HISTOGRAM_THRESHOLD, HISTOGRAM_BORDER_HEIGHT, HISTOGRAM_BORDER_WIDTH
from positif.parameters import TEMPERATURE_CORRECTIONS

DATA_TYPES = {8: np.uint8, 16: np.uint16}


def mid_level(im,
              threshold=HISTOGRAM_THRESHOLD,
              border_h=HISTOGRAM_BORDER_HEIGHT,
              border_w=HISTOGRAM_BORDER_WIDTH):
    height, width, _ = im.shape
    bh = int(border_h * height)
    bw = int(border_w * width)
    h, b = np.histogram(im[bh:-bh, bw:-bw, :].flatten(), bins=np.arange(2 ** BPS))
    th = threshold * np.max(h)
    lower_bound = np.argmax(h[1:] > th) + 1
    upper_bound = len(h) - 1 - np.argmax(h[::-1] > th)
    centre = 0.5 * (lower_bound + upper_bound)
    return centre


def create_splines(curves_directory, order=ORDER):
    red = np.fromfile(os.path.join(curves_directory, "red.bin"))
    green = np.fromfile(os.path.join(curves_directory, "green.bin"))
    blue = np.fromfile(os.path.join(curves_directory, "blue.bin"))

    n = len(red) // 2
    tck_r = (red[:n], red[n:], order)

    n = len(green) // 2
    tck_g = (green[:n], green[n:], order)

    n = len(blue) // 2
    tck_b = (blue[:n], blue[n:], order)

    return tck_r, tck_g, tck_b


def convert(im, tck_r, tck_g, tck_b, middle_level,
            red_correction=0,
            green_correction=0,
            blue_correction=0,
            temperature_correction=None,
            bits_per_sample=BPS):
    max_level = 2 ** bits_per_sample - 1
    if middle_level is not None:
        c = middle_level * max_level
    else:
        c = mid_level(im)

    rc = c + red_correction * max_level
    gc = c + green_correction * max_level
    bc = c + blue_correction * max_level

    dst = np.empty_like(im, dtype=float)
    dst[:, :, 0] = splev(im[:, :, 0].flatten() - rc, tck_r).reshape(im.shape[:2])
    dst[:, :, 1] = splev(im[:, :, 1].flatten() - gc, tck_g).reshape(im.shape[:2])
    dst[:, :, 2] = splev(im[:, :, 2].flatten() - bc, tck_b).reshape(im.shape[:2])

    if temperature_correction is not None:
        dst[:, :, 0] *= temperature_correction[0]
        dst[:, :, 1] *= temperature_correction[1]
        dst[:, :, 2] *= temperature_correction[2]

    dst_scaled = np.clip(dst * max_level, 0, max_level)
    return dst_scaled.astype(DATA_TYPES[bits_per_sample]), c / max_level


def read_raw(filename, bits_per_sample=BPS, flip=True):
    with rawpy.imread(filename) as raw:
        im = raw.postprocess(output_color=rawpy.ColorSpace.raw,
                             output_bps=bits_per_sample,
                             use_camera_wb=True,
                             no_auto_bright=True)
        if flip:
            im = im[:, ::-1, :]
        return im


def white_correction(temp, datafile=TEMPERATURE_CORRECTIONS):
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


def main():
    args = parse_arguments()

    tck_red, tck_green, tck_blue = create_splines(args.curves)
    temperature = white_correction(args.temperature)

    if os.path.isfile(args.raw):
        src = read_raw(args.raw, flip=args.flip)
        positive, mid = convert(src, tck_red, tck_green, tck_blue,
                                middle_level=args.mid_level,
                                red_correction=args.red,
                                green_correction=args.green,
                                blue_correction=args.blue,
                                temperature_correction=temperature)
        print(f"mid level: {mid:.2f}")
        iio.imwrite(args.output, positive)
    else:
        if os.path.isdir(args.raw) and os.path.isdir(args.output):
            raw_files = glob.glob(os.path.join(args.raw, f"*.{args.format}"))
            for fn in raw_files:
                basename = os.path.basename(fn)
                name, _ = os.path.splitext(basename)

                src = read_raw(fn, flip=args.flip)
                positive, mid = convert(src, tck_red, tck_green, tck_blue,
                                        middle_level=args.mid_level,
                                        red_correction=args.red,
                                        green_correction=args.green,
                                        blue_correction=args.blue,
                                        temperature_correction=temperature)
                output_fn = os.path.join(args.output, f"{name}.tiff")
                iio.imwrite(output_fn, positive)

                print(f"{name}.tiff \tmid level: {mid:.2f}")


if __name__ == "__main__":
    main()
