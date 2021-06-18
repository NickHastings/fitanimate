# fitanimate
Creates animated graphics from `fit` file data. These graphics can be written to a video file suitable to be used as an overlay of simultaneously recorded video.

## Install

### Development version
Clone the repository:
```
git clone https://github.com/NickHastings/fitanimate.git
```
Install locally with pip
```
python3 -m pip install ./fitanimate
```
### Stable realeases
```
python3 -m pip install fitanimate
```

On Ubuntu or Debian these installations may fail with an error like:
```
Proj4 version 0.0.0 is installed, but cartopy requires at least version 4.9.0.

    ----------------------------------------
    Command "python setup.py egg_info" failed with error code 1 in /tmp/pip-build-l42wavod/cartopy/
```
It seems this can be solved by installing some additonal dependencies (see https://github.com/googlecolab/colabtools/issues/85)
```
sudo apt install libproj-dev proj-data proj-bin libgeos-dev
```
Then finally try again
```
python3 -m pip install fitanimate
```

## Usage

Commandline options and configuration file information:
```
usage: fa [-h] [--offset OFFSET] [--show] [--num NUM]
          [--fields {timestamp,temperature,core_temperature,heart_rate,lap,gears,altitude,grad,distance}]
          [--plots {cadence,speed,power,heart_rate,None}] [--no-elevation]
          [--no-map] [--outfile OUTFILE]
          [--format {240p,360p,480p,720p,1080p,1440p,4k}] [--dpi DPI]
          [--text-color TEXT_COLOR] [--plot-color PLOT_COLOR]
          [--highlight-color HIGHLIGHT_COLOR] [--alpha ALPHA] [--vertical]
          [--elevation-factor ELEVATION_FACTOR] [--test]
          FITFILE

Args that start with '--' (eg. --offset) can also be set in a config file
(/home/hastings/.config/fitanimate/*.conf or /home/hastings/.fitanimate.conf).
Config file syntax allows: key=value, flag=true, stuff=[a,b,c] (for details,
see syntax at https://goo.gl/R74nmi). If an arg is specified in more than one
place, then commandline values override config file values which override
defaults.

positional arguments:
  FITFILE               Input .FIT file (Use - for stdin).

optional arguments:
  -h, --help            show this help message and exit
  --offset OFFSET       Time offset (hours). (default: 0.0)
  --show, -s            Show the animation on screen. (default: False)
  --num NUM, -n NUM     Only animate the first NUM frames. (default: 0)
  --fields {timestamp,temperature,core_temperature,heart_rate,lap,gears,altitude,grad,distance}
                        Fit file variables to display as text. (default:
                        ['timestamp', 'temperature', 'heart_rate', 'lap',
                        'gears', 'altitude', 'grad', 'distance'])
  --plots {cadence,speed,power,heart_rate,None}
                        Fit file variables to display as bar plot. (default:
                        ['cadence', 'speed', 'power'])
  --no-elevation        Disable elevation plot. (default: False)
  --no-map              Disable map. (default: False)
  --outfile OUTFILE, -o OUTFILE
                        Output filename. (default: None)
  --format {240p,360p,480p,720p,1080p,1440p,4k}, -f {240p,360p,480p,720p,1080p,1440p,4k}
                        Output video file resolution. (default: 1080p)
  --dpi DPI, -d DPI     Dots Per Inch. Probably shouldn't change. (default:
                        100)
  --text-color TEXT_COLOR, -c TEXT_COLOR
                        Text Color. (default: black)
  --plot-color PLOT_COLOR
                        Plot Color. (default: tab:blue)
  --highlight-color HIGHLIGHT_COLOR
                        Plot Highlight Color. (default: tab:red)
  --alpha ALPHA         Opacity of plots. (default: 0.3)
  --vertical, -v        Plot bars Verticaly. (default: False)
  --elevation-factor ELEVATION_FACTOR, -e ELEVATION_FACTOR
                        Scale the elevation by this factor in the plot.
                        (default: 5.0)
  --test, -t            Options for quick tests. Equivalent to "-s -f 360p".
                        (default: False)
```

For testing use the -t or --test option. Eg
```
fa --test path/to/afternoon-ride.fit
```
Sample configuration file.
```
cat ~/.fitanimate.conf
format = 4k
offset = 9.0
fields = [timestamp, temperature, heart_rate, altitude, grad, distance]
```
