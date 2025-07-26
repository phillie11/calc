# services/ocr_service.py
import pytesseract
import io
import re
import os
import logging
import tempfile
import json
from typing import Dict, Any, Optional, Union, List
from PIL import Image
import numpy as np
import cv2
from datetime import datetime

logger = logging.getLogger(__name__)

class OCRError(Exception):
    """Exception raised for errors in OCR processing."""
    pass

class OCRProcessor:
    """Base class for OCR processing of game screenshots using Tesseract"""
    
    def __init__(self, debug_mode: bool = False):
        """Initialize the OCR processor
        
        Args:
            debug_mode: Whether to save debug information
        """
        self.debug_mode = debug_mode
        self.debug_info = {}
        
    def process_image(self, image_path: str, regions: Dict[str, tuple]) -> Dict[str, Any]:
        """Process an image and extract text from defined regions
        
        Args:
            image_path: Path to the image file
            regions: Dictionary mapping parameter names to regions (x1, y1, x2, y2) as percentages
            
        Returns:
            Dictionary of extracted values
        """
        try:
            # Get image dimensions
            with Image.open(image_path) as img:
                width, height = img.size
            
            # Initialize results
            results = {}
            self.debug_info = {}
            
            # Create debug directory if in debug mode
            debug_dir = None
            if self.debug_mode:
                debug_dir = os.path.join(os.path.dirname(image_path), 'debug_regions')
                os.makedirs(debug_dir, exist_ok=True)
            
            # Process the whole image first for debugging
            if self.debug_mode:
                try:
                    # Use Tesseract OCR on the full image for debugging
                    full_text = pytesseract.image_to_string(image_path)
                    self.debug_info['full_text'] = full_text
                    logger.debug("Full text detected in image:")
                    logger.debug("-" * 50)
                    logger.debug(full_text)
                    logger.debug("-" * 50)
                except Exception as e:
                    self.debug_info['full_text'] = f"Error getting full text: {str(e)}"
                    logger.warning(f"Error in full image OCR: {str(e)}")
            
            # Process each region
            for param_name, region_pct in regions.items():
                try:
                    # Convert percentage to actual pixel coordinates
                    left = int(region_pct[0] * width)
                    top = int(region_pct[1] * height)
                    right = int(region_pct[2] * width)
                    bottom = int(region_pct[3] * height)
                    
                    # Create a cropped image
                    with Image.open(image_path) as img:
                        cropped = img.crop((left, top, right, bottom))
                        
                        # Save cropped image for debugging
                        if self.debug_mode and debug_dir:
                            debug_path = os.path.join(debug_dir, f"{param_name}_region.jpg")
                            cropped.save(debug_path)
                        
                        # Save to temporary file for Tesseract
                        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp:
                            temp_path = temp.name
                            cropped.save(temp_path)
                    
                    # Process with Tesseract OCR
                    # You can customize the config for better recognition based on content type
                    try:
                        if param_name in ['rpm', 'gear_ratio', 'final_drive', 'speed']:
                            # Use a completely different configuration approach - no char whitelist
                            # Just specify the page segmentation mode
                            config = '--oem 3 --psm 7'  # PSM 7 is for single line of text
                        else:
                            # Default configuration for other text
                            config = '--oem 3 --psm 6'
    
                        region_text = pytesseract.image_to_string(temp_path, config=config).strip()
                    except Exception as tesseract_error:
                        logger.warning(f"Tesseract error for {param_name}: {str(tesseract_error)}")
                        region_text = ""
                        
                    # Delete the temporary file
                    os.unlink(temp_path)
                    
                    # Extract text from the region
                    if region_text:
                        if self.debug_mode:
                            self.debug_info[param_name] = region_text
                        logger.debug(f"{param_name}: Found text: '{region_text}'")
                        
                        # Process the text based on parameter name (subclasses will implement this)
                        processed_value = self._process_text(param_name, region_text)
                        if processed_value is not None:
                            results[param_name] = processed_value
                    else:
                        if self.debug_mode:
                            self.debug_info[param_name] = "No text detected"
                        logger.debug(f"{param_name}: No text detected in this region")
                
                except Exception as e:
                    logger.error(f"Error processing region {param_name}: {str(e)}")
                    if self.debug_mode:
                        self.debug_info[param_name] = f"Error: {str(e)}"
            
            # Save debug info if in debug mode
            if self.debug_mode:
                debug_file_path = os.path.join(os.path.dirname(image_path), f'ocr_debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                with open(debug_file_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'debug_info': self.debug_info,
                        'results': results
                    }, f, indent=2)
                logger.info(f"OCR debug information saved to {debug_file_path}")
            
            return results
        
        except Exception as e:
            logger.error(f"Error in OCR processing: {str(e)}")
            raise OCRError(f"Failed to process image: {str(e)}")
    
    def _process_text(self, param_name: str, text: str) -> Optional[Any]:
        """Process extracted text based on parameter name
        
        Subclasses should override this method to implement specific processing
        
        Args:
            param_name: Name of the parameter
            text: Extracted text
            
        Returns:
            Processed value or None if processing failed
        """
        return text  # Base implementation just returns the text

def extract_ride_height_directly(image_path, is_front=True):
    """
    Extract ride height values directly from an image using OCR on the full image
    
    Args:
        image_path: Path to the screenshot
        is_front: True if looking for front ride height, False for rear
        
    Returns:
        Integer value of the ride height or None if not found
    """
    try:
        # Load the image
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Could not load image at {image_path}")
            return None
        
        # Invert the image (GT7 has light text on dark background)
        inverted = cv2.bitwise_not(img)
        
        # Run OCR on the full image
        full_text = pytesseract.image_to_string(inverted).strip()
        
        # Debug output
        logger.debug(f"Full text from inverted image: {full_text}")
        
        # Define specific search patterns that clearly identify front or rear
        if is_front:
            specific_patterns = [
                r'front\s*height[\s:]*(\d+)',
                r'front[\s:]*(\d+)\s*mm',
                r'front.*?(\d+)\s*mm',
                r'f\.height[\s:]*(\d+)',
                r'f[\s:]*(\d+)\s*mm'
            ]
        else:
            specific_patterns = [
                r'rear\s*height[\s:]*(\d+)',
                r'rear[\s:]*(\d+)\s*mm',
                r'rear.*?(\d+)\s*mm',
                r'r\.height[\s:]*(\d+)',
                r'r[\s:]*(\d+)\s*mm'
            ]
        
        # Try each specific pattern first
        for pattern in patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                value = int(match.group(1))
                logger.info(f"Found {'front' if is_front else 'rear'} ride height in full text: {value}")
                return value
        
        # As a fallback, look for any occurrence of "mm" followed by digits
        mm_pattern = r'mm\s*(\d+)'
        mm_matches = re.findall(mm_pattern, full_text, re.IGNORECASE)
        
        if mm_matches:
            # If we're looking for front height, take the first match
            # If we're looking for rear height, take the second match (if available)
            index = 0 if is_front else (1 if len(mm_matches) > 1 else 0)
            value = int(mm_matches[index])
            logger.info(f"Found {'front' if is_front else 'rear'} ride height using mm pattern at index {index}: {value}")
            return value
        
        # Still no match, return None
        logger.warning(f"Could not extract {'front' if is_front else 'rear'} ride height from full text")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting ride height directly: {str(e)}")
        return None

