# llm/final_article.py

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

async def generate_final_article(
    edited_draft: str,
    final_edits: Dict[str, Any],
    llm_client: Any,
    prompt_handler: Any,
    user_email: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Generate final version of article incorporating all edits and feedback
    
    Args:
        edited_draft (str): The edited article draft
        final_edits (Dict[str, Any]): Dictionary containing final editing instructions
        llm_client (Any): LLM client instance for generating responses
        prompt_handler (Any): Handler for managing prompts
        user_email (str): Email of the user making the request
        metadata (Optional[Dict[str, Any]]): Additional metadata for article tracking
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary containing final article content or error information
    """
    try:
        logger.info("Generating final article version...")
        
        # Format final article prompt
        final_prompt = await prompt_handler.format_prompt(
            'final_article',
            {
                'edited_draft': edited_draft,
                'final_edits': final_edits,
                'metadata': metadata or {}
            }
        )
        
        if not final_prompt:
            raise ValueError("Failed to format final article prompt")
            
        # Generate final version using LLM
        final_content = await llm_client.generate_response(
            system_prompt=(
                "You are an AI assistant for Fair Fight, tasked with generating final "
                "versions of blog articles. Your role is to incorporate all approved edits "
                "while maintaining consistency in tone, style, and message. Ensure the "
                "final content is polished, professional, and ready for publication while "
                "staying true to Fair Fight's mission of empowering employees and promoting "
                "workplace fairness."
            ),
            user_prompt=final_prompt,
            max_tokens=2000,
            user_email=user_email
        )
        
        logger.info("Final article generation complete.")
        
        # Prepare article metadata
        article_metadata = {
            'version': '1.0',
            'status': 'final',
            'last_edited': metadata.get('timestamp') if metadata else None,
            'word_count': len(final_content.split()),
            'editor_email': user_email
        }
        
        return {
            'success': True,
            'article': final_content,
            'metadata': article_metadata,
            'edits_applied': list(final_edits.keys())  # Track which edits were applied
        }
        
    except Exception as e:
        logger.error(f"Error generating final article: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }