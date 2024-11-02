# pages/seo_generation.py
import streamlit as st
import asyncio
from typing import Dict, Any, Optional, List
from llm.llm_client import AsyncLLMClient
from utils.prompt_handler import AsyncPromptHandler
import logging
import json
import re
from datetime import datetime

logger = logging.getLogger(__name__)

def check_page_access(page_name: str) -> bool:
    """Check if user has access to requested page"""
    if not st.session_state.authenticated:
        return False
        
    required_pages = {
        'Topic Research': ['user', 'admin'],
        'Topic Campaign': ['user', 'admin'],
        'Article Draft': ['user', 'admin'],
        'Editing Criteria': ['user', 'admin'],
        'Final Article': ['user', 'admin'],
        'Image Description': ['user', 'admin'],
        'SEO Generation': ['user', 'admin']
    }
    
    user_role = st.session_state.user.get('role', 'user')
    return user_role in required_pages.get(page_name, [])

logger = logging.getLogger(__name__)

class SEOGenerator:
    """Handles SEO content generation and validation"""
    
    META_REQUIREMENTS = {
        "title": {
            "min_length": 30,
            "max_length": 60,
            "required_elements": ["brand", "keyword"]
        },
        "description": {
            "min_length": 120,
            "max_length": 160,
            "required_elements": ["value proposition", "call to action"]
        }
    }
    
    SCHEMA_TYPES = {
        "article": {
            "name": "Article Schema",
            "required_fields": ["headline", "author", "datePublished", "publisher"]
        },
        "organization": {
            "name": "Organization Schema",
            "required_fields": ["name", "url", "logo", "contactPoint"]
        },
        "faq": {
            "name": "FAQ Schema",
            "required_fields": ["questions", "answers"]
        }
    }
    
    KEYWORD_TYPES = {
        "primary": "Main focus keyword",
        "secondary": "Supporting keywords",
        "long_tail": "Long-tail variations",
        "related": "Related terms",
        "lsi": "Latent Semantic Indexing keywords"
    }
    
    @staticmethod
    def validate_meta_title(title: str) -> Dict[str, Any]:
        """Validate meta title"""
        length = len(title)
        return {
            'valid': 30 <= length <= 60,
            'length': length,
            'message': f"Title length: {length}/60 characters"
        }
    
    @staticmethod
    def validate_meta_description(description: str) -> Dict[str, Any]:
        """Validate meta description"""
        length = len(description)
        return {
            'valid': 120 <= length <= 160,
            'length': length,
            'message': f"Description length: {length}/160 characters"
        }
    
    @staticmethod
    def generate_slug(title: str) -> str:
        """Generate URL slug from title"""
        slug = title.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug

async def generate_seo_content(
    article: str,
    image_description: str,
    target_keywords: List[str],
    schema_types: List[str],
    llm_client: AsyncLLMClient,
    prompt_handler: AsyncPromptHandler,
    user_email: str
) -> Dict[str, Any]:
    """Generate SEO content based on article and keywords"""
    try:
        # Check user authentication
        if not user_email:
            raise ValueError("User not authenticated")

        # Format SEO prompt
        seo_prompt = await prompt_handler.format_prompt(
            'seo_generation',
            {
                'article_content': article,
                'image_description': image_description,
                'target_keywords': ', '.join(target_keywords),
                'schema_types': ', '.join(schema_types)
            }
        )
        
        if not seo_prompt:
            raise ValueError("Failed to format SEO prompt")

        # Generate SEO content
        seo_content = await llm_client.generate_response(
            system_prompt=(
                "You are an SEO expert optimizing content for Fairness Factor's blog. "
                "Focus on employee advocacy keywords while maintaining natural language "
                "and providing comprehensive meta information for optimal search visibility. "
                "Generate schema markup for specified types and ensure all meta elements "
                "follow best practices."
            ),
            user_prompt=seo_prompt,
            max_tokens=2000,
            user_email=user_email
        )
        
        # Parse SEO content into structured format
        try:
            seo_data = json.loads(seo_content)
        except json.JSONDecodeError:
            raise ValueError("Generated SEO content is not in valid JSON format")
        
        # Validate meta elements
        title_validation = SEOGenerator.validate_meta_title(seo_data.get('meta_title', ''))
        desc_validation = SEOGenerator.validate_meta_description(seo_data.get('meta_description', ''))
        
        if not title_validation['valid'] or not desc_validation['valid']:
            raise ValueError("Generated meta elements do not meet requirements")
        
        return {
            'success': True,
            'seo_data': seo_data,
            'validations': {
                'title': title_validation,
                'description': desc_validation
            }
        }
    except Exception as e:
        logger.error(f"Error generating SEO content: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

async def seo_generation_page(db_handlers, llm_client, prompt_handler):
    """SEO Generation Page Handler"""
    try:
        # Check authentication and access
        if not st.session_state.authenticated:
            st.warning("Please log in to access this page")
            st.stop()
            return
            
        if not check_page_access('SEO Generation'):
            st.error("You don't have permission to access this page")
            st.stop()
            return

        user_email = st.session_state.user['email']
        
        # Check prerequisites
        if 'final_article' not in st.session_state or 'image_description' not in st.session_state:
            st.warning("⚠️ Please complete the Final Article and Image Description steps first")
            st.stop()
            return

        # Log page access
        await db_handlers['analytics'].log_activity(
            user_email=user_email,
            activity_type='page_access',
            metadata={'page': 'SEO Generation'}
        )

        # Existing page code continues here...
        
        # Display previous content
        with st.expander("📄 Article Content", expanded=False):
            st.write(st.session_state['final_article'])
            st.write("### Image Description")
            st.write(st.session_state['image_description'])
        
        # SEO Settings
        st.write("### 🎯 SEO Target Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Keyword settings
            st.write("#### Keyword Strategy")
            
            primary_keyword = st.text_input(
                "Primary Keyword:",
                help="Enter the main keyword to target"
            )
            
            secondary_keywords = st.text_area(
                "Secondary Keywords (one per line):",
                help="Enter supporting keywords"
            ).split('\n')
            
            long_tail_keywords = st.text_area(
                "Long-tail Keywords (one per line):",
                help="Enter long-tail keyword variations"
            ).split('\n')
        
        with col2:
            # Target settings
            st.write("#### Target Settings")
            
            target_location = st.selectbox(
                "Target Location:",
                ["Global", "United States", "Europe", "Asia"],
                help="Select primary geographic target"
            )
            
            target_devices = st.multiselect(
                "Target Devices:",
                ["Desktop", "Mobile", "Tablet"],
                default=["Desktop", "Mobile"],
                help="Select target devices"
            )
            
            target_audience = st.multiselect(
                "Target Audience:",
                ["Employees", "HR Professionals", "Business Leaders", "Legal Professionals"],
                default=["Employees"],
                help="Select target audience segments"
            )
        
        # Schema Markup Settings
        st.write("### 📝 Schema Markup")
        
        selected_schemas = st.multiselect(
            "Select Schema Types:",
            list(SEOGenerator.SCHEMA_TYPES.keys()),
            default=["article"],
            format_func=lambda x: SEOGenerator.SCHEMA_TYPES[x]['name'],
            help="Select schema markup types to generate"
        )
        
        # Advanced SEO Settings
        with st.expander("⚙️ Advanced SEO Settings", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                search_intent = st.selectbox(
                    "Search Intent:",
                    ["Informational", "Navigational", "Commercial", "Transactional"],
                    help="Select primary search intent"
                )
                
                content_type = st.selectbox(
                    "Content Type:",
                    ["Blog Post", "Article", "Guide", "Case Study"],
                    help="Select content type for schema markup"
                )
            
            with col2:
                competition_level = st.slider(
                    "Competition Level:",
                    min_value=1,
                    max_value=10,
                    value=5,
                    help="Estimate keyword competition level"
                )
                
                readability_target = st.select_slider(
                    "Readability Target:",
                    options=["Basic", "Intermediate", "Advanced", "Expert"],
                    value="Intermediate",
                    help="Select target readability level"
                )
        
        # Generate SEO content
        if st.button("🚀 Generate SEO Content", help="Click to generate SEO optimization content"):
            if not primary_keyword:
                st.error("❌ Please enter a primary keyword.")
                return
                
            with st.spinner("✍️ Generating SEO content..."):
                try:
                    result = await generate_seo_content(
                        article=st.session_state['final_article'],
                        image_description=st.session_state['image_description'],
                        target_keywords=[primary_keyword] + secondary_keywords + long_tail_keywords,
                        schema_types=selected_schemas,
                        llm_client=llm_client,
                        prompt_handler=prompt_handler,
                        user_email=user_email
                    )
                    
                    if result['success']:
                        seo_data = result['seo_data']
                        
                        # Save SEO content
                        content_id = await db_handlers['blog'].save_content(
                            user_email=user_email,
                            content_type='seo_content',
                            content=json.dumps(seo_data),
                            metadata={
                                'final_id': st.session_state['final_id'],
                                'primary_keyword': primary_keyword,
                                'secondary_keywords': secondary_keywords,
                                'long_tail_keywords': long_tail_keywords,
                                'target_location': target_location,
                                'target_devices': target_devices,
                                'target_audience': target_audience,
                                'search_intent': search_intent,
                                'content_type': content_type,
                                'competition_level': competition_level,
                                'readability_target': readability_target
                            }
                        )
                        
                        # Update session state
                        st.session_state['seo_content'] = seo_data
                        st.session_state['seo_id'] = content_id
                        
                        # Log activity
                        await db_handlers['analytics'].log_activity(
                            user_email=user_email,
                            activity_type='seo_generation',
                            metadata={
                                'content_id': content_id,
                                'primary_keyword': primary_keyword
                            }
                        )
                        
                        # Display SEO content
                        st.success("✅ SEO content generated successfully!")
                        
                        # Meta Information
                        st.write("### 📊 Meta Information")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            meta_title = st.text_input(
                                "Meta Title:",
                                value=seo_data.get('meta_title', ''),
                                help="Edit meta title"
                            )
                            
                            title_validation = SEOGenerator.validate_meta_title(meta_title)
                            st.write(title_validation['message'])
                            if not title_validation['valid']:
                                st.warning("⚠️ Title length should be between 30-60 characters")
                        
                        with col2:
                            meta_description = st.text_area(
                                "Meta Description:",
                                value=seo_data.get('meta_description', ''),
                                help="Edit meta description"
                            )
                            
                            desc_validation = SEOGenerator.validate_meta_description(meta_description)
                            st.write(desc_validation['message'])
                            if not desc_validation['valid']:
                                st.warning("⚠️ Description length should be between 120-160 characters")
                        
                        # URL Slug
                        suggested_slug = SEOGenerator.generate_slug(meta_title)
                        url_slug = st.text_input(
                            "URL Slug:",
                            value=suggested_slug,
                            help="Edit URL slug"
                        )
                        
                        # Keyword Analysis
                        st.write("### 🔍 Keyword Analysis")
                        
                        keyword_data = seo_data.get('keyword_analysis', {})
                        for keyword_type, keywords in keyword_data.items():
                            with st.expander(f"{keyword_type.title()} Keywords"):
                                edited_keywords = st.text_area(
                                    f"Edit {keyword_type} keywords:",
                                    value='\n'.join(keywords),
                                    key=f"edit_{keyword_type}"
                                ).split('\n')
                                keyword_data[keyword_type] = edited_keywords
                        
                        # Schema Markup
                        st.write("### 📝 Schema Markup")
                        schema_markup = seo_data.get('schema_markup', {})
                        for schema_type in selected_schemas:
                            with st.expander(f"{SEOGenerator.SCHEMA_TYPES[schema_type]['name']}"):
                                schema_json = st.text_area(
                                    f"Edit {schema_type} schema:",
                                    value=json.dumps(schema_markup.get(schema_type, {}), indent=2),
                                    height=200,
                                    key=f"schema_{schema_type}"
                                )
                                try:
                                    schema_markup[schema_type] = json.loads(schema_json)
                                except json.JSONDecodeError:
                                    st.error("❌ Invalid JSON format")
                        
                        # Save changes
                        if st.button("💾 Save SEO Changes"):
                            try:
                                updated_seo_data = {
                                    'meta_title': meta_title,
                                    'meta_description': meta_description,
                                    'url_slug': url_slug,
                                    'keyword_analysis': keyword_data,
                                    'schema_markup': schema_markup
                                }
                                
                                await db_handlers['blog'].update_content(
                                    content_id,
                                    {'content': json.dumps(updated_seo_data)}
                                )
                                
                                st.session_state['seo_content'] = updated_seo_data
                                st.success("✅ SEO content updated successfully!")
                                
                            except Exception as e:
                                st.error(f"❌ Error saving SEO content: {str(e)}")
                        
                        # Export options
                        if st.button("📤 Export SEO Package"):
                            export_data = {
                                'meta_information': {
                                    'title': meta_title,
                                    'description': meta_description,
                                    'url_slug': url_slug
                                },
                                'keyword_analysis': keyword_data,
                                'schema_markup': schema_markup,
                                'settings': {
                                    'target_location': target_location,
                                    'target_devices': target_devices,
                                    'target_audience': target_audience,
                                    'search_intent': search_intent,
                                    'content_type': content_type,
                                    'competition_level': competition_level,
                                    'readability_target': readability_target
                                }
                            }
                            
                            st.download_button(
                                label="📥 Download SEO Package",
                                data=json.dumps(export_data, indent=2),
                                file_name=f"seo_package_{content_id}.json",
                                mime="application/json"
                            )
                        
                    else:
                        st.error(f"❌ Failed to generate SEO content: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")
                    logger.error(f"Error in SEO content generation: {str(e)}")
        
        # SEO History
        with st.expander("📚 SEO History", expanded=False):
            try:
                seo_history = await db_handlers['blog'].get_user_content(
                    user_email=user_email,
                    content_type='seo_content',
                    limit=5
                )
                
                if seo_history:
                    for entry in seo_history:
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            metadata = entry.get('metadata', {})
                            st.write(f"**Primary Keyword:** {metadata.get('primary_keyword', 'Unknown')}")
                            st.write(f"Generated: {entry['created_at'].strftime('%Y-%m-%d %H:%M')}")
                            
                        with col2:
                            if st.button("Load", key=f"load_{entry['_id']}"):
                                st.session_state['seo_content'] = json.loads(entry['content'])
                                st.session_state['seo_id'] = str(entry['_id'])
                                st.experimental_rerun()
                                
                        with col3:
                            if st.button("Delete", key=f"delete_{entry['_id']}"):
                                try:
                                    await db_handlers['blog'].delete_content(str(entry['_id']))
                                    st.success("✅ SEO content deleted successfully!")
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error(f"❌ Error deleting SEO content: {str(e)}")
                        
                        st.markdown("---")
                else:
                    st.info("No previous SEO content found.")
                    
            except Exception as e:
                st.error("Failed to load SEO history")
                logger.error(f"Error loading SEO history: {str(e)}")

        # Help section
        with st.expander("❓ Need Help?", expanded=False):
            st.markdown("""
            ### SEO Guidelines
            1. Use target keywords naturally
            2. Optimize meta information
            3. Create descriptive URLs
            4. Implement proper schema markup
            5. Consider search intent
            
            ### Best Practices
            - Keep titles under 60 characters
            - Meta descriptions between 120-160 characters
            - Use relevant keywords
            - Include call-to-action
            - Optimize for mobile
            
            ### Support
            Contact: seo@fairnessfactor.com
            """)

    except Exception as e:
        logger.error(f"Error in SEO generation page: {str(e)}")
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
        
        await seo_generation_page(
            handlers,
            AsyncLLMClient(),
            AsyncPromptHandler(db)
        )
    
    asyncio.run(test_page())