class SuspensionOCRProcessor(OCRProcessor):
    """OCR processor for suspension screenshots"""
    
    def __init__(self, debug_mode: bool = False):
        super().__init__(debug_mode)
        # Define regions for suspension screenshot
        self.regions = {
            'vehicle_name': (0.02, 0.20, 0.20, 0.23),
            'vehicle_weight': (0.30, 0.48, 0.34, 0.52),
            'front_weight_distribution': (0.29, 0.52, 0.315, 0.56),
            'front_ride_height': (0.54, 0.33, 0.58, 0.37),
            'rear_ride_height': (0.62, 0.33, 0.66, 0.37),
            'front_downforce': (0.85, 0.15, 0.90, 0.18),
            'rear_downforce': (0.92, 0.15, 0.98, 0.18),
            'low_speed_stability': (0.30, 0.74, 0.34, 0.76),
            'high_speed_stability': (0.30, 0.78, 0.34, 0.80),
            'rotational_g_40mph': (0.30, 0.84, 0.34, 0.87),
            'rotational_g_75mph': (0.30, 0.88, 0.34, 0.91),
            'rotational_g_150mph': (0.30, 0.92, 0.34, 0.95),
            'performance_points': (0.29, 0.32, 0.34, 0.35),
            'front_tires': (0.51, 0.13, 0.63, 0.16),
            'rear_tires': (0.51, 0.17, 0.63, 0.21)
        }
    
    def process_screenshot(self, image_path: str) -> Dict[str, Any]:
        """Process a suspension screenshot
        
        Args:
            image_path: Path to the screenshot
            
        Returns:
            Dictionary of extracted values
        """
        return self.process_image(image_path, self.regions)

    def process_image_for_digits(image_path, region=None):
        """
        Process image optimized for digit extraction
        """
        img = cv2.imread(image_path)
    
        # If region is specified, crop the image
        if region:
            height, width = img.shape[:2]
            left = int(width * region[0])
            top = int(height * region[1])
            right = int(width * region[2])
            bottom = int(height * region[3])
            img = img[top:bottom, left:right]
    
        # Preprocess
        processed = preprocess_image_for_tesseract(img)
    
        # Configure Tesseract for digits
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.,'
    
        # Process with Tesseract
        result = pytesseract.image_to_string(processed, config=custom_config).strip()
    
        return result

        
    def _process_text(self, param_name: str, text: str) -> Optional[Any]:
        """Process text for suspension parameters"""
        try:
            if param_name == 'vehicle_weight':
                # Extract digits, remove commas
                match = re.search(r'([0-9,]+)', text.replace(',', ''))
                return int(match.group(1)) if match else None
        
            elif param_name == 'front_weight_distribution':
                # Look for X:Y format first
                match = re.search(r'(\d+)\s*:\s*\d+', text)
                if match:
                    return int(match.group(1))
                # If not found, look for any integer
                match = re.search(r'(\d+)', text)
                return int(match.group(1)) if match else 50  # Default to 50%

            elif param_name in ['front_ride_height', 'rear_ride_height']:
                # Extract the numeric value
                match = re.search(r'(\d+)', text)
                if match:
                    logger.debug(f"Found {param_name} value: {match.group(1)}")
                    return int(match.group(1))
                return None
        
            elif param_name in ['front_downforce', 'rear_downforce']:
                # Log the raw text for debugging
                logger.debug(f"Raw text for {param_name}: '{text}'")
    
                # Simply extract the first sequence of digits
                match = re.search(r'(\d+)', text)
                if match:
                    logger.debug(f"Basic digit sequence matched for {param_name}: {match.group(1)}")
                    return int(match.group(1))
    
                # If that fails, clean up the text and try again
                cleaned_text = re.sub(r'[^\w\s]', '', text).strip()
                logger.debug(f"Cleaned text for {param_name}: '{cleaned_text}'")
    
                match = re.search(r'(\d+)', cleaned_text)
                if match:
                    logger.debug(f"Basic digit sequence matched for {param_name} after cleanup: {match.group(1)}")
                    return int(match.group(1))
    
                # If still no match, look for any digits
                all_digits = re.findall(r'\d+', cleaned_text)
                if all_digits:
                    # Take the first sequence of digits found
                    logger.debug(f"Taking first digit sequence for {param_name}: {all_digits[0]}")
                    return int(all_digits[0])
    
                # No valid downforce value found
                return None
            
            elif param_name in ['low_speed_stability', 'high_speed_stability', 'rotational_g_40mph', 'rotational_g_75mph', 'rotational_g_150mph']:
                # Extract decimal number, may be negative
                match = re.search(r'(-?\d+\.\d+)', text)
                if match:
                    return float(match.group(1))
                # Try just extracting integer part
                match = re.search(r'(-?\d+)', text)
                return float(match.group(1)) if match else 0.0
            
            elif param_name == 'performance_points':
                # Look for PP followed by number
                match = re.search(r'PP\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
                if match:
                    return float(match.group(1))
                # Try extracting any decimal
                match = re.search(r'(\d+\.\d+)', text)
                if match:
                    return float(match.group(1))
                # Try just an integer
                match = re.search(r'(\d+)', text)
                return float(match.group(1)) if match else 0
            
            elif param_name in ['front_tires', 'rear_tires']:
                return self._extract_tire_type(text)
                
            return None
        except Exception as e:
            logger.error(f"Error processing text for {param_name}: {str(e)}")
            return None

    
    def _extract_tire_type(self, text: str) -> str:
        """Extract tire type from text with fuzzy matching and confidence scores"""
        # Clean up text
        cleaned_text = text.lower().strip()
        
        # Define tire types with keywords and aliases
        tire_types = {
            'CH': ['comfort: hard', 'comfort hard', 'ch', 'comfort h', 'hard comfort'],
            'CM': ['comfort: medium', 'comfort medium', 'cm', 'comfort m', 'medium comfort'],
            'CS': ['comfort: soft', 'comfort soft', 'cs', 'comfort s', 'soft comfort'],
            'SH': ['sports: hard', 'sports hard', 'sport: hard', 'sport hard', 'sh', 'sports h', 'sport h', 'hard sport'],
            'SM': ['sports: medium', 'sports medium', 'sport: medium', 'sport medium', 'sm', 'sports m', 'sport m', 'medium sport'],
            'SS': ['sports: soft', 'sports soft', 'sport: soft', 'sport soft', 'ss', 'sports s', 'sport s', 'soft sport'],
            'RH': ['racing: hard', 'racing hard', 'rh', 'racing h', 'hard racing'],
            'RM': ['racing: medium', 'racing medium', 'rm', 'racing m', 'medium racing'],
            'RS': ['racing: soft', 'racing soft', 'rs', 'racing s', 'soft racing'],
            'RI': ['racing: intermediate', 'racing intermediate', 'ri', 'intermediate', 'inter', 'int racing'],
            'RW': ['racing: heavy wet', 'racing heavy wet', 'racing wet', 'rw', 'wet', 'heavy wet', 'rain']
        }
        
        # Score each tire type
        scores = {}
        for code, keywords in tire_types.items():
            # Calculate match score based on how many keywords appear
            score = sum(1 for keyword in keywords if keyword in cleaned_text)
            # Boost score for exact matches
            score += sum(3 for keyword in keywords if keyword == cleaned_text)
            # Partial word matches
            for keyword in keywords:
                if keyword in cleaned_text and len(keyword) > 2:
                    score += 0.5
            scores[code] = score
        
        # Get the highest scoring tire type
        if any(scores.values()):
            best_match = max(scores.items(), key=lambda x: x[1])
            if best_match[1] > 0:
                return best_match[0]
        
        # Default to Racing Medium if no match
        return 'RM'


class PowerOCRProcessor(OCRProcessor):
    """OCR processor for power curve screenshots"""
    
    def __init__(self, debug_mode: bool = False):
        super().__init__(debug_mode)
        # Define regions for power screenshot
        self.regions = {
            'power_hp': (0.28, 0.34, 0.36, 0.39),
            'torque_kgfm': (0.28, 0.38, 0.36, 0.43),
            'min_rpm': (0.55, 0.30, 0.63, 0.35),
            'max_rpm': (0.70, 0.30, 0.78, 0.35),
            'max_power_rpm_region': (0.50, 0.20, 0.80, 0.40)  # Larger region to extract max power RPM text
        }
    
    def process_screenshot(self, image_path: str) -> Dict[str, Any]:
        """Process a power curve screenshot
        
        Args:
            image_path: Path to the screenshot
            
        Returns:
            Dictionary of extracted values
        """
        results = self.process_image(image_path, self.regions)
        
        # Extract max power RPM from graph if needed
        if ('min_rpm' in results and 'max_rpm' in results and 
            ('max_power_rpm' not in results or not results['max_power_rpm'])):
            try:
                max_power_rpm = self._extract_max_power_rpm_from_graph(
                    image_path, 
                    results['min_rpm'], 
                    results['max_rpm']
                )
                results['max_power_rpm'] = max_power_rpm
            except Exception as e:
                logger.error(f"Error extracting max power RPM from graph: {str(e)}")
                # Fallback estimation
                if 'min_rpm' in results and 'max_rpm' in results:
                    results['max_power_rpm'] = int(
                        results['min_rpm'] + 
                        (results['max_rpm'] - results['min_rpm']) * 0.75
                    )
                else:
                    results['max_power_rpm'] = 6500  # Default value
        
        if all(key in results for key in ['min_rpm', 'max_rpm', 'torque_kgfm', 'power_hp']):
            try:
                from services.engine_data import process_engine_data
                engine_data_results = process_engine_data(
                    image_path, 
                    results
                )
                # Update results with engine data
                results.update(engine_data_results)
            except Exception as e:
                logger.error(f"Error processing engine data: {str(e)}")
    
        return results 
    
    def _process_text(self, param_name: str, text: str) -> Optional[Any]:
        """Process text for power parameters"""
        try:
            if param_name == 'power_hp':
                # Look for power value with HP/BHP/PS unit
                match = re.search(r'(\d+)\s*(?:BHP|HP|PS|bhp|hp|ps)', text, re.IGNORECASE)
                if match:
                    return int(match.group(1))
                # Try just an integer
                match = re.search(r'(\d+)', text)
                return int(match.group(1)) if match else None
            
            elif param_name == 'torque_kgfm':
                # Extract any decimal number
                match = re.search(r'(\d+(?:\.\d+)?)', text)
                return float(match.group(1)) if match else None
            
            elif param_name in ['min_rpm', 'max_rpm']:
                # Extract number, remove commas
                match = re.search(r'(\d+(?:,\d+)?)', text.replace(',', ''))
                return int(match.group(1)) if match else None
            
            elif param_name == 'max_power_rpm_region':
                # Try to find a pattern like "XXX HP @ YYYY RPM"
                match = re.search(r'@\s*(\d+(?:,\d+)?)\s*(?:RPM|rpm)', text.replace(',', ''))
                if match:
                    return int(match.group(1))
                # Try other patterns
                match = re.search(r'(?:at|@)\s*(\d+(?:,\d+)?)', text.replace(',', ''))
                return int(match.group(1)) if match else None
                
            return None
        except Exception as e:
            logger.error(f"Error processing text for {param_name}: {str(e)}")
            return None
    
    def _extract_max_power_rpm_from_graph(self, image_path: str, min_rpm: int, max_rpm: int) -> int:
        """Extract the RPM value at maximum power by analyzing the power curve graph
        
        Args:
            image_path: Path to the screenshot
            min_rpm: Minimum RPM value
            max_rpm: Maximum RPM value
            
        Returns:
            RPM value at maximum power
        """
        try:
            # Load the image with OpenCV
            img = cv2.imread(image_path)
            if img is None:
                raise OCRError(f"Could not load image at {image_path}")
            
            height, width = img.shape[:2]
            
            # Define graph region (approximately where the power curve is shown)
            graph_region = (0.585, 0.095, 0.77, 0.32)  # (left, top, right, bottom) as percentages
            
            # Convert to pixel coordinates
            left = int(width * graph_region[0])
            top = int(height * graph_region[1])
            right = int(width * graph_region[2])
            bottom = int(height * graph_region[3])
            
            # Crop the image to the graph region
            cropped_img = img[top:bottom, left:right]
            
            # Save cropped region for debugging
            if self.debug_mode:
                debug_dir = os.path.join(os.path.dirname(image_path), 'debug_power_regions')
                os.makedirs(debug_dir, exist_ok=True)
                cv2.imwrite(os.path.join(debug_dir, "power_graph_region.jpg"), cropped_img)
            
            # Create a mask to isolate the power curve (usually in a distinct color like blue/cyan)
            # The power curve in GT7 is typically cyan (high blue and green, low red)
            blue = cropped_img[:, :, 0]
            green = cropped_img[:, :, 1]
            red = cropped_img[:, :, 2]
            
            # Create mask where blue is high, green is high, and red is low (cyan color)
            power_mask = cv2.inRange(cropped_img, 
                                   np.array([160, 160, 0]),   # Lower bound for cyan
                                   np.array([255, 255, 100]))  # Upper bound for cyan
            
            # Save the mask for debugging
            if self.debug_mode:
                cv2.imwrite(os.path.join(debug_dir, "power_curve_mask.jpg"), power_mask)
            
            # Find all non-zero pixels (the power curve)
            y_indices, x_indices = np.where(power_mask > 0)
            
            if len(x_indices) == 0:
                logger.warning("No power curve found in the image, using default estimation")
                return int(min_rpm + (max_rpm - min_rpm) * 0.75)
            
            # Create a map of x positions to lowest y positions (highest point on graph)
            # In images, lower y values are higher on the graph (power peak)
            x_to_min_y = {}
            for x, y in zip(x_indices, y_indices):
                if x not in x_to_min_y or y < x_to_min_y[x]:
                    x_to_min_y[x] = y
            
            # Find the x position with the lowest y (peak of power curve)
            if not x_to_min_y:
                return int(min_rpm + (max_rpm - min_rpm) * 0.75)
            
            # Get the highest points (lowest y values)
            sorted_by_height = sorted(x_to_min_y.items(), key=lambda item: item[1])
            highest_points = sorted_by_height[:5]  # Take the 5 highest points
            
            # Average the x positions of the highest points for stability
            peak_x_positions = [x for x, y in highest_points]
            peak_x = sum(peak_x_positions) / len(peak_x_positions)
            
            # For visualization in debug mode
            if self.debug_mode:
                visualization_img = cropped_img.copy()
                for x, y in highest_points:
                    cv2.circle(visualization_img, (x, y), 3, (0, 0, 255), -1)  # Red circles
                
                # Draw a larger circle at the average peak position
                avg_y = sum([y for _, y in highest_points]) / len(highest_points)
                cv2.circle(visualization_img, (int(peak_x), int(avg_y)), 5, (255, 0, 0), -1)  # Blue circle
                
                cv2.imwrite(os.path.join(debug_dir, "power_peak_detected.jpg"), visualization_img)
            
            # Calculate the relative position of the peak on the x-axis
            crop_width = cropped_img.shape[1]
            relative_position = peak_x / crop_width
            
            # Map the relative position to the RPM range
            rpm_at_max_power = int(min_rpm + relative_position * (max_rpm - min_rpm))
            
            # Round to nearest 25 RPM (as is common in engine specs)
            rpm_at_max_power = int(round(rpm_at_max_power / 25) * 25)
            
            logger.debug(f"Calculated RPM at max power: {rpm_at_max_power} (peak at {relative_position:.2f} of x-axis)")
            
            return rpm_at_max_power
            
        except Exception as e:
            logger.error(f"Error extracting max power RPM from graph: {str(e)}")
            # Fallback to default estimation
            return int(min_rpm + (max_rpm - min_rpm) * 0.75)


class TransmissionOCRProcessor(OCRProcessor):
    """OCR processor for transmission screenshots"""
    
    def __init__(self, debug_mode: bool = False):
        super().__init__(debug_mode)
        # Define regions for transmission screenshot
        self.regions = {
            'gear_ratio': (0.38, 0.43, 0.425, 0.46),
            'rpm': (0.49, 0.35, 0.53, 0.375),
            'speed': (0.435, 0.43, 0.46, 0.46),
            'final_drive': (0.42, 0.67, 0.46, 0.71),
            'gear_section': (0.30, 0.35, 0.34, 0.67)  # For detecting number of gears
        }
    
    def process_screenshot(self, image_path: str) -> Dict[str, Any]:
        """Process a transmission screenshot
        
        Args:
            image_path: Path to the screenshot
            
        Returns:
            Dictionary of extracted values
        """
        return self.process_image(image_path, self.regions)
    
    def _process_text(self, param_name: str, text: str) -> Optional[Any]:
        """Process text for transmission parameters"""
        try:
            if param_name == 'gear_ratio':
                match = re.search(r'(\d+(?:\.\d+)?)', text)
                return float(match.group(1)) if match else None
            
            elif param_name == 'rpm':
                # First try with rpm suffix
                match = re.search(r'(\d+(?:,\d+)?)', text.replace(',', ''))
                return int(match.group(1)) if match else None
            
            elif param_name == 'speed':
                # Look for numbers followed by speed units
                match = re.search(r'(\d+)', text)
                return int(match.group(1)) if match else None
            
            elif param_name == 'final_drive':
                match = re.search(r'(\d+(?:\.\d+)?)', text)
                return float(match.group(1)) if match else None
            
            elif param_name == 'gear_section':
                return self._extract_num_gears(text)
                
            return None
        except Exception as e:
            logger.error(f"Error processing text for {param_name}: {str(e)}")
            return None
    
    def _extract_num_gears(self, text: str) -> int:
        """Extract the number of gears from gear section text"""
        try:
            # Try to detect all gear numbers in the text (like 1st, 2nd, etc.)
            gear_matches = re.findall(r'(\d+)(?:st|nd|rd|th)', text.lower())
            
            # Count unique gear numbers
            if gear_matches:
                unique_gears = set([int(g) for g in gear_matches if g.isdigit()])
                num_gears = max(unique_gears) if unique_gears else 6
                
                # Validate range (4-9)
                if 4 <= num_gears <= 9:
                    return num_gears
            
            # Alternative detection - count lines containing 'gear' or ordinals
            lines = text.lower().split('\n')
            gear_lines = [l for l in lines if 'gear' in l or '1st' in l or '2nd' in l or 
                         '3rd' in l or '4th' in l or '5th' in l or '6th' in l or 
                         '7th' in l or '8th' in l or '9th' in l]
            
            if gear_lines:
                num_gears = len(gear_lines)
                # Validate range
                if 4 <= num_gears <= 9:
                    return num_gears
            
            # Default to 6 gears
            return 6
            
        except Exception as e:
            logger.error(f"Error extracting number of gears: {str(e)}")
            return 6  # Default to 6 gears


# Module-level functions for backward compatibility
def process_uploaded_screenshot(uploaded_file, debug_mode: bool = False):
    """Process an uploaded suspension screenshot"""
    # Check if uploaded_file is a file object or string path
    if hasattr(uploaded_file, 'read') and callable(uploaded_file.read):
        # Create a temporary file to save the uploaded image
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp:
            for chunk in uploaded_file.chunks():
                temp.write(chunk)
            temp_path = temp.name
    else:
        # Assume it's already a path
        temp_path = uploaded_file
    
    try:
        # Extract inputs using OCR
        processor = SuspensionOCRProcessor(debug_mode=debug_mode)
        inputs = processor.process_screenshot(temp_path)
        
        # Check if ride height values are in the debug_info but not in the results
        if debug_mode and hasattr(processor, 'debug_info'):
            if 'front_ride_height' in processor.debug_info and 'front_ride_height' not in inputs:
                try:
                    front_height = int(processor.debug_info['front_ride_height'])
                    inputs['front_ride_height'] = front_height
                    logger.info(f"Added front_ride_height from debug_info: {front_height}")
                except (ValueError, TypeError):
                    pass
                    
            if 'rear_ride_height' in processor.debug_info and 'rear_ride_height' not in inputs:
                try:
                    rear_height = int(processor.debug_info['rear_ride_height'])
                    inputs['rear_ride_height'] = rear_height
                    logger.info(f"Added rear_ride_height from debug_info: {rear_height}")
                except (ValueError, TypeError):
                    pass
        
        # Delete temp file if not in debug mode and if we created it
        if not debug_mode and hasattr(uploaded_file, 'read'):
            os.unlink(temp_path)
        
        return inputs
    except Exception as e:
        # Keep temp file for debugging if in debug mode
        if not debug_mode and hasattr(uploaded_file, 'read'):
            os.unlink(temp_path)
        raise e

def extract_power_data_from_screenshot(image_path, debug_mode: bool = False):
    """Extract power data from screenshot
    
    Args:
        image_path: Path to the screenshot
        debug_mode: Whether to save debug information
        
    Returns:
        Dictionary of extracted values
    """
    processor = PowerOCRProcessor(debug_mode=debug_mode)
    return processor.process_screenshot(image_path)

    if all(key in results for key in ['min_rpm', 'max_rpm', 'torque_kgfm', 'power_hp']):
        try:
            results = process_engine_data(image_path, results)
        except Exception as e:
            logger.error(f"Error processing engine data: {str(e)}")
    
    return results

def process_transmission_screenshot(uploaded_file, debug_mode: bool = False):
    """Process an uploaded transmission screenshot
    
    Args:
        uploaded_file: Django UploadedFile object or path to image file
        debug_mode: Whether to save debug information
        
    Returns:
        Dictionary of extracted values
    """
    # Check if uploaded_file is a file object or string path
    if hasattr(uploaded_file, 'read') and callable(uploaded_file.read):
        # Create a temporary file to save the uploaded image
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp:
            for chunk in uploaded_file.chunks():
                temp.write(chunk)
            temp_path = temp.name
    else:
        # Assume it's already a path
        temp_path = uploaded_file
    
    try:
        # Extract data using OCR
        processor = TransmissionOCRProcessor(debug_mode=debug_mode)
        transmission_data = processor.process_screenshot(temp_path)
        
        # Delete temp file if not in debug mode and if we created it
        if not debug_mode and hasattr(uploaded_file, 'read'):
            os.unlink(temp_path)
        
        return transmission_data
    except Exception as e:
        # Keep temp file for debugging if in debug mode
        if not debug_mode and hasattr(uploaded_file, 'read'):
            os.unlink(temp_path)
        raise e