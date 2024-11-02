# pages/final_article.py
import streamlit as st
import asyncio
from typing import Dict, Any, Optional
from llm.llm_client import AsyncLLMClient
from utils.prompt_handler import AsyncPromptHandler
from datetime import datetime
import logging
import json
import yaml
import re

logger = logging.getLogger(__name__)

class FinalArticleGenerator:
    """Handles final article generation and validation"""
    
    QUALITY_CHECKLIST = {
        "content": [
            "All editing suggestions addressed",
            "Facts and statistics verified",
            "Legal information accurate",
            "Citations properly formatted",
            "Examples relevant and current"
        ],
        "structure": [
            "Logical flow maintained",
            "Transitions smooth",
            "Paragraphs well-organized",
            "Headers properly structured",
            "Sections balanced"
        ],
        "style": [
            "Brand voice consistent",
            "Tone appropriate",
            "Language accessible",
            "Technical terms explained",
            "Writing engaging"
        ],
        "seo": [
            "Keywords naturally incorporated",
            "Meta information optimized",
            "Headers SEO-friendly",
            "Alt text for images",
            "Internal links added"
        ]
    }
    
    @staticmethod
    def validate_article(content: str) -> Dict[str, Any]:
        """Validate final article content"""
        min_length = 1000
        max_length = 5000
        current_length = len(content.split())
        
        return {
            'valid': min_length <= current_length <= max_length,
            'length': current_length,
            'message': f"Article length: {current_length} words (should be between {min_length} and {max_length})"
        }
    
    @staticmethod
    def generate_slug(title: str) -> str:
        """Generate URL-friendly slug from title"""
        # Convert to lowercase and replace spaces with hyphens
        slug = title.lower().strip()
        # Remove special characters
        slug = re.sub(r'[^\w\s-]', '', slug)
        # Replace spaces and repeated hyphens with single hyphen
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug

