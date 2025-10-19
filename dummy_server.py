import re
from typing import List, Dict, Union, Tuple
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("basic")


@mcp.tool()
def analyze_text(text: str) -> Dict[str, Union[int, float]]:
    """
    Perform comprehensive text analysis.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Dictionary containing various text statistics
    """
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Basic counts
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    
    stats = {
        'word_count': len(words),
        'char_count': len(text),
        'sentence_count': len(sentences),
        'avg_word_length': round(sum(len(word) for word in words) / len(words), 2),
        'avg_sentence_length': round(len(words) / len(sentences), 2),
        'unique_words': len(set(word.lower() for word in words))
    }
    return stats

@mcp.tool()
def fibonacci_sum(n: int) -> Dict[str, Union[int, list]]:
    """
    Calculate Fibonacci sequence and its sum up to n numbers.
    
    Args:
        n: Number of Fibonacci sequence elements to generate
        
    Returns:
        Dictionary with sequence and sum
    """
    if n <= 0:
        return {'sequence': [], 'sum': 0}
        
    if n == 1:
        return {'sequence': [0], 'sum': 0}
        
    sequence = [0, 1]
    while len(sequence) < n:
        sequence.append(sequence[-1] + sequence[-2])
        
    return {
        'sequence': sequence,
        'sum': sum(sequence)
    }

@mcp.tool()
def convert_distance(value: float, from_unit: str, to_unit: str) -> Dict[str, Union[float, str]]:
    """
    Convert between different distance units.
    
    Args:
        value: Distance value to convert
        from_unit: Source unit (km/mi/m/cm/ft)
        to_unit: Target unit (km/mi/m/cm/ft)
        
    Returns:
        Dictionary with converted value and unit
    """
    # Conversion factors to meters
    to_meters = {
        'cm': 0.01,
        'm': 1,
        'km': 1000,
        'mi': 1609.34,
        'ft': 0.3048
    }
    
    if from_unit not in to_meters or to_unit not in to_meters:
        raise ValueError("Invalid unit. Use: m, km, mi, ft")
    
    # Convert to meters first
    meters = value * to_meters[from_unit]
    # Convert to target unit
    result = meters / to_meters[to_unit]
    
    return {
        'value': round(result, 3),
        'unit': to_unit,
        'original': f"{value} {from_unit}"
    }
if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
