from django import template
import logging

register = template.Library()
logger = logging.getLogger(__name__)

@register.simple_tag
def get_form_field(form, field_name):
    """
    Retrieve a form field dynamically by name
    """
    return getattr(form, field_name, None)

@register.filter
def get_attribute(obj, attr):
    """
    Safely access object attributes, dictionary keys, or nested attributes.
    
    Args:
        obj: The object or dictionary to access
        attr: Attribute/key to retrieve (supports dot notation for nested attributes)
    
    Returns:
        Attribute value or None if not found
    """
    try:
        # First check if this is a dictionary access
        if isinstance(obj, dict):
            return obj.get(attr)
            
        # Handle dot notation for nested attributes
        for part in attr.split('.'):
            obj = getattr(obj, part, None)
            if obj is None:
                return None
        return obj
    except Exception:
        return None

@register.filter
def call_with_arg(obj, arg):
    """
    Safely call a method on an object with a single argument.
    
    Args:
        obj: The object on which to call the method
        arg: A string in the format 'method_name:parameter_value'
    
    Returns:
        Result of the method call or None if an error occurs
    """
    try:
        # Validate input format
        if not arg or ':' not in arg:
            logger.warning(f"Invalid argument format: {arg}")
            return None
        
        # Split method and parameter
        method, param = arg.split(':', 1)
        
        # Validate method existence
        if not hasattr(obj, method):
            logger.warning(f"Method {method} not found on object {obj}")
            return None
        
        # Convert parameter to appropriate type
        try:
            param_value = int(param)
        except ValueError:
            try:
                param_value = float(param)
            except ValueError:
                param_value = param
        
        # Call method and return result
        return getattr(obj, method)(param_value)
    
    except Exception as e:
        logger.error(f"Error in call_with_arg filter: {e}")
        return None

@register.filter
def sub(value, arg):
    """
    Subtract two values with type conversion.
    
    Args:
        value: Minuend
        arg: Subtrahend
    
    Returns:
        Difference between values or empty string if conversion fails
    """
    try:
        return float(value) - float(arg)
    except (TypeError, ValueError):
        return ''
@register.filter
def sub(value, arg):
    """
    Subtract arg from value.
    
    Args:
        value: Minuend
        arg: Subtrahend
    
    Returns:
        Difference between values
    """
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return value
@register.filter
def get_range(value):
    """
    Generate a range of integers from 0 to value-1.
    
    Args:
        value: Upper bound of range (exclusive)
    
    Returns:
        Range object
    """
    try:
        return range(4, int(value) + 1)
    except (TypeError, ValueError):
        # Return an empty range if conversion fails
        return range(4, 4)
@register.filter
def index(value, index):
    """
    Returns the item at the given index from a list or similar sequence.
    
    Args:
        value: List-like object
        index: Index to retrieve
        
    Returns:
        Item at the specified index or None if index is invalid
    """
    try:
        return value[index]
    except (IndexError, TypeError):
        return None