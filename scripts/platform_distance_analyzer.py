# Platform Distance Analyzer for Germany425_2025 AFSIM Scenario
# Analyzes platform positions and calculates distances from AFSIM observer CSV output
#
# Usage:
#     python scripts/platform_distance_analyzer.py <csv_file> 
#     ex: python scripts/platform_distance_analyzer.py output/platform_positions_run_1.csv
# 
#      
# Output files generated:
#     - platform_distance_analysis.csv (comprehensive analysis)
#     - platform_distance_matrix.csv (all pairwise distances)

import csv
import math
import sys
from collections import defaultdict
from pathlib import Path


class PlatformDistanceAnalyzer:
    
    def __init__(self, csv_file):
        
        self.csv_file = csv_file
        self.platforms = {}  # {name: {lat, lon, alt_ft, sensor_range, type, side}}
        self.distances = {}  # {(plat1, plat2): distance_nm}
        
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        # Calculate distance between two points
        # 
        # Args:
        #     lat1, lon1: First point (decimal degrees)
        #     lat2, lon2: Second point (decimal degrees)
        #     
        # Returns:
        #     Distance in nautical miles
        # Latitude: 1 degree = 60 nautical miles
        lat_diff_nm = (lat2 - lat1) * 60.0
        
        # Longitude: 1 degree varies with latitude
        # At mean latitude, use Distance = 60 x cos(Latitude)
        mean_lat = (lat1 + lat2) / 2.0
        cos_lat = math.cos(math.radians(mean_lat))
        lon_diff_nm = (lon2 - lon1) * 60.0 * cos_lat
        
        #  distance formaula
        distance_nm = math.sqrt(lat_diff_nm**2 + lon_diff_nm**2)
        return distance_nm
    
    def load_csv(self):
        # Load platform data from AFSIM observer CSV file
        try:
            with open(self.csv_file, 'r') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    plat_name = row['Platform_Name'].strip()
                    
                    self.platforms[plat_name] = {
                        'type': row['Platform_Type'].strip(),
                        'side': row['Side'].strip(),
                        'lat': float(row['Latitude']),
                        'lon': float(row['Longitude']),
                        'alt_ft': float(row['Altitude_ft']),
                        'sensor_range_nm': float(row['Sensor_Range_NM'])
                    }
            
            print(f"Loaded {len(self.platforms)} platforms from {self.csv_file}")
            return True
            
        except FileNotFoundError:
            print(f"Error: File not found - {self.csv_file}")
            return False
        except (KeyError, ValueError) as e:
            print(f"Error parsing CSV: {e}")
            return False
    
    def calculate_distances(self):
        # calculate distances between all platform pairs
        platform_list = list(self.platforms.keys())
        
        for i, plat1 in enumerate(platform_list):
            for plat2 in platform_list[i+1:]:
                lat1 = self.platforms[plat1]['lat']
                lon1 = self.platforms[plat1]['lon']
                lat2 = self.platforms[plat2]['lat']
                lon2 = self.platforms[plat2]['lon']
                
                distance = self.calculate_distance(lat1, lon1, lat2, lon2)
                
                # store both directions for reporting
                self.distances[(plat1, plat2)] = distance
                self.distances[(plat2, plat1)] = distance
        
        print(f"Calculated distances for {len(self.distances)//2} platform pairs")
    
    def generate_text_report(self):
        #generate report of platform distances
        csv_lines = []
        
        csv_lines.append("PLATFORM SUMMARY")
        csv_lines.append("Platform_Name,Type,Side,Latitude,Longitude,Altitude_ft,Sensor_Range_nm")
        
        for plat_name in sorted(self.platforms.keys()):
            p = self.platforms[plat_name]
            csv_lines.append(f"{plat_name},{p['type']},{p['side']},{p['lat']:.6f},{p['lon']:.6f},{p['alt_ft']:.1f},{p['sensor_range_nm']:.1f}")
        
        # distance analysis section
        csv_lines.append("")
        csv_lines.append("DISTANCE ANALYSIS BY PLATFORM")
        csv_lines.append("Platform_1,Platform_2,Distance_nm,Platform_2_Type,Platform_2_Side,In_Range")
        
        # sort platforms by side and type
        all_platforms = sorted(self.platforms.keys())

        
        for plat1 in all_platforms:
            # find distances to all other platforms
            platform_distances = []
            for plat2 in self.platforms.keys():
                if plat2 != plat1:
                    distance = self.distances.get((plat1, plat2), None)
                    if distance is not None:
                        sensor_range = self.platforms[plat1]['sensor_range_nm']
                        within_range = "YES" if (sensor_range > 0 and distance <= sensor_range) else "NO"
                    platform_distances.append((distance, plat2, within_range))
            
            # sort by distance
            for distance, plat2, within_range in sorted(platform_distances):
                csv_lines.append(f"{plat1},{plat2},{distance:.2f},{self.platforms[plat2]['type']},{self.platforms[plat2]['side']},{within_range}")
        
        # threat analysis section
        csv_lines.append("")
        csv_lines.append("THREAT ANALYSIS (RED can detect BLUE)")
        csv_lines.append("RED_Platform,RED_Sensor_Range_nm,BLUE_Platform,Distance_nm,Detection_Margin_nm")
        
        # get red and blue platforms
        red_platforms = sorted([p for p in self.platforms.keys() if self.platforms[p]['side'].lower() == 'red'])
        blue_platforms = sorted([p for p in self.platforms.keys() if self.platforms[p]['side'].lower() == 'blue'])
        # analyze red-blue distances
        for red_plat in red_platforms:
            red_range = self.platforms[red_plat]['sensor_range_nm']
            threats = []
            
            for blue_plat in blue_platforms:
                distance = self.distances.get((red_plat, blue_plat), None)
                if distance is not None and distance <= red_range:
                    threats.append((distance, blue_plat, red_range - distance))
            
            for distance, blue_plat, margin in sorted(threats):
                csv_lines.append(f"{red_plat},{red_range:.1f},{blue_plat},{distance:.2f},{margin:.2f}")
        
        return "\n".join(csv_lines)
    
    def generate_distance_matrix_csv(self):
        platform_list = sorted(self.platforms.keys())
        
        csv_lines = []
        
        # header row 
        csv_lines.append(",".join(["Platform"] + platform_list))
        
        # distance rows
        for plat1 in platform_list:
            row = [plat1]
            for plat2 in platform_list:
                if plat1 == plat2:
                    row.append("0.00")
                else:
                    distance = self.distances.get((plat1, plat2), 0)
                    row.append(f"{distance:.2f}")
            csv_lines.append(",".join(row))
        
        return "\n".join(csv_lines)

    
    def run(self):
        print("\n" + "=" * 80)
        print("PLATFORM DISTANCE ANALYZER")
        print("=" * 80 + "\n")
        
        if not self.load_csv():
            return False
        
        self.calculate_distances()
        
        print("Generating text report...")
        text_report = self.generate_text_report()
        report_file = Path(self.csv_file).parent / "platform_distance_analysis.csv"
        with open(report_file, 'w') as f:
            f.write(text_report)
        print(f"Saved: {report_file}")
        
        print("Generating distance matrix CSV...")
        distance_csv = self.generate_distance_matrix_csv()
        matrix_file = Path(self.csv_file).parent / "platform_distance_matrix.csv"
        with open(matrix_file, 'w') as f:
            f.write(distance_csv)
        print(f"Saved: {matrix_file}")
        
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"\nOutput files generated:")
        print(f"  1. {report_file}")
        print(f"  2. {matrix_file}")
        
        return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python platform_distance_analyzer.py <csv_file>")
        print("\nExample:")
        print("  python platform_distance_analyzer.py output/run_001/platform_positions.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    analyzer = PlatformDistanceAnalyzer(csv_file)
    success = analyzer.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()