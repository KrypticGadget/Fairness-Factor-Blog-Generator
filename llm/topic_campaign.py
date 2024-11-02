# llm/topic_campaign.py
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

async def generate_topic_campaign(
    research_analysis: str,
    llm_client: Any,
    prompt_handler: Any,
    user_email: str
) -> Optional[Dict[str, Any]]:
    """Generate topic campaign based on research analysis"""
    try:
        # Format campaign prompt
        campaign_prompt = await prompt_handler.format_prompt(
            'topic_campaign',
            {'research_analysis': research_analysis}
        )
        
        if not campaign_prompt:
            raise ValueError("Failed to format campaign prompt")

        # Generate campaign content
        campaign_content = await llm_client.generate_response(
            system_prompt="You are an AI strategist creating content campaigns for Fairness Factor...",
            user_prompt=campaign_prompt,
            max_tokens=1000,
            user_email=user_email
        )
        
        return {
            'success': True,
            'campaign': campaign_content
        }
    except Exception as e:
        logger.error(f"Error generating topic campaign: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }