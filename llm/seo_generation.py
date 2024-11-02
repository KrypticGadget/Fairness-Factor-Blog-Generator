import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

async def generate_seo_content(
    article: str,
    image_description: str,
    llm_client: Any,
    prompt_handler: Any,
    user_email: str
) -> Optional[Dict[str, Any]]:
    """Generate SEO content for the article"""
    try:
        seo_prompt = await prompt_handler.format_prompt(
            'seo_generation',
            {
                'final_article': article,
                'image_description': image_description
            }
        )
        
        if not seo_prompt:
            raise ValueError("Failed to format SEO prompt")

        seo_content = await llm_client.generate_response(
            system_prompt="You are an SEO expert optimizing Fairness Factor blog content...",
            user_prompt=seo_prompt,
            max_tokens=1000,
            user_email=user_email
        )
        
        return {
            'success': True,
            'seo_content': seo_content
        }
    except Exception as e:
        logger.error(f"Error generating SEO content: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }