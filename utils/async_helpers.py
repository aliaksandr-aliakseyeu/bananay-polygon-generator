"""
Async utilities for Streamlit
Handles event loop configuration for Streamlit 1.37+
"""

import asyncio
import nest_asyncio


def setup_async():
    """
    Setup async support for Streamlit
    
    Streamlit 1.37+ has its own event loop which conflicts with asyncio.run().
    nest_asyncio allows nested event loops to work together.
    
    MUST be called at the very beginning of the app before any async operations.
    """
    nest_asyncio.apply()


def run_async(coro):
    """
    Safely run async coroutine in Streamlit context
    
    Args:
        coro: Async coroutine to execute
        
    Returns:
        Result of the coroutine execution
        
    Note:
        setup_async() must be called first!
    """
    return asyncio.run(coro)