async def generate_final_article(
    draft: str,
    suggestions: str,
    feedback: Dict[str, Any],
    llm_client: AsyncLLMClient,
    prompt_handler: AsyncPromptHandler,
    user_email: str
) -> Dict[str, Any]:
    """Generate final article incorporating editing suggestions and feedback"""
    try:
        # Check user authentication
        if not user_email:
            raise ValueError("User not authenticated")

        # Format final article prompt
        final_prompt = await prompt_handler.format_prompt(
            'final_article',
            {
                'article_draft': draft,
                'editing_suggestions': suggestions,
                'user_feedback': json.dumps(feedback, indent=2)
            }
        )
        
        if not final_prompt:
            raise ValueError("Failed to format final article prompt")

        # Generate final article
        final_content = await llm_client.generate_response(
            system_prompt=(
                "You are an expert content editor finalizing a Fairness Factor blog article. "
                "Incorporate all editing suggestions while maintaining brand voice and "
                "ensuring the article effectively communicates employee advocacy messages. "
                "Focus on creating engaging, informative content that provides value to readers."
            ),
            user_prompt=final_prompt,
            max_tokens=3000,
            user_email=user_email
        )
        
        # Validate article
        validation = FinalArticleGenerator.validate_article(final_content)
        if not validation['valid']:
            raise ValueError(f"Generated article does not meet requirements: {validation['message']}")
        
        return {
            'success': True,
            'article': final_content,
            'validation': validation
        }
    except Exception as e:
        logger.error(f"Error generating final article: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

async def final_article_page(
    db_handlers: Dict[str, Any],
    llm_client: AsyncLLMClient,
    prompt_handler: AsyncPromptHandler
):
    """Final Article Page Handler"""
    try:
        # Check user authentication
        if 'user' not in st.session_state or not st.session_state.user:
            st.warning("Please log in to access this page.")
            return

        user_email = st.session_state.user['email']
        
        st.title("Generate Final Fairness Factor Blog Article")
        
        # Check prerequisites
        if 'editing_suggestions' not in st.session_state:
            st.warning("⚠️ Please complete the Editing Criteria step first.")
            return
        
        # Display previous content
        col1, col2 = st.columns(2)
        
        with col1:
            with st.expander("📄 Original Draft", expanded=False):
                st.write(st.session_state['article_draft'])
                
        with col2:
            with st.expander("✏️ Editing Suggestions", expanded=False):
                st.write(st.session_state['editing_suggestions'])
        
        # Article metadata
        st.write("### 📋 Article Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input(
                "Article Title:",
                value=st.session_state.get('selected_topic', ''),
                help="Enter the final article title"
            )
            
            author = st.text_input(
                "Author Name:",
                value=st.session_state.user['name'],
                help="Enter the author's name"
            )
        
        with col2:
            publish_date = st.date_input(
                "Publication Date:",
                value=datetime.now(),
                help="Select planned publication date"
            )
            
            categories = st.multiselect(
                "Categories:",
                ["Employee Rights", "Workplace Safety", "Legal Updates", 
                 "HR Best Practices", "Career Development", "Industry News"],
                help="Select relevant categories"
            )
        
        # Quality checklist
        st.write("### ✅ Quality Checklist")
        
        checklist_status = {}
        for category, items in FinalArticleGenerator.QUALITY_CHECKLIST.items():
            st.write(f"#### {category.title()}")
            for item in items:
                checked = st.checkbox(item, key=f"check_{category}_{item}")
                checklist_status[f"{category}_{item}"] = checked
        
        # Additional feedback
        st.write("### 💭 Final Revisions")
        
        feedback = {
            "tone_adjustments": st.text_area(
                "Tone Adjustments:",
                help="Any specific adjustments to tone or voice"
            ),
            "content_focus": st.text_area(
                "Content Focus:",
                help="Areas to emphasize or clarify"
            ),
            "additional_notes": st.text_area(
                "Additional Notes:",
                help="Any other feedback for the final version"
            )
        }
        
        # Generate final article
        if st.button("🚀 Generate Final Article", help="Click to generate the final version"):
            if not title or not author:
                st.error("❌ Please fill in all article details.")
                return
                
            with st.spinner("✍️ Generating final article..."):
                try:
                    result = await generate_final_article(
                        draft=st.session_state['article_draft'],
                        suggestions=st.session_state['editing_suggestions'],
                        feedback=feedback,
                        llm_client=llm_client,
                        prompt_handler=prompt_handler,
                        user_email=user_email
                    )
                    
                    if result['success']:
                        # Generate slug
                        slug = FinalArticleGenerator.generate_slug(title)
                        
                        # Prepare metadata
                        metadata = {
                            'title': title,
                            'author': author,
                            'publish_date': publish_date.isoformat(),
                            'categories': categories,
                            'slug': slug,
                            'checklist_status': checklist_status,
                            'feedback': feedback,
                            'word_count': result['validation']['length']
                        }
                        
                        # Save final article
                        content_id = await db_handlers['blog'].save_content(
                            user_email=user_email,
                            content_type='final_article',
                            content=result['article'],
                            metadata={
                                'article_metadata': metadata,
                                'draft_id': st.session_state['draft_id'],
                                'editing_id': st.session_state['editing_id']
                            }
                        )
                        
                        # Update session state
                        st.session_state['final_article'] = result['article']
                        st.session_state['final_id'] = content_id
                        
                        # Log activity
                        await db_handlers['analytics'].log_activity(
                            user_email=user_email,
                            activity_type='final_article',
                            metadata={
                                'content_id': content_id,
                                'title': title
                            }
                        )
                        
                        # Display success and validation
                        st.success("✅ Final article generated successfully!")
                        st.info(result['validation']['message'])
                        
                        # Article preview
                        st.write("### 📖 Final Article Preview")
                        
                        # Article sections
                        sections = result['article'].split('\n\n')
                        for i, section in enumerate(sections):
                            with st.expander(f"Section {i+1}", expanded=i==0):
                                st.write(section)
                        
                        # Export options
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            # Export as Markdown
                            markdown_content = f"""---
title: {title}
author: {author}
date: {publish_date}
categories: {', '.join(categories)}
slug: {slug}
---

{result['article']}
"""
                            st.download_button(
                                label="📥 Export as Markdown",
                                data=markdown_content,
                                file_name=f"article_{slug}.md",
                                mime="text/markdown"
                            )
                        
                        with col2:
                            # Export as JSON
                            export_data = {
                                'metadata': metadata,
                                'content': result['article'],
                                'history': {
                                    'draft_id': st.session_state['draft_id'],
                                    'editing_id': st.session_state['editing_id']
                                }
                            }
                            
                            st.download_button(
                                label="📤 Export as JSON",
                                data=json.dumps(export_data, indent=2),
                                file_name=f"article_{slug}.json",
                                mime="application/json"
                            )
                        
                        with col3:
                            # Preview formatted
                            if st.button("👀 Preview Formatted"):
                                st.markdown(f"# {title}")
                                st.markdown(f"*By {author} | {publish_date}*")
                                st.markdown("---")
                                st.markdown(result['article'])
                        
                    else:
                        st.error(f"❌ Failed to generate final article: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")
                    logger.error(f"Error in final article generation: {str(e)}")
        
        # Article history
        with st.expander("📚 Article History", expanded=False):
            try:
                article_history = await db_handlers['blog'].get_user_content(
                    user_email=user_email,
                    content_type='final_article',
                    limit=5
                )
                
                if article_history:
                    for entry in article_history:
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            metadata = entry.get('metadata', {}).get('article_metadata', {})
                            st.write(f"**{metadata.get('title', 'Untitled')}**")
                            st.write(f"Created: {entry['created_at'].strftime('%Y-%m-%d %H:%M')}")
                            
                        with col2:
                            if st.button("Load", key=f"load_{entry['_id']}"):
                                st.session_state['final_article'] = entry['content']
                                st.session_state['final_id'] = str(entry['_id'])
                                st.experimental_rerun()
                                
                        with col3:
                            if st.button("Delete", key=f"delete_{entry['_id']}"):
                                try:
                                    await db_handlers['blog'].delete_content(str(entry['_id']))
                                    st.success("✅ Article deleted successfully!")
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error(f"❌ Error deleting article: {str(e)}")
                        
                        st.markdown("---")
                else:
                    st.info("No previous articles found.")
                    
            except Exception as e:
                st.error("Failed to load article history")
                logger.error(f"Error loading article history: {str(e)}")

        # Help section
        with st.expander("❓ Need Help?", expanded=False):
            st.markdown("""
            ### Final Article Guidelines
            1. Ensure all editing suggestions are addressed
            2. Maintain consistent brand voice
            3. Verify all facts and citations
            4. Check for proper formatting
            5. Review SEO optimization
            
            ### Quality Checklist
            - Clear and engaging introduction
            - Logical flow of ideas
            - Strong supporting examples
            - Effective conclusion
            - Call-to-action included
            
            ### Support
            Contact: content@fairnessfactor.com
            """)

    except Exception as e:
        logger.error(f"Error in final article page: {str(e)}")
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
        
        await final_article_page(
            handlers,
            AsyncLLMClient(),
            AsyncPromptHandler(db)
        )
    
    asyncio.run(test_page())