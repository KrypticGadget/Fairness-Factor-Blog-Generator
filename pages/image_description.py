# pages/image_description.py
import streamlit as st
import asyncio
from typing import Dict, Any, Optional, List
from llm.llm_client import AsyncLLMClient
from utils.prompt_handler import AsyncPromptHandler
from datetime import datetime
import logging
import json
from PIL import Image
import io

logger = logging.getLogger(__name__)

class ImageDescriptionGenerator:
    """Handles image description generation and validation"""
    
    IMAGE_TYPES = {
        "hero": {
            "name": "Hero Image",
            "description": "Main header image for the article",
            "dimensions": "1200x630px",
            "style": "Professional and impactful"
        },
        "section": {
            "name": "Section Break",
            "description": "Visual break between article sections",
            "dimensions": "800x400px",
            "style": "Subtle and thematic"
        },
        "infographic": {
            "name": "Infographic",
            "description": "Visual representation of data or processes",
            "dimensions": "800x1200px",
            "style": "Clear and informative"
        },
        "testimonial": {
            "name": "Testimonial",
            "description": "Supporting image for quotes or case studies",
            "dimensions": "400x400px",
            "style": "Personal and authentic"
        },
        "icon": {
            "name": "Icon",
            "description": "Small symbolic representation",
            "dimensions": "100x100px",
            "style": "Simple and recognizable"
        }
    }
    
    STYLE_GUIDELINES = {
        "professional": "Corporate and professional style",
        "modern": "Modern and dynamic approach",
        "inclusive": "Diverse and inclusive representation",
        "empowering": "Empowering and positive imagery",
        "authentic": "Genuine and relatable visuals"
    }
    
    COLOR_SCHEMES = {
        "brand": {
            "primary": "#0077BD",
            "secondary": "#003A6E",
            "accent": "#FC510B",
            "neutral": "#F5F5F5"
        },
        "complementary": {
            "warm": ["#FF7500", "#FFB800", "#FFE5B4"],
            "cool": ["#0075E0", "#00A3E0", "#CEF3FF"]
        }
    }
    
    @staticmethod
    def validate_description(description: str) -> Dict[str, Any]:
        """Validate image description"""
        min_length = 100
        max_length = 500
        current_length = len(description)
        
        return {
            'valid': min_length <= current_length <= max_length,
            'length': current_length,
            'message': f"Description length: {current_length} characters (should be between {min_length} and {max_length})"
        }

