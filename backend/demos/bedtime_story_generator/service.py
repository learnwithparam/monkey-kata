from typing import AsyncGenerator
import json
import asyncio
from utils.llm_provider import get_llm_provider, _fix_streaming_chunk_spacing
from .models import StoryRequest

# Initialize the AI provider (automatically selects based on your API keys)
llm_provider = get_llm_provider()

"""
What is Prompt Engineering?
- The art of writing instructions that guide AI to produce desired output
- Good prompts are: clear, specific, and structured
- This is where you teach the AI what you want

Key Prompt Engineering Techniques Used Here:
1. Role-Setting: Tell the AI who it is ("bedtime storyteller")
2. Context: Provide user inputs (character name, age, theme)
3. Instructions: Specify format, length, style
4. Constraints: Set boundaries (age-appropriate, specific word count)

💡 Try This: Modify this prompt and see how the story quality changes!
"""
def build_story_prompt(request: StoryRequest) -> str:
    """
    Builds a well-structured prompt for the AI
    
    This function takes user inputs and combines them into a clear
    instruction that tells the AI exactly what kind of story to write.
    """
    # Define length requirements - maps user selection to specific instructions
    length_map = {
        "short": "3-5 paragraphs, approximately 40-60 words",
        "medium": "5-7 paragraphs, approximately 100-150 words",
        "long": "8-12 paragraphs, approximately 200-300 words"
    }
    
    # Build the prompt step by step for clarity
    prompt = f"""You are a creative and gentle bedtime storyteller.

Write a personalized bedtime story with these details:
- Main character: {request.character_name}, age {request.character_age}
- Theme: {request.story_theme}
- Length: {length_map.get(request.story_length, length_map['medium'])}

Requirements:
1. Start with an engaging title
2. Write in clear paragraphs with natural breaks
3. Make it age-appropriate for a {request.character_age}-year-old
4. End with a gentle moral lesson about kindness, bravery, or friendship
5. Keep the tone warm, comforting, and suitable for bedtime

Begin the story now:"""

    return prompt

"""
What is Streaming?
- Instead of waiting for the entire story, send it piece by piece
- Creates a "typing" effect like ChatGPT
- Feels faster and more interactive to users

How Streaming Works:
1. AI generates text in small chunks (tokens)
2. Each chunk is sent immediately to the frontend
3. Frontend displays chunks as they arrive
4. User sees story appear in real-time

Technical Details:
- Uses async generators (async functions with 'yield')
- Formats as Server-Sent Events (SSE) with "data: {json}\n\n"
- Keeps connection alive until story is complete
"""
async def generate_story_stream(request: StoryRequest) -> AsyncGenerator[str, None]:
    """
    Generates and streams a story in real-time
    
    This is an async generator - it yields chunks of data as they're generated.
    Each yield sends data to the frontend immediately.
    """
    # Step 1: Notify frontend that connection is established
    yield f"data: {json.dumps({'status': 'connected', 'message': 'Starting story generation...'})}\n\n"
    
    # Step 1.1: Emit thinking events for the creative process
    thinking_analysis = {'thinking': {'category': 'analysis', 'content': f'Developing a story for a {request.character_age}-year-old named {request.character_name} with the theme of {request.story_theme}...', 'timestamp': 'now'}}
    yield f"data: {json.dumps(thinking_analysis)}\n\n"
    await asyncio.sleep(0.5)
    yield f"data: {json.dumps({'thinking': {'category': 'planning', 'content': 'Planning the narrative arc and moral lesson...', 'timestamp': 'now'}})}\n\n"
    await asyncio.sleep(0.5)
    yield f"data: {json.dumps({'thinking': {'category': 'processing', 'content': 'Weaving the tale together...', 'timestamp': 'now'}})}\n\n"
    
    try:
        # Step 2: Build the prompt from user inputs
        prompt = build_story_prompt(request)
        
        # Step 3: Stream the story content from the AI
        # The AI generates text chunk by chunk, and we forward each chunk immediately
        story_content = ""
        try:
            async for chunk in llm_provider.generate_stream(
                prompt,
                temperature=0.8,  # Controls creativity (0.0 = deterministic, 1.0+ = creative)
                max_tokens=800    # Limits story length
            ):
                # Fix spacing issues in streaming chunks (e.g., "night,5-year-old" -> "night, 5-year-old")
                chunk = _fix_streaming_chunk_spacing(chunk)
                story_content += chunk
                # Send each chunk to frontend as it arrives
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        except (RuntimeError, StopIteration) as e:
            # StopIteration and some RuntimeErrors indicate normal completion
            # (some async frameworks convert StopIteration to RuntimeError)
            error_str = str(e).lower()
            if "stopiteration" in error_str or "async generator" in error_str:
                # Generator finished normally - this is expected, not an error
                pass
            else:
                # Other RuntimeError - re-raise as it's a real error
                raise
        
        # Step 4: Signal that generation is complete
        yield f"data: {json.dumps({'done': True, 'status': 'completed'})}\n\n"
        
    except Exception as e:
        # Handle errors gracefully
        error_message = f"Error generating story: {str(e)}"
        yield f"data: {json.dumps({'error': error_message, 'status': 'error'})}\n\n"
