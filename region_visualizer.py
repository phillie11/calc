# region_visualizer.py
from PIL import Image, ImageDraw, ImageFont
import os

def visualize_regions(screenshot_path, output_path=None):
    """Draw region boxes on screenshot for visualization"""
    # Open the image
    img = Image.open(screenshot_path)
    width, height = img.size
    draw = ImageDraw.Draw(img)
    
    # Try to create a font - use default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 20)
        small_font = ImageFont.truetype("arial.ttf", 12)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Draw grid lines at 0.05 increments (light blue)
    for y in range(0, 21):  # 0 to 1.0 in steps of 0.05
        y_pos = int(y * 0.05 * height)
        draw.line([(0, y_pos), (width, y_pos)], fill="lightblue", width=1)
        # Add labels at every 0.1 steps to avoid cluttering
        if y % 2 == 0:
            draw.text((5, y_pos), f"{y*0.05:.2f}", fill="lightblue", font=small_font)
    
    for x in range(0, 21):  # 0 to 1.0 in steps of 0.05
        x_pos = int(x * 0.05 * width)
        draw.line([(x_pos, 0), (x_pos, height)], fill="lightblue", width=1)
        # Add labels at every 0.1 steps
        if x % 2 == 0:
            draw.text((x_pos, 5), f"{x*0.05:.2f}", fill="lightblue", font=small_font)
    
    # Define regions (same as in your OCR function)
    regions = {
        # Left panel
        'vehicle_name': (0.38, 0.43, 0.425, 0.46),      # Mercedes-AMG GT R '17
        'vehicle_weight': (0.38, 0.43, 0.425, 0.46),    # 3rd gear
        'front_weight_distribution': (0.435, 0.43, 0.46, 0.46),  # speed
        
        # Center panel - Body Height
        'front_ride_height': (0.49, 0.35, 0.53, 0.375),  # RPM
        'rear_ride_height': (0.42, 0.67, 0.46, 0.71),   # Final
        
        # Right panel - Downforce
        'front_downforce': (0.85, 0.15, 0.90, 0.18),    # Left value in Downforce
        'rear_downforce': (0.92, 0.15, 0.97, 0.18),     # Right value in Downforce
        
        # Bottom panel - Stability and G values
        'low_speed_stability': (0.30, 0.74, 0.34, 0.76),  # -0.19 (Low Speed)
        'high_speed_stability': (0.30, 0.78, 0.34, 0.80), # -1.00 (High Speed)
        'rotational_g_40mph': (0.30, 0.84, 0.34, 0.87),   # 1.40 G (40 mph)
        'rotational_g_75mph': (0.30, 0.88, 0.34, 0.91),   # 1.45 G (75 mph)
        'rotational_g_150mph': (0.30, 0.92, 0.34, 0.95),   # 1.63 G (150 mph)
        'performance_points': (0.30, 0.35, 0.34, 0.67),  # Adjust these coordinates for PP
        'front_tires': (0.51, 0.13, 0.63, 0.16),         # Adjust for front tires
        'rear_tires': (0.51, 0.17, 0.63, 0.21)
    }
    
    # Define colors for different types of regions
    colors = {
        'vehicle_name': "red",
        'vehicle_weight': "green", 
        'front_weight_distribution': "green",
        'front_ride_height': "blue",
        'rear_ride_height': "blue",
        'front_downforce': "purple",
        'rear_downforce': "purple",
        'low_speed_stability': "orange",
        'high_speed_stability': "orange",
        'rotational_g_40mph': "yellow",
        'rotational_g_75mph': "yellow",
        'rotational_g_150mph': "yellow"
    }
    
    # Draw each region
    for name, region in regions.items():
        # Convert percentage to pixels
        left = int(region[0] * width)
        top = int(region[1] * height)
        right = int(region[2] * width)
        bottom = int(region[3] * height)
        
        # Draw rectangle
        draw.rectangle([(left, top), (right, bottom)], outline=colors.get(name, "white"), width=3)
        
        # Draw label above rectangle
        draw.text((left, top-20), name, fill=colors.get(name, "white"), font=font)
        
        # Draw the coordinates for reference
        coord_text = f"({region[0]:.2f}, {region[1]:.2f}, {region[2]:.2f}, {region[3]:.2f})"
        draw.text((left, bottom+5), coord_text, fill=colors.get(name, "white"), font=small_font)
    
    # Save the modified image
    if output_path is None:
        output_path = os.path.splitext(screenshot_path)[0] + "_regions.jpg"
    
    img.save(output_path)
    print(f"Region visualization saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    # Use raw string prefix 'r' for Windows paths
    screenshot_path = r"C:\Users\philc\OneDrive\Desktop\RGT Gears.jpg"
    visualize_regions(screenshot_path)