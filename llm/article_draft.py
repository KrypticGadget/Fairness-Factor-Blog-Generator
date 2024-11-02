import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

async def generate_article_draft(
    topic: str,
    structure: str,
    llm_client: Any,
    prompt_handler: Any,
    user_email: str
) -> Optional[Dict[str, Any]]:
    """Generate article draft based on selected topic and structure"""
    try:
        draft_prompt = await prompt_handler.format_prompt(
            'article_draft',
            {
                'selected_topic': topic,
                'article_structure': structure
            }
        )
        
        if not draft_prompt:
            raise ValueError("Failed to format draft prompt")

        draft_content = await llm_client.generate_response(
            system_prompt="You are an AI writer creating blog articles for Fairness Factor...",
            user_prompt=draft_prompt,
            max_tokens=2000,
            user_email=user_email
        )
        
        return {
            'success': True,
            'draft': draft_content
        }
    except Exception as e:
        logger.error(f"Error generating article draft: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }