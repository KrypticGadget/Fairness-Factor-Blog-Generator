# pages/user_management.py
import streamlit as st
import asyncio
from typing import Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def user_management_page(db_handlers, auth_handler):
    """User Management Page"""
    if not st.session_state.authenticated or st.session_state.user.get('role') != 'admin':
        st.error("Access denied. Admin privileges required.")
        return
        
    st.title("User Management")
    
    admin_email = st.session_state.user['email']  # Get admin email from session state
    
    # Add new user form
    with st.expander("Add New User", expanded=False):
        with st.form("add_user_form"):
            new_email = st.text_input("Email", placeholder="example@fairnessfactor.com")
            new_name = st.text_input("Name")
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["user", "admin"])
            
            if st.form_submit_button("Add User"):
                try:
                    if await auth_handler.add_user(
                        email=new_email,
                        password=new_password,
                        name=new_name,
                        added_by=admin_email,
                        role=new_role
                    ):
                        st.success(f"User {new_email} added successfully!")
                        # Log activity
                        await db_handlers['analytics'].log_activity(
                            admin_email,
                            'user_added',
                            {'added_user': new_email}
                        )
                    else:
                        st.error("Failed to add user")
                except ValueError as ve:
                    st.error(str(ve))
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # List existing users
    st.write("### Existing Users")
    users = await auth_handler.get_all_users()
    
    for user in users:
        with st.expander(f"{user['name']} ({user['email']})", expanded=False):
            col1, col2, col3 = st.columns([2,1,1])
            
            with col1:
                st.write(f"**Role:** {user['role']}")
                st.write(f"**Created:** {user['created_at'].strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Last Login:** {user.get('last_login', 'Never').strftime('%Y-%m-%d %H:%M') if user.get('last_login') else 'Never'}")
            
            with col2:
                new_role = st.selectbox(
                    "Change Role",
                    ["user", "admin"],
                    index=0 if user['role'] == 'user' else 1,
                    key=f"role_{user['email']}"
                )
                if new_role != user['role']:
                    if st.button("Update Role", key=f"update_role_{user['email']}"):
                        if await auth_handler.update_user(
                            user['email'], 
                            {'role': new_role},
                            admin_email  # Pass admin email
                        ):
                            st.success(f"Role updated for {user['email']}")
                            # Log activity
                            await db_handlers['analytics'].log_activity(
                                admin_email,
                                'user_role_changed',
                                {'user': user['email'], 'new_role': new_role}
                            )
                        else:
                            st.error("Failed to update role")
            
            with col3:
                if user['email'] != admin_email:  # Prevent self-deletion
                    if st.button("Delete User", key=f"delete_{user['email']}"):
                        if await auth_handler.delete_user(
                            user['email'],
                            admin_email  # Pass admin email
                        ):
                            st.success(f"User {user['email']} deleted")
                            # Log activity
                            await db_handlers['analytics'].log_activity(
                                admin_email,
                                'user_deleted',
                                {'deleted_user': user['email']}
                            )
                            st.experimental_rerun()
                        else:
                            st.error("Failed to delete user")
                else:
                    st.write("(Current User)")
            
            # Rest of the user management page remains the same...
            
            # User Activity
            if st.button("View Activity", key=f"activity_{user['email']}"):
                activity = await auth_handler.get_user_activity(user['email'])
                if activity:
                    st.write("#### Recent Activity")
                    for entry in activity[:10]:  # Show last 10 activities
                        st.write(f"- {entry['activity_type']} on {entry['timestamp'].strftime('%Y-%m-%d %H:%M')}")
                else:
                    st.write("No recent activity")
            
            # Login History
            if st.button("View Login History", key=f"login_history_{user['email']}"):
                login_history = await auth_handler.get_login_history(user['email'])
                if login_history:
                    st.write("#### Recent Logins")
                    for entry in login_history:
                        status = "✅ Success" if entry['success'] else f"❌ Failed ({entry.get('reason', 'Unknown')})"
                        st.write(f"- {entry['timestamp'].strftime('%Y-%m-%d %H:%M')} - {status}")
                else:
                    st.write("No login history available")

    # User Statistics
    st.write("### User Statistics")
    total_users = len(users)
    active_users = sum(1 for user in users if user.get('status') == 'active')
    admin_users = sum(1 for user in users if user.get('role') == 'admin')
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Users", total_users)
    col2.metric("Active Users", active_users)
    col3.metric("Admin Users", admin_users)

    # Recent Activity Log
    st.write("### Recent System Activity")
    recent_activity = await db_handlers['analytics'].get_recent_activity(limit=20)
    if recent_activity:
        for activity in recent_activity:
            st.write(f"- {activity['timestamp'].strftime('%Y-%m-%d %H:%M')} - {activity['user_email']} - {activity['activity_type']}")
    else:
        st.write("No recent activity logged")

    # Export User Data
    if st.button("Export User Data"):
        user_data = [
            {
                "email": user['email'],
                "name": user['name'],
                "role": user['role'],
                "created_at": user['created_at'].isoformat(),
                "last_login": user.get('last_login', '').isoformat() if user.get('last_login') else None,
                "status": user.get('status', 'unknown')
            }
            for user in users
        ]
        st.download_button(
            label="Download User Data CSV",
            data='\n'.join([','.join(user_data[0].keys())] + [','.join(map(str, user.values())) for user in user_data]),
            file_name=f"user_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

async def run_user_management_page(db_handlers, auth_handler):
    """Run the user management page"""
    try:
        await user_management_page(db_handlers, auth_handler)
    except Exception as e:
        logger.error(f"Error in user management page: {str(e)}")
        st.error("An unexpected error occurred. Please try again.")

if __name__ == "__main__":
    # For testing the page individually
    import os
    from dotenv import load_dotenv
    from utils.mongo_manager import AsyncMongoManager
    from utils.auth import AsyncAuthHandler
    
    load_dotenv()
    
    async def test_page():
        mongo_manager = AsyncMongoManager()
        client, db = await mongo_manager.get_connection()
        
        auth_handler = AsyncAuthHandler(db)
        
        handlers = {
            'analytics': None,  # Add your analytics handler here
        }
        
        await run_user_management_page(handlers, auth_handler)
    
    asyncio.run(test_page())