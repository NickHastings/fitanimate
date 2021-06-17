# fitanimate
Creates animated graphics from `fit` file data. These graphics can be written to a video file suitable to be used as an overlay of simultaneously recorded video.

## Install
Clone the repository:
```
git clone https://github.com/NickHastings/fitanimate.git
```
Install locally with pip
```
cd fitanimate
python3 -m pip install ./fitanimate
```

## Usage

Commandline options and configuration file information:
```
fa --help
usage: fa [-h] [--offset OFFSET] [--show] [--num NUM]
          [--fields {timestamp,temperature,core_temperature,heart_rate,lap,gears,altitude,grad,distance}]
          [--outfile OUTFILE] [--format {240p,360p,480p,720p,1080p,1440p,4k}]
          [--dpi DPI] [--text-color TEXT_COLOR] [--vertical]
          [--elevation-factor ELEVATION_FACTOR] [--test]
          FITFILE

Args that start with '--' (eg. --offset) can also be set in a config file
(/home/hastings/.config/fitanimate/*.conf or /home/hastings/.fitanimate.conf).
Config file syntax allows: key=value, flag=true, stuff=[a,b,c] (for details,
see syntax at https://goo.gl/R74nmi). If an arg is specified in more than one
place, then commandline values override config file values which override
defaults.

positional arguments:
  FITFILE               Input .FIT file (Use - for stdin)

optional arguments:
  -h, --help            show this help message and exit
  --offset OFFSET       Time offset (hours)
  --show, -s            Show the animation on screen
  --num NUM, -n NUM     Only animate the first NUM frames
  --fields {timestamp,temperature,core_temperature,heart_rate,lap,gears,altitude,grad,distance}
                        Fit file variables to display.
  --outfile OUTFILE, -o OUTFILE
                        Output filename
  --format {240p,360p,480p,720p,1080p,1440p,4k}, -f {240p,360p,480p,720p,1080p,1440p,4k}
                        Output video file resolution.
  --dpi DPI, -d DPI     Dots Per Inch. Probably shouldn't change
  --text-color TEXT_COLOR, -c TEXT_COLOR
                        Text Color
  --vertical, -v        Plot bars Verticaly
  --elevation-factor ELEVATION_FACTOR, -e ELEVATION_FACTOR
                        Scale the elevation by this factor in the plot.
                        --test, -t            Options for quick tests. Equivalent to "-s -f 360p".
```

For testing use the -t or --test option. Eg
```
fa --test path/to/file.fitanimate
```
Sample configuration file.
```
cat ~/.fitanimate.conf
format = 4k
offset = 9.0
fields = [timestamp, temperature, heart_rate, altitude, grad, distance]
```
