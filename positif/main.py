import os
import glob
import imageio.v3 as iio
import rawpy
from scipy.interpolate import splev, splrep
import scipy.ndimage
import numpy as np
from positif.parser import parse_arguments
import positif.parameters as params


DATA_TYPES = {8: np.uint8, 16: np.uint16}


def mid_level(im,
              bin_width=params.HISTOGRAM_BIN_WIDTH,
              threshold=params.HISTOGRAM_THRESHOLD,
              border_h=params.HISTOGRAM_BORDER_HEIGHT,
              border_w=params.HISTOGRAM_BORDER_WIDTH):
    height, width, _ = im.shape
    bh = int(border_h * height)
    bw = int(border_w * width)
    bins = np.arange(0, 2 ** params.BPS, bin_width)
    h, b = np.histogram(im[bh:-bh, bw:-bw, :].flatten(), bins=bins)
    th = threshold * np.max(h)
    lower_bound = np.argmax(h[1:] > th) + 1
    upper_bound = len(h) - 1 - np.argmax(h[::-1] > th)
    centre = 0.5 * (lower_bound + upper_bound) * bin_width
    return centre


def create_splines(curves_directory, order=params.ORDER):
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
            bits_per_sample=params.BPS):
    max_level = 2 ** bits_per_sample - 1
    if middle_level is not None:
        c = middle_level * max_level
    else:
        c = mid_level(im)

    rc = c + red_correction * max_level
    gc = c + green_correction * max_level
    bc = c + blue_correction * max_level

    x = np.arange(max_level+1)
    lut_red = splev(x - rc, tck_r, ext=3)
    lut_green = splev(x - gc, tck_g, ext=3)
    lut_blue = splev(x - bc, tck_b, ext=3)

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
        dst = dst/dst_max

    dst_scaled = np.clip(dst * max_level, 0, max_level)
    return dst_scaled.astype(DATA_TYPES[bits_per_sample]), c / max_level


def read_raw(filename, bits_per_sample=params.BPS, flip=True, downsample=1):
    with rawpy.imread(filename) as raw:
        im = raw.postprocess(output_color=rawpy.ColorSpace.raw,
                             output_bps=bits_per_sample,
                             use_camera_wb=True,
                             no_auto_bright=True)
        if flip:
            im = im[:, ::-1, :]
        if downsample > 1:
            factor = 1.0/downsample
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


def main():
    args = parse_arguments()
    tck_red, tck_green, tck_blue = create_splines(args.curves)
    temperature = white_correction(args.temperature)

    if os.path.isfile(args.raw):
        src = read_raw(args.raw, flip=args.flip, downsample=args.downsample)
        positive, mid = convert(src, tck_red, tck_green, tck_blue,
                                middle_level=args.mid_level,
                                red_correction=args.red,
                                green_correction=args.green,
                                blue_correction=args.blue,
                                temperature_correction=temperature)
        print(f'"{args.output}"  {mid:.3f}')
        iio.imwrite(args.output, positive)
    else:
        if not os.path.isdir(args.output):
            os.mkdir(args.output)
        if os.path.isdir(args.raw) and os.path.isdir(args.output):
            raw_files = glob.glob(os.path.join(args.raw, f"*.{args.format}"))
            for fn in raw_files:
                basename = os.path.basename(fn)
                name, _ = os.path.splitext(basename)

                src = read_raw(fn, flip=args.flip, downsample=args.downsample)
                positive, mid = convert(src, tck_red, tck_green, tck_blue,
                                        middle_level=args.mid_level,
                                        red_correction=args.red,
                                        green_correction=args.green,
                                        blue_correction=args.blue,
                                        temperature_correction=temperature)
                output_fn = os.path.join(args.output, f"{name}.tiff")
                iio.imwrite(output_fn, positive)
                print(f'"{name}.tiff"  {mid:.3f}')


if __name__ == "__main__":
    main()
