# services/image_processing.py
import cv2
import numpy as np
import tempfile
import os
import logging
from typing import Tuple, Optional, Dict, List, Any
from PIL import Image

logger = logging.getLogger(__name__)

class ImageProcessingError(Exception):
    """Exception raised for errors in image processing."""
    pass


def detect_ui_regions(image_path: str, debug_mode: bool = False) -> Dict[str, Tuple[float, float, float, float]]:
    """
    Detect UI regions dynamically based on image content
    
    Args:
        image_path: Path to the image
        debug_mode: Whether to save debug images
        
    Returns:
        Dictionary mapping region names to normalized coordinates (x1, y1, x2, y2)
    """
    try:
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ImageProcessingError(f"Could not load image at {image_path}")
        
        height, width = img.shape[:2]
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Find edges
        edges = cv2.Canny(blurred, 50, 150)
        
        if debug_mode:
            debug_dir = os.path.join(os.path.dirname(image_path), 'debug_ui_detection')
            os.makedirs(debug_dir, exist_ok=True)
            cv2.imwrite(os.path.join(debug_dir, "edges.jpg"), edges)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by size to find potential UI elements
        min_area = width * height * 0.001  # Minimum area threshold (0.1% of image)
        max_area = width * height * 0.1    # Maximum area threshold (10% of image)
        
        ui_contours = [cnt for cnt in contours if min_area < cv2.contourArea(cnt) < max_area]
        
        if debug_mode:
            # Draw contours on original image for debugging
            debug_img = img.copy()
            cv2.drawContours(debug_img, ui_contours, -1, (0, 255, 0), 2)
            cv2.imwrite(os.path.join(debug_dir, "detected_regions.jpg"), debug_img)
        
        # Group contours into UI regions based on proximity and alignment
        ui_regions = {}
        
        # Simple approach: Use bounding boxes of contours as UI regions
        for i, contour in enumerate(ui_contours):
            x, y, w, h = cv2.boundingRect(contour)
            
            # Normalize coordinates
            x1 = x / width
            y1 = y / height
            x2 = (x + w) / width
            y2 = (y + h) / height
            
            # Add some padding
            padding = 0.01
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(1, x2 + padding)
            y2 = min(1, y2 + padding)
            
            ui_regions[f"region_{i}"] = (x1, y1, x2, y2)
        
        logger.debug(f"Detected {len(ui_regions)} UI regions")
        
        # If no regions detected, return empty dict
        if not ui_regions:
            logger.warning("No UI regions detected")
            return {}
        
        return ui_regions
        
    except Exception as e:
        logger.error(f"Error detecting text blocks: {str(e)}")
        return {}

def preprocess_gt7_screenshot(image_path):
    """
    Preprocess GT7 screenshot by inverting colors to make text more readable for Tesseract
    """
    try:
        # Create a temporary file to save the uploaded image
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp:
            for chunk in uploaded_file.chunks():
                temp.write(chunk)
            temp_path = temp.name
        
        # Load the image with OpenCV
        img = cv2.imread(temp_path)
        if img is None:
            raise ImageProcessingError(f"Could not load image at {temp_path}")
        
        # Invert colors if requested (for better OCR)
        if invert_colors:
            img = cv2.bitwise_not(img)
        
        # Save the processed image
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"processed_{os.path.basename(temp_path)}")
            cv2.imwrite(output_path, img)
            
            # Clean up temporary file
            if enhanced_path != temp_path:  # Only delete if different
                os.unlink(temp_path)
            
            return output_path
        else:
            # If no output directory, save to a new temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as out_temp:
                output_path = out_temp.name
            
            cv2.imwrite(output_path, img)
            
            # Clean up original temp file
            os.unlink(temp_path)
            
            return output_path
            
    except Exception as e:
        logger.error(f"Error processing screenshot: {str(e)}")
        raise ImageProcessingError(f"Failed to process screenshot: {str(e)}")

