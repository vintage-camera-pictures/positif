# Positif

Convert colour film negative digitised with DSLR to a positive image.

## Motivation

Colour film negatives can be digitised by taking an image of the negative placed on a light box with a digital camera.
Provided you have a camera with a proper lens, this technique is very inexpensive and fast compared to
scanning the negatives by a dedicated film scanner or having them digitised by a photographic lab.
The quality of the resulting digital capture is only limited by the specifications of your camera and lens.
Usually, they are on par or exceed those of the film scanners, including the professional machines used by the labs.

The main problem of the method is in converting the negative images to positives.
[Negative Lab Pro](https://www.negativelabpro.com/) is probably the best tool for the job. It is reasonably priced and
delivers excellent results. Unfortunately, Negative Lab Pro is a Lightroom plugin and requires a subscription to this product.
Not all film photographers use Lightroom. Some prefer [Darktable](https://www.darktable.org/),
[RawTherapee](https://www.rawtherapee.com/) and other free and open-source software. Both
Darktable and RawTherapee are capable of excellent results if you know how to use these tools.
The hardest part is achieving consistency between the frames shot on the same roll of film, different rolls shot on the same
film stock and between different films. At the end of the day, we are shooting film to get that special look that is almost
impossible to replicate digitally.

`Positif` is an experimental tool for converting RAW images of the film negatives taken by a digital camera to positive images.
The idea is to use transformation curves specific to the film, development process, the digital camera and the light source you use.

## Installation

`Positif` is a command-line tool that requires Python version 3.11 or above. It is installed from `PyPI` using `pip`:

```bash
pip install positif
```

## Usage

Run `positif -h` to get a full list of command line arguments. There are two major use scenarios. You can convert an
individual file, for example:

```bash
positif --raw="frame00000.ARW" --film=Ektar --output=frame00.tiff
```

Alternatively, you can process all RAW files in a directory and save the results in the destination directory, like that:

```bash
positif --raw="./capture" --format=ARW --film=Ektar --output="./results"
```

The `--format` parameter is required when converting all RAW files in a directory.

## Conversion Parameters

`positif` would normally create an output image which is a good starting point for further post-processing in your
favourite photo editing software. If you notice a consistent exposure offset, temperature bias or colour shift you can
use the conversion parameters described below to improve the resulting image.

| Parameter     | Description                                                                                                                                                                                                                                               |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| --mid-level   | Middle grey level relative to full scale. If this parameter is not specified it is determined automatically based on the histogram of the image.<br> Values below 0.5 result in darker output image and vice versa. The allowed range is from 0.1 to 0.9. |
| --red         | Red channel adjustment. Positive corrections add red. Valid range is from -0.5 to 0.5. <br>Typical values are within &plusmn;0.1.                                                                                                                         |
| --green       | Green channel adjustment.                                                                                                                                                                                                                                 |
| --blue        | Blue channel adjustment.                                                                                                                                                                                                                                  |
| --temperature | Colour temperature of the output image in Kelvin. Valid range is from 1000K (very red) to 40000K (very blue).<br> When not specified the correction is not applied.                                                                                       |
| --flip        | Use this flag to flip the image horizontally. This is useful if you photograph the negative with the emulsion side to the camera                                                                                                                          |

## Examples

Here are a few examples of using `positif`. The scene was shot on Kodak Ektar 100 developed at home using Tetenal Colortec C-41 kit. The first image is the negative, the second is the output of the script called with the default parameters.

![Negative](https://github.com/vintage-camera-pictures/positif/blob/main/examples/frame04-negative.jpg?raw=true "Negative")

![Default settings](https://github.com/vintage-camera-pictures/positif/blob/main/examples/frame04-default.jpg?raw=true "Default parameters")

There is a strong green cast and the reds are somewhat missing. Calling `positif` with the `--red=0.01 --green=-0.04` parameters results in the image below.

![Corrected](https://github.com/vintage-camera-pictures/positif/blob/main/examples/frame04-corrected.jpg?raw=true "corrected") 

For comparison, here is the same scene captured with a digital camera. No adjustments were made to the digital RAW image except applying the camera white balance.

![Digital capture](https://github.com/vintage-camera-pictures/positif/blob/main/examples/digital.jpg?raw=true "digital capture")

There is an obvious difference in the exposure between the image from the colour negative film and the direct digital capture. Apart from this, the corrected image is very close to the digital. More importantly, batch processing of the whole roll produces consistent output.

## How it works

Red, Green and Blue transform curves are applied to the corresponding channels of the RAW image of the film negative captured by a digital camera. The curves look like shown in the plot below.

![Curves](https://github.com/vintage-camera-pictures/positif/blob/main/examples/ektar.jpg?raw=true "film curves")

The input and output levels are normalised pixel values, 1.0 corresponds to the maximum channel level, 255 (8 bit) or 65535 (16 bit).

The transform curve can be determined by several methods. The most straightforward approach is to expose a roll of your favourite colour negative film and include several scenes with a wide dynamic range, like the one in the example. Have your film developed and scanned by a good professional lab. This is your reference. Digitise one or more frames from this roll using your digital camera and light source. You must use RAW image format. The transform curves for each channel can then be derived by comparing the lab scan (your reference) with the RAW image from your camera, pixel-by-pixel.

In the example above, the calibration curves were determined using a different roll of Kodak Ektar 100 shot with a different film camera on a different day in a different location. The reference film was developed by a professional lab using Fuji chemistry and scanned on a Noritsu scanner. The green colour cast in the first converted image could be caused by the camera lens, processing chemistry and development, or the digitising setup.

## Tips for Digitising Negatives

There are several simple rules that you need to follow when digitising your film negatives:

- **Reduce Flare.** Work in subdued light, use a lens hood and mask unused areas of your light source.
- **Calibrate White Balance.** Set custom white balance on your camera to the colour of your film base. Ideally, your want to do it for each roll of film. As a minimum, set custom white balance for each film stock you shoot. The gaps between the frames should be neutral grey as in the example below:

  ![Negative](https://github.com/vintage-camera-pictures/positif/blob/main/examples/negative.jpg?raw=true "white-balanced negative")

  There is no need to include the film borders and the gaps in the shot.
- **Use Manual Exposure.** Not strictly necessary, but more consistent results would be achieved if you use the same exposure settings for the whole roll. Use the aperture of around f11 and adjust the shutter speed such that the film base is around 1/3 of a stop below clipping (after the white balance has been applied). Check all three channels. Obviously, the film base is the brightest white in your negatives unless you choose to include perforations in your scans. If this is the case, you might want to decrease the shutter time accordingly to avoid clipping. Flare might be a problem especially with high-key images (dense negatives). Once you are happy with your exposure settings, fix them by switching to a manual exposure mode.
- **Scan Film Emulsion Side to the Lens**. It might not affect the final result, but simplifies your workflow.
