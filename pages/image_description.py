# pages/image_description.py
import streamlit as st
import asyncio
from typing import Dict, Any
from llm.llm_client import AsyncLLMClient
from utils.prompt_handler import AsyncPromptHandler
import logging

logger = logging.getLogger(__name__)

async def generate_image_description(
    article: str,
    llm_client: AsyncLLMClient,
    prompt_handler: AsyncPromptHandler,
    user_email: str
) -> Dict[str, Any]:
    """Generate image description asynchronously"""
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

async def image_description_page(
    db_handlers: Dict[str, Any],
    llm_client: AsyncLLMClient,
    prompt_handler: AsyncPromptHandler
):
    st.title("Generate Fairness Factor Blog Image Description")
    
    user_email = st.session_state.user['email']
    
    if 'final_article' not in st.session_state:
        st.warning("Please generate the final article first.")
        return
    
    st.write("Final Article:")
    st.write(st.session_state['final_article'])
    
    if st.button("Generate Image Description"):
        with st.spinner("Generating image description..."):
            try:
                result = await generate_image_description(
                    article=st.session_state['final_article'],
                    llm_client=llm_client,
                    prompt_handler=prompt_handler,
                    user_email=user_email
                )
                
                if result['success']:
                    # Save image description
                    content_id = await db_handlers['blog'].save_content(
                        user_email=user_email,
                        content_type='image_description',
                        content=result['description'],
                        metadata={'final_id': st.session_state['final_id']}
                    )
                    
                    # Update session state
                    st.session_state['image_description'] = result['description']
                    st.session_state['image_id'] = content_id
                    
                    # Log activity
                    await db_handlers['analytics'].log_activity(
                        user_email=user_email,
                        activity_type='image_description',
                        metadata={'content_id': content_id}
                    )
                    
                    st.write("Generated Image Description:")
                    st.write(result['description'])
                    
                    # Allow editing
                    edited_description = st.text_area(
                        "Edit the image description if needed:",
                        result['description']
                    )
                    
                    if edited_description != result['description']:
                        if st.button("Save Edited Description"):
                            try:
                                await db_handlers['blog'].update_content(
                                    content_id,
                                    {'content': edited_description}
                                )
                                st.session_state['image_description'] = edited_description
                                st.success("Updated image description saved")
                            except Exception as e:
                                st.error(f"Error saving edited description: {str(e)}")
                                
                else:
                    st.error(f"Failed to generate image description: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                logger.error(f"Error in image description generation: {str(e)}")