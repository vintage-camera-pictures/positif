import os
import glob
import imageio.v3 as iio
from positif.parser import parse_arguments
import positif.parameters as params
import positif.conversion as conv


def main():
    film_stocks, film_curves = conv.read_config(params.CONFIG)
    args = parse_arguments(film_stocks=film_stocks, film_curves=film_curves)
    tck_red, tck_green, tck_blue = conv.create_splines(args.curves)
    temperature = conv.white_correction(args.temperature)

    if os.path.isfile(args.raw):
        src = conv.read_raw(args.raw, flip=args.flip, linear=args.linear, downsample=args.downsample)
        positive, mid = conv.convert(src, tck_red, tck_green, tck_blue,
                                     middle_level=args.mid_level,
                                     red_correction=args.red,
                                     green_correction=args.green,
                                     blue_correction=args.blue,
                                     temperature_correction=temperature)
        if args.linear:
            positive = conv.apply_gamma(positive)

        try:
            iio.imwrite(args.output, positive)
        except OSError as e:
            print("The following error occurred when saving the output file: \n{str(e)}")
            exit(1)

        print(f'"{args.output}"  {mid:.3f}')
    else:
        if not os.path.isdir(args.output):
            os.mkdir(args.output)
        if os.path.isdir(args.raw) and os.path.isdir(args.output):
            raw_files = glob.glob(os.path.join(args.raw, f"*.{args.format}"))
            for fn in raw_files:
                basename = os.path.basename(fn)
                name, _ = os.path.splitext(basename)

                src = conv.read_raw(fn, flip=args.flip, linear=args.linear, downsample=args.downsample)
                positive, mid = conv.convert(src, tck_red, tck_green, tck_blue,
                                             middle_level=args.mid_level,
                                             red_correction=args.red,
                                             green_correction=args.green,
                                             blue_correction=args.blue,
                                             temperature_correction=temperature)
                output_fn = os.path.join(args.output, f"{name}.tiff")
                if args.linear:
                    positive = conv.apply_gamma(positive)
                try:
                    iio.imwrite(output_fn, positive)
                except OSError as e:
                    print("The following error occurred when saving the output file: \n{str(e)}")
                    exit(1)

                print(f'"{name}.tiff"  {mid:.3f}')


if __name__ == "__main__":
    main()