async def generate_image_description(
    article: str,
    image_type: str,
    style: str,
    color_scheme: List[str],
    additional_notes: str,
    llm_client: AsyncLLMClient,
    prompt_handler: AsyncPromptHandler,
    user_email: str
) -> Dict[str, Any]:
    """Generate image description based on article content and preferences"""
    try:
        # Check user authentication
        if not user_email:
            raise ValueError("User not authenticated")

        # Format image prompt
        image_prompt = await prompt_handler.format_prompt(
            'image_description',
            {
                'article_content': article,
                'image_type': ImageDescriptionGenerator.IMAGE_TYPES[image_type]['description'],
                'style_preference': ImageDescriptionGenerator.STYLE_GUIDELINES[style],
                'color_scheme': ', '.join(color_scheme),
                'additional_notes': additional_notes
            }
        )
        
        if not image_prompt:
            raise ValueError("Failed to format image description prompt")

        # Generate description
        description = await llm_client.generate_response(
            system_prompt=(
                "You are an expert visual designer creating image descriptions for "
                "Fairness Factor blog articles. Focus on professional, inclusive, "
                "and empowering imagery that reinforces the message of employee advocacy. "
                f"Create a detailed description for a {ImageDescriptionGenerator.IMAGE_TYPES[image_type]['name']}."
            ),
            user_prompt=image_prompt,
            max_tokens=1000,
            user_email=user_email
        )
        
        # Validate description
        validation = ImageDescriptionGenerator.validate_description(description)
        if not validation['valid']:
            raise ValueError(f"Generated description does not meet requirements: {validation['message']}")
        
        return {
            'success': True,
            'description': description,
            'validation': validation
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
    """Image Description Page Handler"""
    try:
        # Check user authentication
        if 'user' not in st.session_state or not st.session_state.user:
            st.warning("Please log in to access this page.")
            return

        user_email = st.session_state.user['email']
        
        st.title("Generate Fairness Factor Blog Image Descriptions")
        
        # Check prerequisites
        if 'final_article' not in st.session_state:
            st.warning("⚠️ Please generate the final article first.")
            return
        
        # Display article
        with st.expander("📄 Final Article", expanded=False):
            st.write(st.session_state['final_article'])
        
        # Image description settings
        st.write("### 🎨 Image Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            image_type = st.selectbox(
                "Image Type:",
                list(ImageDescriptionGenerator.IMAGE_TYPES.keys()),
                format_func=lambda x: ImageDescriptionGenerator.IMAGE_TYPES[x]['name'],
                help="Select the type of image needed"
            )
            
            # Display selected image type details
            st.info(
                f"**Dimensions:** {ImageDescriptionGenerator.IMAGE_TYPES[image_type]['dimensions']}\n\n"
                f"**Style:** {ImageDescriptionGenerator.IMAGE_TYPES[image_type]['style']}"
            )
            
            style_preference = st.selectbox(
                "Style Preference:",
                list(ImageDescriptionGenerator.STYLE_GUIDELINES.keys()),
                format_func=lambda x: ImageDescriptionGenerator.STYLE_GUIDELINES[x],
                help="Select the preferred style"
            )
        
        with col2:
            # Color scheme selection
            st.write("#### Color Scheme")
            
            use_brand_colors = st.checkbox(
                "Use Brand Colors",
                value=True,
                help="Include Fairness Factor brand colors"
            )
            
            if use_brand_colors:
                selected_colors = list(ImageDescriptionGenerator.COLOR_SCHEMES['brand'].keys())
            else:
                selected_colors = st.multiselect(
                    "Select Colors:",
                    list(ImageDescriptionGenerator.COLOR_SCHEMES['complementary'].keys()),
                    default=["warm"],
                    help="Select color preferences"
                )
            
            # Display color preview
            st.write("Selected Colors:")
            colors_html = ""
            if use_brand_colors:
                for color_name, color_code in ImageDescriptionGenerator.COLOR_SCHEMES['brand'].items():
                    colors_html += f'<div style="background-color: {color_code}; width: 50px; height: 20px; display: inline-block; margin-right: 5px;"></div>'
            else:
                for scheme in selected_colors:
                    for color in ImageDescriptionGenerator.COLOR_SCHEMES['complementary'][scheme]:
                        colors_html += f'<div style="background-color: {color}; width: 50px; height: 20px; display: inline-block; margin-right: 5px;"></div>'
            
            st.markdown(colors_html, unsafe_allow_html=True)
        
        # Image composition
        st.write("### 📐 Image Composition")
        
        composition_options = {
            "layout": st.selectbox(
                "Layout:",
                ["Centered", "Rule of Thirds", "Golden Ratio", "Symmetrical"],
                help="Select image composition layout"
            ),
            "focus": st.selectbox(
                "Focus Point:",
                ["Center", "Left Third", "Right Third", "Golden Point"],
                help="Select main focus point"
            ),
            "depth": st.selectbox(
                "Depth:",
                ["Flat", "Shallow", "Medium", "Deep"],
                help="Select depth of field"
            )
        }
        
        # Additional notes
        additional_notes = st.text_area(
            "Additional Notes:",
            help="Any specific requirements or preferences for the image"
        )
        
        # Generate description
        if st.button("🎨 Generate Image Description", help="Click to generate image description"):
            with st.spinner("✍️ Generating image description..."):
                try:
                    result = await generate_image_description(
                        article=st.session_state['final_article'],
                        image_type=image_type,
                        style=style_preference,
                        color_scheme=selected_colors,
                        additional_notes=additional_notes,
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
                            metadata={
                                'final_id': st.session_state['final_id'],
                                'image_type': image_type,
                                'style': style_preference,
                                'color_scheme': selected_colors,
                                'composition': composition_options,
                                'additional_notes': additional_notes
                            }
                        )
                        
                        # Update session state
                        st.session_state['image_description'] = result['description']
                        st.session_state['image_id'] = content_id
                        
                        # Log activity
                        await db_handlers['analytics'].log_activity(
                            user_email=user_email,
                            activity_type='image_description',
                            metadata={
                                'content_id': content_id,
                                'image_type': image_type
                            }
                        )
                        
                        # Display success and validation
                        st.success("✅ Image description generated successfully!")
                        st.info(result['validation']['message'])
                        
                        # Description display
                        st.write("### 📝 Generated Description")
                        
                        # Display description with editing option
                        edited_description = st.text_area(
                            "Edit Description:",
                            value=result['description'],
                            height=300,
                            key="edit_description"
                        )
                        
                        if edited_description != result['description']:
                            if st.button("💾 Save Edited Description"):
                                validation = ImageDescriptionGenerator.validate_description(edited_description)
                                if validation['valid']:
                                    await db_handlers['blog'].update_content(
                                        content_id,
                                        {'content': edited_description}
                                    )
                                    st.session_state['image_description'] = edited_description
                                    st.success("✅ Description updated successfully!")
                                else:
                                    st.error(validation['message'])
                        
                        # Technical specifications
                        st.write("### 📋 Technical Specifications")
                        
                        specs = {
                            "Type": ImageDescriptionGenerator.IMAGE_TYPES[image_type]['name'],
                            "Dimensions": ImageDescriptionGenerator.IMAGE_TYPES[image_type]['dimensions'],
                            "Style": ImageDescriptionGenerator.STYLE_GUIDELINES[style_preference],
                            "Color Scheme": ", ".join(selected_colors),
                            "Layout": composition_options['layout'],
                            "Focus Point": composition_options['focus'],
                            "Depth": composition_options['depth']
                        }
                        
                        for key, value in specs.items():
                            st.write(f"**{key}:** {value}")
                        
                        # Export options
                        if st.button("📤 Export Image Package"):
                            export_data = {
                                'description': edited_description or result['description'],
                                'specifications': specs,
                                'metadata': {
                                    'generated_at': datetime.now().isoformat(),
                                    'article_id': st.session_state['final_id'],
                                    'composition': composition_options,
                                    'additional_notes': additional_notes
                                }
                            }
                            
                            st.download_button(
                                label="📥 Download Image Package",
                                data=json.dumps(export_data, indent=2),
                                file_name=f"image_specs_{content_id}.json",
                                mime="application/json"
                            )
                        
                    else:
                        st.error(f"❌ Failed to generate description: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")
                    logger.error(f"Error in image description generation: {str(e)}")
        
        # Description history
        with st.expander("📚 Description History", expanded=False):
            try:
                description_history = await db_handlers['blog'].get_user_content(
                    user_email=user_email,
                    content_type='image_description',
                    limit=5
                )
                
                if description_history:
                    for entry in description_history:
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.write(f"Description from {entry['created_at'].strftime('%Y-%m-%d %H:%M')}")
                            st.write(f"Type: {entry['metadata'].get('image_type', 'Unknown')}")
                            
                        with col2:
                            if st.button("Load", key=f"load_{entry['_id']}"):
                                st.session_state['image_description'] = entry['content']
                                st.session_state['image_id'] = str(entry['_id'])
                                st.experimental_rerun()
                                
                        with col3:
                            if st.button("Delete", key=f"delete_{entry['_id']}"):
                                try:
                                    await db_handlers['blog'].delete_content(str(entry['_id']))
                                    st.success("✅ Description deleted successfully!")
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error(f"❌ Error deleting description: {str(e)}")
                        
                        st.markdown("---")
                else:
                    st.info("No previous descriptions found.")
                    
            except Exception as e:
                st.error("Failed to load description history")
                logger.error(f"Error loading description history: {str(e)}")

        # Help section
        with st.expander("❓ Need Help?", expanded=False):
            st.markdown("""
            ### Image Guidelines
            1. Focus on professional quality
            2. Maintain brand consistency
            3. Ensure inclusive representation
            4. Consider image context
            5. Follow technical specifications
            
            ### Best Practices
            - Use high-quality images
            - Consider composition rules
            - Match article tone
            - Include diverse representation
            - Follow brand guidelines
            
            ### Support
            Contact: design@fairnessfactor.com
            """)

    except Exception as e:
        logger.error(f"Error in image description page: {str(e)}")
        st.error("An unexpected error occurred. Please try again.")

if __name__ == "__main__":
    # For testing the page individually
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    async def test_page():
        from utils.mongo_manager import AsyncMongoManager
        from utils.prompt_handler import AsyncPromptHandler
        from llm.llm_client import AsyncLLMClient
        
        mongo_manager = AsyncMongoManager()
        client, db = await mongo_manager.get_connection()
        
        handlers = {
            'blog': None,  # Add your handlers here
            'file': None,
            'analytics': None
        }
        
        await image_description_page(
            handlers,
            AsyncLLMClient(),
            AsyncPromptHandler(db)
        )
    
    asyncio.run(test_page())