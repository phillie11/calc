# power_graph_visualizer.py
from PIL import Image, ImageDraw, ImageFont
import os
import sys

def visualize_power_graph_regions(screenshot_path, output_path=None):
    """Draw region boxes on power graph screenshot for visualization"""
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
    
    # Define regions for power graph OCR
    regions = {
        # Power and BHP values at the top
        'power_value': (0.17, 0.36, 0.21, 0.39),     # Power value (like "575")
        'power_unit': (0.21, 0.36, 0.24, 0.39),      # Power unit (like "BHP")
        
        # Torque values 
        'torque_value': (0.17, 0.40, 0.21, 0.43),    # Torque value (like "68.7")
        'torque_unit': (0.21, 0.40, 0.24, 0.43),     # Torque unit (like "kgfm")
        
        # RPM values on the graph
        'min_rpm': (0.57, 0.32, 0.63, 0.35),         # Min RPM value (left side of graph)
        'max_rpm': (0.72, 0.32, 0.78, 0.35),         # Max RPM value (right side of graph)
        
        # The actual power curve graph region
        'power_curve_graph': (0.58, 0.09, 0.77, 0.32)  # Region containing the curve graph
    }
    
    # Define colors for different types of regions
    colors = {
        'power_value': "red",
        'power_unit': "red",
        'torque_value': "green",
        'torque_unit': "green",
        'min_rpm': "blue",
        'max_rpm': "blue",
        'power_curve_graph': "yellow"
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
        output_path = os.path.splitext(screenshot_path)[0] + "_power_regions.jpg"
    
    img.save(output_path)
    print(f"Power graph region visualization saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    # Check if path is passed as command line argument
    if len(sys.argv) > 1:
        screenshot_path = sys.argv[1]
    else:
        # Default path - edit this as needed
        screenshot_path = "C:/Users/philc/OneDrive/Desktop/RGT Dyno.JPG"
    
    # Run the visualization
    visualize_power_graph_regions(screenshot_path)