def crop_regions(image_path: str, regions: Dict[str, Tuple[float, float, float, float]], 
                output_dir: Optional[str] = None) -> Dict[str, str]:
    """
    Crop image to extract regions of interest
    
    Args:
        image_path: Path to the image
        regions: Dictionary mapping region names to normalized coordinates (x1, y1, x2, y2)
        output_dir: Directory to save cropped images (if None, uses temp files)
        
    Returns:
        Dictionary mapping region names to file paths of cropped images
    """
    try:
        # Load image with PIL for better handling
        with Image.open(image_path) as img:
            width, height = img.size
            
            # Create output directory if specified and doesn't exist
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            cropped_paths = {}
            
            for name, region in regions.items():
                # Convert normalized coordinates to pixels
                left = int(region[0] * width)
                top = int(region[1] * height)
                right = int(region[2] * width)
                bottom = int(region[3] * height)
                
                # Ensure valid coordinates
                left = max(0, left)
                top = max(0, top)
                right = min(width, right)
                bottom = min(height, bottom)
                
                # Skip if region is too small
                if right - left < 5 or bottom - top < 5:
                    logger.warning(f"Region {name} is too small, skipping")
                    continue
                
                # Crop the image
                cropped = img.crop((left, top, right, bottom))
                
                # Save to file
                if output_dir:
                    output_path = os.path.join(output_dir, f"{name}.jpg")
                    cropped.save(output_path)
                else:
                    # Use temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp:
                        temp_path = temp.name
                        cropped.save(temp_path)
                        output_path = temp_path
                
                cropped_paths[name] = output_path
            
            return cropped_paths
            
    except Exception as e:
        logger.error(f"Error cropping regions: {str(e)}")
        return {}

def detect_graph_area(image_path: str, debug_mode: bool = False) -> Optional[Tuple[float, float, float, float]]:
    """
    Detect graph area in the image (for power curves, etc.)
    
    Args:
        image_path: Path to the image
        debug_mode: Whether to save debug images
        
    Returns:
        Normalized coordinates (x1, y1, x2, y2) of the graph area or None if not found
    """
    try:
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ImageProcessingError(f"Could not load image at {image_path}")
        
        height, width = img.shape[:2]
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply Canny edge detection
        edges = cv2.Canny(blurred, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours to find rectangular shapes that could be graphs
        graph_candidates = []
        
        for cnt in contours:
            # Approximate contour to simplify shape
            epsilon = 0.02 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            
            # Check if approximated contour has 4 points (rectangular)
            if len(approx) == 4:
                # Check area ratio
                area = cv2.contourArea(cnt)
                x, y, w, h = cv2.boundingRect(cnt)
                rect_area = w * h
                
                area_ratio = area / rect_area if rect_area > 0 else 0
                
                # Graphs typically have a specific aspect ratio and area
                min_graph_area = width * height * 0.01  # At least 1% of image
                max_graph_area = width * height * 0.25  # At most 25% of image
                
                if (min_graph_area < area < max_graph_area and 
                    area_ratio > 0.7 and  # Fairly rectangular
                    0.5 < w/h < 2.0):     # Reasonable aspect ratio
                    
                    graph_candidates.append((x, y, w, h, area))
        
        if not graph_candidates:
            logger.warning("No graph area detected")
            return None
        
        # Sort candidates by area (descending)
        graph_candidates.sort(key=lambda x: x[4], reverse=True)
        
        # Take the largest candidate
        x, y, w, h, _ = graph_candidates[0]
        
        if debug_mode:
            debug_dir = os.path.join(os.path.dirname(image_path), 'debug_graph_detection')
            os.makedirs(debug_dir, exist_ok=True)
            
            # Draw detected graph area
            debug_img = img.copy()
            cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.imwrite(os.path.join(debug_dir, "detected_graph.jpg"), debug_img)
        
        # Normalize coordinates
        x1 = x / width
        y1 = y / height
        x2 = (x + w) / width
        y2 = (y + h) / height
        
        return (x1, y1, x2, y2)
        
    except Exception as e:
        logger.error(f"Error detecting graph area: {str(e)}")
        return None

def process_screenshot(uploaded_file, output_dir=None, debug_mode=False, invert_colors=False):
    """
    Process uploaded screenshot and save to file
    
    Args:
        uploaded_file: Django UploadedFile object
        output_dir: Directory to save processed image (if None, uses temp file)
        debug_mode: Whether to save debug information
        invert_colors: Whether to invert image colors for better OCR
        
    Returns:
        Path to the processed image
    """
    try:
        # Create a temporary file to save the uploaded image
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp:
            for chunk in uploaded_file.chunks():
                temp.write(chunk)
            temp_path = temp.name
        
        # Enhance image
        enhanced_path = temp_path
        
        # If we need to invert colors for better OCR (light text on dark background)
        if invert_colors:
            # Load the image
            img = cv2.imread(temp_path)
            if img is None:
                raise ImageProcessingError(f"Could not load image at {temp_path}")
            
            # Invert colors
            img = cv2.bitwise_not(img)
            
            # Save to a new temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as inverted_temp:
                inverted_path = inverted_temp.name
                cv2.imwrite(inverted_path, img)
            
            # Use this as our enhanced path
            enhanced_path = inverted_path
        
        # If output directory is provided, save the processed image there
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"processed_{os.path.basename(temp_path)}")
            
            # Copy the enhanced image to the output path
            with open(enhanced_path, 'rb') as src, open(output_path, 'wb') as dst:
                dst.write(src.read())
            
            # Clean up temporary files
            if enhanced_path != temp_path:  # Only delete enhanced path if it's different from temp_path
                os.unlink(enhanced_path)
            os.unlink(temp_path)
            
            return output_path
        else:
            # If no output directory, just return the enhanced path
            # Delete the original temp file if different
            if enhanced_path != temp_path:
                os.unlink(temp_path)
            
            return enhanced_path
            
    except Exception as e:
        logger.error(f"Error processing screenshot: {str(e)}")
        raise ImageProcessingError(f"Failed to process screenshot: {str(e)}")

