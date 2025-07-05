import pandas as pd
import argparse

# Define all possible fix types
ALL_FIX_TYPES = [
    'extrapolated',
    'no-fix',
    'no-rtk',
    'float-rtk',
    'fixed-rtk',
    'dead-reckoning',
    'synced'
]

def parse_args():
    parser = argparse.ArgumentParser(description="Convert GNSS log files to KML format.")
    parser.add_argument('--input', type=str, required=True, help='Path to the input GNSS log file.')
    parser.add_argument('--output', type=str, required=True, help='Path to the output KML file.')
    parser.add_argument('--name', type=str, default='GNSS Log', help='Name for trace in KML file.')
    parser.add_argument('--downsample', type=int, default=1, help='Downsample: include every N-th point. Default: 1 (no downsampling).')
    parser.add_argument('--trace', action='store_true', help='Include a trace (line) connecting all points.')
    parser.add_argument('--placemark', action='store_true', help='Include a group of placemarks (points).')
    parser.add_argument('--fix-types', nargs='*', default=ALL_FIX_TYPES,
                       help=f'Only use points with these fix types. Default: all ({", ".join(ALL_FIX_TYPES)}).')
    return parser.parse_args()

def get_color(fix_type):
    color_map = {
        'extrapolated': 'ff0000ff',     # Red
        'no-fix': 'ff7f7f7f',           # Gray
        'no-rtk': 'ff00ffff',           # Cyan
        'float-rtk': 'ff00ff00',        # Green
        'fixed-rtk': 'ffff0000',        # Blue
        'dead-reckoning': 'ffff00ff'    # Magenta
    }
    return color_map.get(fix_type.lower(), "ffffffff")  # default: white

def main(args=None):
    args = parse_args() if args is None else args

    # Read the CSV file
    df = pd.read_csv(args.input)

    # Filter by fix type (args.fix_types is already a list)
    selected_types = [ft.lower() for ft in args.fix_types]
    df = df[df['FixType'].str.lower().isin(selected_types)]

    # Reset index for clean downsampling (optional, but recommended for clarity)
    df = df.reset_index(drop=True)

    # KML header
    kml_header = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{args.name}</name>
"""

    # Prepare placemarks and track coordinates
    placemarks = []
    track_coords = []
    for idx, row in df.iterrows():
        if idx % args.downsample != 0:
            continue

        lat = row['Latitude']
        lon = row['Longitude']
        fix_type = row['FixType']
        color = get_color(fix_type)
        point_name = f"{args.name} {idx}"

        if args.placemark:
            placemark = f"""
      <Placemark>
        <name>{point_name}</name>
        <description>FixType: {fix_type}</description>
        <Style>
          <IconStyle>
            <color>{color}</color>
            <scale>0.6</scale>
            <Icon>
              <href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href>
            </Icon>
          </IconStyle>
        </Style>
        <Point>
          <coordinates>{lon},{lat},0</coordinates>
        </Point>
      </Placemark>
"""
            placemarks.append(placemark)
        if args.trace:
            track_coords.append(f"{lon},{lat},0")

    # Add placemark group if requested
    points_group = ""
    if args.placemark:
        points_group = f"""
    <Folder>
      <name>{args.name} Points</name>
      {''.join(placemarks)}
    </Folder>
"""

    # Add trace if requested
    track_kml = ""
    if args.trace and track_coords:
        track_kml = f"""
    <Placemark>
      <name>GNSS Track</name>
      <Style>
        <LineStyle>
          <color>ff00ffff</color>
          <width>2</width>
        </LineStyle>
      </Style>
      <LineString>
        <coordinates>
          {' '.join(track_coords)}
        </coordinates>
      </LineString>
    </Placemark>
"""

    # KML footer
    kml_footer = """
  </Document>
</kml>
"""

    # Write to file
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(kml_header)
        if args.placemark:
            f.write(points_group)
        if args.trace:
            f.write(track_kml)
        f.write(kml_footer)

    print(f"KML file generated: {args.output}")

if __name__ == "__main__":
    main()
