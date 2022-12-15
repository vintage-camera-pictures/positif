import os
import glob
import imageio.v3 as iio
from positif.parser import parse_arguments
import positif.parameters as params
import positif.conversion as conv


def main():
    film_stocks, film_curves = conv.read_config(params.CONFIG)
    args = parse_arguments(film_stocks=film_stocks, film_curves=film_curves)
    temperature = conv.white_correction(args.temperature)

    if os.path.isfile(args.raw):
        src = conv.read_raw(args.raw,
                            user_wb=args.user_white_balance,
                            flip=args.flip,
                            region=args.region,
                            downsample=args.downsample)
        positive, neg_range, curve_range = conv.convert(src,
                                                        curve_file=args.curves,
                                                        contrast_correction=args.contrast,
                                                        red_correction=args.red,
                                                        green_correction=args.green,
                                                        blue_correction=args.blue,
                                                        temperature_correction=temperature)

        print(f"negative range: ({neg_range[0]:.2f}, {neg_range[1]:.2f})")
        print(f"film curve range: ({curve_range[0]:.2f}, {curve_range[1]:.2f})")

        try:
            iio.imwrite(args.output, positive)
        except OSError as e:
            print("The following error occurred when saving the output file: \n{str(e)}")
            exit(1)

        print(f'"{args.output}"')
    else:
        if not os.path.isdir(args.output):
            os.mkdir(args.output)
        if os.path.isdir(args.raw) and os.path.isdir(args.output):
            raw_files = glob.glob(os.path.join(args.raw, f"*.{args.format}"))
            for fn in raw_files:
                basename = os.path.basename(fn)
                name, _ = os.path.splitext(basename)

                src = conv.read_raw(fn, flip=args.flip, downsample=args.downsample)
                positive, neg_range, curve_range = conv.convert(src,
                                                                curve_file=args.curves,
                                                                contrast_correction=args.contrast,
                                                                red_correction=args.red,
                                                                green_correction=args.green,
                                                                blue_correction=args.blue,
                                                                temperature_correction=temperature)
                output_fn = os.path.join(args.output, f"{name}.tiff")
                try:
                    iio.imwrite(output_fn, positive)
                except OSError as e:
                    print("The following error occurred when saving the output file: \n{str(e)}")
                    exit(1)

                print(f'"{output_fn}"')


if __name__ == "__main__":
    main()
