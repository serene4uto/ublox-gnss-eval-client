import pandas as pd
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Convert GNSS log files to KML format.")
    parser.add_argument('--input', type=str, required=True, help='Path to the input GNSS log file.')
    parser.add_argument('--output', type=str, required=True, help='Path to the output KML file.')
    parser.add_argument('--name', type=str, default='GNSS Log', help='Name for trace in KML file.')
    return parser.parse_args()

def get_color(fix_type):
    color_map = {
        "fixed-rtk": "ff00ff00",  # green
        "extrapolated": "ff0000ff",  # red
    }
    return color_map.get(fix_type.lower(), "ffffffff")  # default: white

def main(args=None):
    args = parse_args() if args is None else args

    # Read the CSV file
    df = pd.read_csv(args.input)

    # KML header
    kml_header = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{args.name}</name>
"""

    # Prepare placemarks (points)
    placemarks = []
    track_coords = []
    for idx, row in df.iterrows():
        lat = row['Latitude']
        lon = row['Longitude']
        fix_type = row['FixType']
        color = get_color(fix_type)
        point_name = f"{args.name} {idx}"

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
        track_coords.append(f"{lon},{lat},0")

    # Group all point placemarks inside a Folder
    points_group = f"""
    <Folder>
      <name>{args.name} Points</name>
      {' '.join(placemarks)}
    </Folder>
"""

    # Add track (LineString)
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
        f.write(points_group)
        f.write(track_kml)
        f.write(kml_footer)

    print(f"KML file generated: {args.output}")

if __name__ == "__main__":
    main()
