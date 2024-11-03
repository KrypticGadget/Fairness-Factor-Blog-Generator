# llm/image_description.py

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

async def generate_image_description(
    final_article: str,
    topic_data: Optional[Dict[str, Any]] = None,
    llm_client: Any = None,
    prompt_handler: Any = None,
    user_email: str = None,
    image_requirements: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Generate detailed image descriptions for blog articles
    
    Args:
        final_article (str): The final article content
        topic_data (Optional[Dict[str, Any]]): Additional topic-specific data
        llm_client (Any): LLM client instance for generating responses
        prompt_handler (Any): Handler for managing prompts
        user_email (str): Email of the user making the request
        image_requirements (Optional[Dict[str, Any]]): Specific requirements for image generation
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary containing image descriptions or error information
    """
    try:
        logger.info("Generating image descriptions...")
        
        # Prepare image requirements
        default_requirements = {
            'style': 'professional and inclusive',
            'format': 'digital illustration',
            'tone': 'positive and empowering',
            'color_scheme': 'Fair Fight brand colors',
            'dimensions': {'width': 1200, 'height': 630}  # Default social media size
        }
        
        final_requirements = {
            **default_requirements,
            **(image_requirements or {})
        }
        
        # Format image description prompt
        image_prompt = await prompt_handler.format_prompt(
            'image_description',
            {
                'final_article': final_article,
                'topic_data': topic_data or {},
                'image_requirements': final_requirements
            }
        )
        
        if not image_prompt:
            raise ValueError("Failed to format image description prompt")
            
        # Generate image description using LLM
        description_content = await llm_client.generate_response(
            system_prompt=(
                "You are an AI assistant for Fair Fight, tasked with generating detailed "
                "image descriptions for blog articles. Your role is to create descriptions "
                "that are inclusive, professional, and align with Fair Fight's mission of "
                "promoting workplace fairness. Focus on creating visuals that are both "
                "engaging and appropriate for professional workplace content. Consider "
                "accessibility and ensure descriptions can be effectively used by image "
                "generation tools or human designers."
            ),
            user_prompt=image_prompt,
            max_tokens=500,
            user_email=user_email
        )
        
        logger.info("Image description generation complete.")
        
        # Parse and structure the description
        description_metadata = {
            'dimensions': final_requirements['dimensions'],
            'style_guidelines': final_requirements['style'],
            'format': final_requirements['format'],
            'purpose': 'blog article illustration',
            'accessibility_notes': 'Designed with alt text compatibility in mind'
        }
        
        return {
            'success': True,
            'description': description_content,
            'metadata': description_metadata,
            'requirements_applied': list(final_requirements.keys())
        }
        
    except Exception as e:
        logger.error(f"Error generating image description: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'error_details': {
                'stage': 'image_description_generation',
                'input_length': len(final_article),
                'requirements_provided': bool(image_requirements)
            }
        }