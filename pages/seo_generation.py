# pages/seo_generation.py
import streamlit as st
import asyncio
from typing import Dict, Any
from llm.llm_client import AsyncLLMClient
from utils.prompt_handler import AsyncPromptHandler
import logging

logger = logging.getLogger(__name__)

async def generate_seo_content(
    article: str,
    image_description: str,
    llm_client: AsyncLLMClient,
    prompt_handler: AsyncPromptHandler,
    user_email: str
) -> Dict[str, Any]:
    """Generate SEO content asynchronously"""
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

async def seo_generation_page(
    db_handlers: Dict[str, Any],
    llm_client: AsyncLLMClient,
    prompt_handler: AsyncPromptHandler
):
    st.title("Generate SEO Content for Fairness Factor Blog")
    
    user_email = st.session_state.user['email']
    
    if 'final_article' not in st.session_state or 'image_description' not in st.session_state:
        st.warning("Please complete the Final Article and Image Description steps first.")
        return
    
    st.write("Final Article:")
    st.write(st.session_state['final_article'])
    
    st.write("Image Description:")
    st.write(st.session_state['image_description'])
    
    if st.button("Generate SEO Content"):
        with st.spinner("Generating SEO content..."):
            try:
                result = await generate_seo_content(
                    article=st.session_state['final_article'],
                    image_description=st.session_state['image_description'],
                    llm_client=llm_client,
                    prompt_handler=prompt_handler,
                    user_email=user_email
                )
                
                if result['success']:
                    # Parse SEO content
                    seo_content = result['seo_content']
                    
                    # Save SEO content
                    content_id = await db_handlers['blog'].save_content(
                        user_email=user_email,
                        content_type='seo_content',
                        content=seo_content,
                        metadata={
                            'final_id': st.session_state['final_id'],
                            'image_id': st.session_state['image_id']
                        }
                    )
                    
                    # Update session state
                    st.session_state['seo_content'] = seo_content
                    st.session_state['seo_id'] = content_id
                    
                    # Log activity
                    await db_handlers['analytics'].log_activity(
                        user_email=user_email,
                        activity_type='seo_generation',
                        metadata={'content_id': content_id}
                    )
                    
                    # Display SEO content in organized sections
                    st.subheader("Generated SEO Content:")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("Meta Title:")
                        meta_title = st.text_input(
                            "Edit meta title:",
                            value=extract_meta_title(seo_content)
                        )
                        
                        st.write("Meta Description:")
                        meta_desc = st.text_area(
                            "Edit meta description:",
                            value=extract_meta_description(seo_content)
                        )
                        
                        st.write("Focus Keyword:")
                        focus_keyword = st.text_input(
                            "Edit focus keyword:",
                            value=extract_focus_keyword(seo_content)
                        )
                    
                    with col2:
                        st.write("Secondary Keywords:")
                        secondary_keywords = st.text_area(
                            "Edit secondary keywords:",
                            value=extract_secondary_keywords(seo_content)
                        )
                        
                        st.write("URL Slug:")
                        url_slug = st.text_input(
                            "Edit URL slug:",
                            value=extract_url_slug(seo_content)
                        )
                    
                    # Save button for edited content
                    if st.button("Save SEO Content"):
                        try:
                            updated_content = format_seo_content(
                                meta_title=meta_title,
                                meta_desc=meta_desc,
                                focus_keyword=focus_keyword,
                                secondary_keywords=secondary_keywords,
                                url_slug=url_slug
                            )
                            
                            await db_handlers['blog'].update_content(
                                content_id,
                                {'content': updated_content}
                            )
                            
                            st.success("Updated SEO content saved")
                            
                        except Exception as e:
                            st.error(f"Error saving SEO content: {str(e)}")
                    
                else:
                    st.error(f"Failed to generate SEO content: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                logger.error(f"Error in SEO content generation: {str(e)}")

# Helper functions for SEO content parsing
def extract_meta_title(seo_content: str) -> str:
    # Implementation for extracting meta title
    pass

def extract_meta_description(seo_content: str) -> str:
    # Implementation for extracting meta description
    pass

def extract_focus_keyword(seo_content: str) -> str:
    # Implementation for extracting focus keyword
    pass

def extract_secondary_keywords(seo_content: str) -> str:
    # Implementation for extracting secondary keywords
    pass

def extract_url_slug(seo_content: str) -> str:
    # Implementation for extracting URL slug
    pass

def format_seo_content(**kwargs) -> str:
    # Implementation for formatting SEO content
    pass