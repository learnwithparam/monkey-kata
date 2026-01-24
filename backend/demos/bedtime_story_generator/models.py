from pydantic import BaseModel, Field

"""
What is a Data Model?
- Defines the structure of incoming requests
- Automatically validates data (type checking, required fields)
- Provides clear error messages if validation fails
- Think of it as a "contract" for what your API expects

Example: If someone sends character_age as "five" instead of 5,
FastAPI will automatically return a 422 error with a helpful message.
"""

class StoryRequest(BaseModel):
    """Defines what data we need to generate a story"""
    
    character_name: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="The name of the story's main character"
    )
    
    character_age: int = Field(
        ..., 
        ge=1, 
        le=18,
        description="Age of the character (1-18 years)"
    )
    
    story_theme: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="The theme or topic of the story (e.g., 'friendship', 'adventure')"
    )
    
    story_length: str = Field(
        ...,
        description="Desired length: 'short', 'medium', or 'long'"
    )
