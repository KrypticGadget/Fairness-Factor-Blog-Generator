# pages/admin_dashboard.py
import streamlit as st
import asyncio
from typing import Dict, Any
import logging
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px

logger = logging.getLogger(__name__)

async def admin_dashboard_page(db_handlers: Dict[str, Any]):
    """Admin dashboard page"""
    if not st.session_state.get('authenticated') or st.session_state.get('user', {}).get('role') != 'admin':
        st.error("Access denied")
        return
    
    st.title("Admin Dashboard")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=30)
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now()
        )
    
    try:
        # User activity metrics
        st.subheader("User Activity")
        
        activity_data = await db_handlers['analytics'].get_activity_metrics(
            start_date=start_date,
            end_date=end_date
        )
        
        if activity_data:
            # Create activity chart
            df = pd.DataFrame(activity_data)
            fig = px.line(
                df,
                x='date',
                y='count',
                color='activity_type',
                title='User Activity Over Time'
            )
            st.plotly_chart(fig)
        
        # Content metrics
        st.subheader("Content Statistics")
        
        content_stats = await db_handlers['blog'].get_content_statistics(
            start_date=start_date,
            end_date=end_date
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Articles", content_stats['total_articles'])
        with col2:
            st.metric("Active Users", content_stats['active_users'])
        with col3:
            st.metric("Avg. Articles/User", content_stats['avg_articles_per_user'])
        
        # User management section
        st.subheader("User Management")
        
        users = await db_handlers['auth'].get_all_users()
        if users:
            user_df = pd.DataFrame(users)
            st.dataframe(user_df)
        
        # System health metrics
        st.subheader("System Health")
        
        health_metrics = await db_handlers['analytics'].get_system_health()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("API Response Time", f"{health_metrics['avg_response_time']:.2f}ms")
        with col2:
            st.metric("Error Rate", f"{health_metrics['error_rate']:.2f}%")
        
    except Exception as e:
        logger.error(f"Admin dashboard error: {str(e)}")
        st.error("Error loading dashboard data")