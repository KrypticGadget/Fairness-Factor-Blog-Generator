# llm/seo_generation.py

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

async def generate_seo_content(
    final_article: str,
    image_description: str,
    llm_client: Any,
    prompt_handler: Any,
    user_email: str,
    seo_params: Optional[Dict[str, Any]] = None,
    topic_data: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Generate SEO content for the article including meta descriptions, tags, and optimizations
    
    Args:
        final_article (str): The final article content
        image_description (str): Description of the article's main image
        llm_client (Any): LLM client instance for generating responses
        prompt_handler (Any): Handler for managing prompts
        user_email (str): Email of the user making the request
        seo_params (Optional[Dict[str, Any]]): Additional SEO parameters and requirements
        topic_data (Optional[Dict[str, Any]]): Additional topic-specific data for context
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary containing SEO content or error information
    """
    try:
        logger.info("Generating SEO content...")
        
        # Set default SEO parameters
        default_params = {
            'target_keywords': 3,  # Number of primary keywords to target
            'meta_description_length': 155,  # Optimal meta description length
            'title_tag_length': 60,  # Optimal title tag length
            'platforms': ['google', 'linkedin', 'twitter'],
            'content_type': 'blog',
            'seo_goals': [
                'organic_traffic',
                'social_sharing',
                'engagement'
            ]
        }
        
        # Merge with provided parameters
        final_params = {
            **default_params,
            **(seo_params or {})
        }
        
        # Format SEO prompt
        seo_prompt = await prompt_handler.format_prompt(
            'seo_generation',
            {
                'final_article': final_article,
                'image_description': image_description,
                'seo_parameters': final_params,
                'topic_data': topic_data or {}
            }
        )
        
        if not seo_prompt:
            raise ValueError("Failed to format SEO prompt")
            
        # Generate SEO content using LLM
        seo_content = await llm_client.generate_response(
            system_prompt=(
                "You are an SEO expert for Fair Fight, optimizing content for maximum visibility "
                "while maintaining authenticity and value. Focus on creating SEO elements that "
                "enhance discoverability of workplace rights and employee empowerment content. "
                "Ensure all optimizations align with current SEO best practices while preserving "
                "the content's professional tone and educational value."
            ),
            user_prompt=seo_prompt,
            max_tokens=1000,
            user_email=user_email
        )
        
        logger.info("SEO content generation complete.")
        
        # Extract and structure SEO elements
        seo_elements = {
            'meta': {
                'title': '',  # To be extracted from response
                'description': '',  # To be extracted from response
                'keywords': [],  # To be extracted from response
                'robots': 'index, follow'
            },
            'social_meta': {
                platform: {} for platform in final_params['platforms']
            },
            'schema_org': {
                '@context': 'https://schema.org',
                '@type': 'Article',
                'headline': '',  # To be extracted from response
                'datePublished': datetime.now().isoformat(),
                'author': {
                    '@type': 'Organization',
                    'name': 'Fair Fight'
                }
            }
        }
        
        # Parse LLM response and populate SEO elements
        try:
            # Basic parsing of the response - in practice, you'd want more robust parsing
            lines = seo_content.split('\n')
            for line in lines:
                if line.startswith('Title:'): 
                    seo_elements['meta']['title'] = line.replace('Title:', '').strip()
                elif line.startswith('Description:'): 
                    seo_elements['meta']['description'] = line.replace('Description:', '').strip()
                elif line.startswith('Keywords:'): 
                    seo_elements['meta']['keywords'] = [
                        k.strip() for k in line.replace('Keywords:', '').strip().split(',')
                    ]
        except Exception as parse_error:
            logger.warning(f"Error parsing SEO elements: {str(parse_error)}")
        
        return {
            'success': True,
            'seo_content': seo_content,
            'structured_elements': seo_elements,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'parameters_used': final_params,
                'content_length': len(final_article),
                'platforms_optimized': final_params['platforms']
            },
            'validation': {
                'title_length_ok': len(seo_elements['meta']['title']) <= final_params['title_tag_length'],
                'description_length_ok': len(seo_elements['meta']['description']) <= final_params['meta_description_length'],
                'keywords_count_ok': len(seo_elements['meta']['keywords']) >= final_params['target_keywords']
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating SEO content: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'error_context': {
                'stage': 'seo_generation',
                'article_length': len(final_article),
                'params_provided': bool(seo_params),
                'timestamp': datetime.now().isoformat()
            }
        }