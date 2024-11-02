import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

async def generate_final_article(
    draft: str,
    suggestions: str,
    feedback: str,
    llm_client: Any,
    prompt_handler: Any,
    user_email: str
) -> Optional[Dict[str, Any]]:
    """Generate final article incorporating editing suggestions and feedback"""
    try:
        final_prompt = await prompt_handler.format_prompt(
            'final_article',
            {
                'article_draft': draft,
                'editing_suggestions': suggestions,
                'user_feedback': feedback
            }
        )
        
        if not final_prompt:
            raise ValueError("Failed to format final article prompt")

        final_content = await llm_client.generate_response(
            system_prompt="You are an AI editor finalizing Fairness Factor blog articles...",
            user_prompt=final_prompt,
            max_tokens=2000,
            user_email=user_email
        )
        
        return {
            'success': True,
            'article': final_content
        }
    except Exception as e:
        logger.error(f"Error generating final article: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }