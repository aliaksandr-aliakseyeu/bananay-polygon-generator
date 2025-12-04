"""
CSS Styles for Polygon Generator UI
"""


def get_custom_css() -> str:
    """
    Get custom CSS styles for the application
    
    Returns:
        HTML string with CSS styles
    """
    return """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    </style>
    """