def detect_text_blocks(image_path: str, debug_mode: bool = False) -> Dict[str, Tuple[float, float, float, float]]:
    """
    Detect text blocks in the image
    
    Args:
        image_path: Path to the image
        debug_mode: Whether to save debug images
        
    Returns:
        Dictionary mapping block IDs to normalized coordinates (x1, y1, x2, y2)
    """
    try:
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ImageProcessingError(f"Could not load image at {image_path}")
        
        height, width = img.shape[:2]
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            gray, 
            255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 
            11, 
            2
        )
        
        # Apply dilation to connect nearby text
        kernel = np.ones((5, 5), np.uint8)
        dilated = cv2.dilate(binary, kernel, iterations=3)
        
        if debug_mode:
            debug_dir = os.path.join(os.path.dirname(image_path), 'debug_text_detection')
            os.makedirs(debug_dir, exist_ok=True)
            cv2.imwrite(os.path.join(debug_dir, "binary.jpg"), binary)
            cv2.imwrite(os.path.join(debug_dir, "dilated.jpg"), dilated)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by size to find potential text blocks
        min_area = width * height * 0.0005  # Minimum area threshold (0.05% of image)
        max_area = width * height * 0.05    # Maximum area threshold (5% of image)
        
        text_contours = [cnt for cnt in contours if min_area < cv2.contourArea(cnt) < max_area]
        
        if debug_mode:
            # Draw contours on original image for debugging
            debug_img = img.copy()
            cv2.drawContours(debug_img, text_contours, -1, (0, 255, 0), 2)
            cv2.imwrite(os.path.join(debug_dir, "detected_text_blocks.jpg"), debug_img)
        
        # Extract bounding boxes for text blocks
        text_blocks = {}
        
        for i, contour in enumerate(text_contours):
            x, y, w, h = cv2.boundingRect(contour)
            
            # Normalize coordinates
            x1 = x / width
            y1 = y / height
            x2 = (x + w) / width
            y2 = (y + h) / height
            
            # Add some padding
            padding = 0.005
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(1, x2 + padding)
            y2 = min(1, y2 + padding)
            
            text_blocks[f"block_{i}"] = (x1, y1, x2, y2)
        
        logger.debug(f"Detected {len(text_blocks)} text blocks")
        
        return text_blocks
        
    except Exception as e:
        logger.error(f"Error detecting text blocks: {str(e)}")
        return {}