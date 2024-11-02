import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

async def generate_image_description(
    article: str,
    llm_client: Any,
    prompt_handler: Any,
    user_email: str
) -> Optional[Dict[str, Any]]:
    """Generate image description based on article content"""
    try:
        image_prompt = await prompt_handler.format_prompt(
            'image_description',
            {'final_article': article}
        )
        
        if not image_prompt:
            raise ValueError("Failed to format image description prompt")

        description = await llm_client.generate_response(
            system_prompt="You are an AI designer creating image descriptions for Fairness Factor blog articles...",
            user_prompt=image_prompt,
            max_tokens=500,
            user_email=user_email
        )
        
        return {
            'success': True,
            'description': description
        }
    except Exception as e:
        logger.error(f"Error generating image description: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }