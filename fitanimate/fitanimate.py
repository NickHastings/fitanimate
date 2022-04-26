'''Generate animations of data from fit file data
'''
import os
from pathlib import Path
import configargparse

import fitanimate.plot as fap
import fitanimate.animator as ani

def main():
    '''Entry point for fitanimate
    '''
    parser = configargparse.ArgumentParser(
        default_config_files=
        [ os.path.join(str(Path.home()), '.config', 'fitanimate', '*.conf'),
          os.path.join(str(Path.home()), '.fitanimate.conf') ],
        formatter_class=configargparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        'infile', metavar='FITFILE', type=configargparse.FileType(mode='rb'),
        help='Input .FIT file (Use - for stdin).',
    )
    parser.add_argument(
        '--offset', type=float, default=0.0, help='Time offset (hours).'
    )
    parser.add_argument(
        '--show',    '-s', action='store_true', default=False, help='Show the animation on screen.'
    )
    parser.add_argument(
        '--num',    '-n', type=int, default=0, help='Only animate the first NUM frames.'
    )
    parser.add_argument(
        '--fields', type=str, action='append', default=ani.default_fields,
        help='Fit file variables to display as text.', choices=fap.RideText.supported_fields
    )
    parser.add_argument(
        '--plots', type=str, action='append', default=ani.default_plots,
        help='Fit file variables to display as bar plot.', choices=fap.supported_plots
    )
    parser.add_argument(
        '--no-elevation', action='store_true', default=False, help='Disable elevation plot.'
    )
    parser.add_argument(
        '--no-map', action='store_true', default=False, help='Disable map.'
    )
    parser.add_argument(
        '--outfile', '-o', type=str, default=None, help='Output filename.'
    )
    parser.add_argument(
        '--format', '-f', type=str, default='1080p', choices=ani.video_formats.keys(),
        help='Output video file resolution.'
    )
    parser.add_argument(
        '--dpi', '-d', type=int, default=100,
        help='Dots Per Inch. Probably shouldn\'t change.'
    )
    parser.add_argument(
        '--text-color', '-c', type=str, default='black',
        help='Text Color.'
    )
    parser.add_argument(
        '--plot-color', type=str, default='tab:blue',
        help='Plot Color.'
    )
    parser.add_argument(
        '--highlight-color', type=str, default='tab:red',
        help='Plot Highlight Color.'
    )
    parser.add_argument(
        '--alpha', type=float, default=0.3, help='Opacity of plots.'
    )
    parser.add_argument(
        '--vertical', '-v', action='store_true', default=False, help='Plot bars Verticaly.'
    )
    parser.add_argument(
        '--elevation-factor', '-e', type=float, default=5.0,
        help='Scale the elevation by this factor in the plot.'
    )
    parser.add_argument(
        '--test', '-t', action='store_true',
        help='Options for quick tests. Equivalent to "-s -f 360p".'
    )
    args = parser.parse_args()

    animator = ani.Animator(args)
    animator.setup()
    animator.draw()
    animator.animate()

if __name__ == '__main__':
    main()
