# pages/topic_research.py
import streamlit as st
import asyncio
from typing import List, Dict, Any, Optional
import PyPDF2
import docx2txt
from llm.llm_client import AsyncLLMClient
from utils.prompt_handler import AsyncPromptHandler
import logging
import io
from datetime import datetime

logger = logging.getLogger(__name__)

async def process_pdf(file_data: bytes) -> Optional[str]:
    """Process PDF file and extract text content"""
    try:
        pdf_file = io.BytesIO(file_data)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        content = []
        
        for page in pdf_reader.pages:
            content.append(page.extract_text())
            
        return "\n".join(content)
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        return None

async def process_docx(file_data: bytes) -> Optional[str]:
    """Process DOCX file and extract text content"""
    try:
        return docx2txt.process(io.BytesIO(file_data))
    except Exception as e:
        logger.error(f"Error processing DOCX: {str(e)}")
        return None

async def process_text_file(file_data: bytes) -> Optional[str]:
    """Process text file and extract content"""
    try:
        return file_data.decode('utf-8')
    except Exception as e:
        logger.error(f"Error processing text file: {str(e)}")
        return None

async def process_file(
    uploaded_file: Any,
    file_handlers: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Process uploaded file based on type"""
    try:
        file_data = uploaded_file.getvalue()
        content = None
        
        if uploaded_file.type == "application/pdf":
            content = await process_pdf(file_data)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            content = await process_docx(file_data)
        else:  # For .txt and .md files
            content = await process_text_file(file_data)
            
        if content is None:
            raise ValueError(f"Failed to process file: {uploaded_file.name}")
            
        return {
            'filename': uploaded_file.name,
            'content': content,
            'file_type': uploaded_file.type
        }
    except Exception as e:
        logger.error(f"Error processing file {uploaded_file.name}: {str(e)}")
        return None

async def analyze_documents(
    documents: List[Dict[str, Any]],
    llm_client: AsyncLLMClient,
    prompt_handler: AsyncPromptHandler,
    user_email: str
) -> Dict[str, Any]:
    """Analyze document contents using LLM"""
    try:
        # Check user authentication
        if not user_email:
            raise ValueError("User not authenticated")

        # Prepare documents for analysis
        doc_contents = [doc['content'] for doc in documents]
        doc_summary = "\n\n".join([
            f"Document: {doc['filename']}\nContent:\n{doc['content']}"
            for doc in documents
        ])
        
        # Format research prompt
        research_prompt = await prompt_handler.format_prompt(
            'topic_research',
            {
                'documents': doc_summary,
                'num_documents': len(documents)
            }
        )
        
        if not research_prompt:
            raise ValueError("Failed to format research prompt")

        # Generate analysis
        analysis = await llm_client.generate_response(
            system_prompt=(
                "You are an AI research assistant analyzing documents for "
                "Fairness Factor blog content. Focus on employee rights, "
                "workplace issues, and legal advocacy themes."
            ),
            user_prompt=research_prompt,
            max_tokens=2000,
            user_email=user_email
        )
        
        return {
            'success': True,
            'analysis': analysis,
            'document_contents': doc_contents
        }
    except Exception as e:
        logger.error(f"Error analyzing documents: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

async def topic_research_page(
    db_handlers: Dict[str, Any],
    llm_client: AsyncLLMClient,
    prompt_handler: AsyncPromptHandler
):
    """Topic Research Page Handler"""
    try:
        # Check user authentication
        if 'user' not in st.session_state or not st.session_state.user:
            st.warning("Please log in to access this page.")
            return

        user_email = st.session_state.user['email']
        
        st.title("Fairness Factor Blog Topic Research")
        
        # Display research guidelines
        with st.expander("Research Guidelines", expanded=True):
            st.markdown("""
            ### Document Upload Guidelines
            - Upload up to 3 research documents
            - Supported formats: PDF, DOCX, TXT, MD
            - Focus on employee rights, workplace issues, and legal advocacy
            - Documents should be relevant to Fairness Factor's mission
            
            ### Best Practices
            1. Include diverse perspectives
            2. Use recent and reliable sources
            3. Consider industry trends
            4. Focus on actionable insights
            """)
        
        # File upload section
        st.write("### Upload Research Documents")
        uploaded_files = st.file_uploader(
            "Upload up to 3 documents",
            type=["pdf", "docx", "txt", "md"],
            accept_multiple_files=True,
            key="research_files"
        )
        
        if uploaded_files:
            if len(uploaded_files) > 3:
                st.warning("⚠️ Please upload a maximum of 3 documents.")
                return

            processed_documents = []
            file_metadata = []
            
            # Process uploaded files
            with st.spinner("Processing documents..."):
                for uploaded_file in uploaded_files:
                    try:
                        # Process file
                        processed_file = await process_file(uploaded_file, db_handlers)
                        if processed_file:
                            processed_documents.append(processed_file)
                            
                            # Save to GridFS
                            file_id = await db_handlers['file'].save_file(
                                filename=uploaded_file.name,
                                file_data=uploaded_file.getvalue(),
                                metadata={
                                    'user_email': user_email,
                                    'file_type': uploaded_file.type,
                                    'content_type': 'research_document',
                                    'upload_date': datetime.now().isoformat()
                                }
                            )
                            
                            file_metadata.append({
                                'file_id': file_id,
                                'filename': uploaded_file.name,
                                'file_type': uploaded_file.type
                            })
                            
                    except Exception as e:
                        st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                        continue
            
            # Display processed files
            if processed_documents:
                st.write("### Processed Documents")
                for doc in processed_documents:
                    with st.expander(f"📄 {doc['filename']}", expanded=False):
                        st.text_area(
                            "Content Preview",
                            value=doc['content'][:500] + "...",
                            height=150,
                            key=f"preview_{doc['filename']}"
                        )
                
                # Analyze documents button
                if st.button("🔍 Analyze Documents"):
                    with st.spinner("Analyzing documents..."):
                        try:
                            # Analyze documents
                            result = await analyze_documents(
                                processed_documents,
                                llm_client,
                                prompt_handler,
                                user_email
                            )
                            
                            if result['success']:
                                # Save research content
                                content_id = await db_handlers['blog'].save_research(
                                    user_email=user_email,
                                    document_contents=result['document_contents'],
                                    analysis=result['analysis'],
                                    metadata={
                                        'files': file_metadata,
                                        'analysis_date': datetime.now().isoformat()
                                    }
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
                                        'num_documents': len(processed_documents),
                                        'files': file_metadata
                                    }
                                )
                                
                                # Display results
                                st.success("✅ Analysis completed successfully!")
                                st.write("### Research Analysis")
                                
                                # Display analysis in sections
                                analysis_sections = result['analysis'].split('\n\n')
                                for i, section in enumerate(analysis_sections):
                                    with st.expander(f"Section {i+1}", expanded=i==0):
                                        st.write(section)
                                        
                                        # Add section feedback
                                        feedback = st.text_area(
                                            "Section Feedback:",
                                            key=f"feedback_{i}",
                                            help="Add notes or feedback for this section"
                                        )
                                        if feedback:
                                            st.session_state.setdefault('section_feedback', {})[i] = feedback
                                
                            else:
                                st.error(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
                                
                        except Exception as e:
                            st.error(f"❌ An error occurred: {str(e)}")
                            logger.error(f"Error in topic research: {str(e)}")

        # Research history section
        with st.expander("📚 View Research History", expanded=False):
            try:
                research_history = await db_handlers['blog'].get_user_content(
                    user_email=user_email,
                    content_type='research',
                    limit=5
                )
                
                if research_history:
                    for entry in research_history:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"Research from {entry['created_at'].strftime('%Y-%m-%d %H:%M')}")
                        with col2:
                            if st.button(
                                "Load",
                                key=f"load_{entry['_id']}",
                                help="Load this research analysis"
                            ):
                                st.session_state['research_analysis'] = entry['analysis']
                                st.session_state['research_id'] = str(entry['_id'])
                                st.experimental_rerun()
                        st.markdown("---")
                else:
                    st.info("No previous research found.")
                    
            except Exception as e:
                st.error("Failed to load research history")
                logger.error(f"Error loading research history: {str(e)}")

    except Exception as e:
        logger.error(f"Error in topic research page: {str(e)}")
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
        
        await topic_research_page(
            handlers,
            AsyncLLMClient(),
            AsyncPromptHandler(db)
        )
    
    asyncio.run(test_page())