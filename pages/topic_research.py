# pages/topic_research.py
import streamlit as st
import asyncio
from typing import List, Dict, Any
import PyPDF2
import docx2txt
from llm.llm_client import AsyncLLMClient
from utils.prompt_handler import AsyncPromptHandler
import logging

logger = logging.getLogger(__name__)

async def process_documents(
    documents: List[str],
    llm_client: AsyncLLMClient,
    prompt_handler: AsyncPromptHandler,
    user_email: str
) -> Dict[str, Any]:
    """Process uploaded documents asynchronously"""
    try:
        # Format research prompt
        research_prompt = await prompt_handler.format_prompt(
            'topic_research',
            {'documents': '\n\n'.join(documents)}
        )
        
        if not research_prompt:
            raise ValueError("Failed to format research prompt")

        # Generate analysis
        analysis = await llm_client.generate_response(
            system_prompt="You are an AI assistant analyzing research documents...",
            user_prompt=research_prompt,
            user_email=user_email
        )
        
        return {
            'success': True,
            'analysis': analysis
        }
    except Exception as e:
        logger.error(f"Error processing documents: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

async def topic_research_page(
    db_handlers: Dict[str, Any],
    llm_client: AsyncLLMClient,
    prompt_handler: AsyncPromptHandler
):
    st.title("Fairness Factor Blog Topic Research")
    
    user_email = st.session_state.user['email']
    
    st.write("Upload up to 3 research documents related to employee rights, workplace issues, or legal advocacy.")
    uploaded_files = st.file_uploader(
        "Upload documents",
        type=["pdf", "docx", "txt", "md"],
        accept_multiple_files=True,
        key="research_files"
    )
    
    if uploaded_files:
        if len(uploaded_files) > 3:
            st.warning("Please upload a maximum of 3 documents.")
            return

        document_contents = []
        file_metadata = []
        
        for uploaded_file in uploaded_files:
            try:
                # Process file based on type
                if uploaded_file.type == "application/pdf":
                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    content = ""
                    for page in pdf_reader.pages:
                        content += page.extract_text()
                    document_contents.append(content)
                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    content = docx2txt.process(uploaded_file)
                    document_contents.append(content)
                else:  # For .txt and .md files
                    content = uploaded_file.getvalue().decode("utf-8")
                    document_contents.append(content)
                
                # Save file to GridFS
                file_id = await db_handlers['file'].save_file(
                    filename=uploaded_file.name,
                    file_data=uploaded_file.getvalue(),
                    metadata={
                        'user_email': user_email,
                        'file_type': uploaded_file.type,
                        'content_type': 'research_document'
                    }
                )
                
                file_metadata.append({
                    'file_id': file_id,
                    'filename': uploaded_file.name,
                    'file_type': uploaded_file.type
                })
                
            except Exception as e:
                st.error(f"Error processing file {uploaded_file.name}: {str(e)}")
                continue
        
        if document_contents and st.button("Analyze Research Documents"):
            with st.spinner("Analyzing documents..."):
                try:
                    # Process documents
                    result = await process_documents(
                        document_contents,
                        llm_client,
                        prompt_handler,
                        user_email
                    )
                    
                    if result['success']:
                        # Save research content
                        content_id = await db_handlers['blog'].save_research(
                            user_email=user_email,
                            document_contents=document_contents,
                            analysis=result['analysis']
                        )
                        
                        # Update session state
                        st.session_state['research_analysis'] = result['analysis']
                        st.session_state['research_id'] = content_id
                        st.session_state['research_files'] = file_metadata
                        
                        # Log activity
                        await db_handlers['analytics'].log_activity(
                            user_email=user_email,
                            activity_type='research_analysis',
                            metadata={
                                'content_id': content_id,
                                'num_documents': len(document_contents),
                                'files': file_metadata
                            }
                        )
                        
                        # Display results
                        st.write("Research Analysis:")
                        st.write(result['analysis'])
                        
                    else:
                        st.error(f"Analysis failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    logger.error(f"Error in topic research: {str(e)}")

    # Display research history
    with st.expander("View Research History"):
        try:
            research_history = await db_handlers['blog'].get_user_content(
                user_email=user_email,
                content_type='research',
                limit=5
            )
            
            if research_history:
                for entry in research_history:
                    st.write(f"Research from {entry['created_at'].strftime('%Y-%m-%d %H:%M')}")
                    if st.button(f"Load Analysis {entry['_id']}", key=f"load_{entry['_id']}"):
                        st.session_state['research_analysis'] = entry['analysis']
                        st.session_state['research_id'] = str(entry['_id'])
                        st.experimental_rerun()
            else:
                st.info("No previous research found.")
                
        except Exception as e:
            st.error("Failed to load research history")
            logger.error(f"Error loading research history: {str(e)}")