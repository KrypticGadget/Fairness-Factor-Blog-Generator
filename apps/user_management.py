# apps/user_management.py
from .base_app import BaseApp
import streamlit as st
from typing import Dict, Any
import logging
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

class UserManagementApp(BaseApp):
    def __init__(self):
        super().__init__()
        self.title = "User Management"
        self.description = "Manage users and permissions"
        self.icon = "👥"

    async def initialize(self, handlers: Dict[str, Any]) -> bool:
        try:
            # Initialize any required resources
            return True
        except Exception as e:
            logger.error(f"User Management initialization error: {str(e)}")
            return False

    async def render(self, handlers: Dict[str, Any]):
        st.title(f"{self.icon} {self.title}")
        
        # Check if user has admin permissions
        if not await self.check_permissions(handlers, 'admin'):
            self.show_error("You do not have permission to access this page.")
            return
        
        # Sidebar options
        with st.sidebar:
            view = st.radio(
                "View",
                ["User List", "Add User", "Roles & Permissions", "Audit Log"]
            )
        
        try:
            if view == "User List":
                await self.render_user_list(handlers)
            elif view == "Add User":
                await self.render_add_user(handlers)
            elif view == "Roles & Permissions":
                await self.render_roles_permissions(handlers)
            elif view == "Audit Log":
                await self.render_audit_log(handlers)
                
        except Exception as e:
            logger.error(f"Error rendering {view}: {str(e)}")
            self.show_error(f"An error occurred while loading {view}")

    async def render_user_list(self, handlers: Dict[str, Any]):
        st.header("User List")
        
        # Get all users
        users = await handlers['auth'].get_all_users()
        
        if users:
            # Convert to DataFrame for easier display
            df = pd.DataFrame(users)
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['last_login'] = pd.to_datetime(df['last_login'])
            
            # Display user table
            st.dataframe(df[['email', 'name', 'role', 'status', 'created_at', 'last_login']])
            
            # User actions
            st.subheader("User Actions")
            selected_user = st.selectbox("Select User", df['email'])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Edit User"):
                    st.session_state['editing_user'] = selected_user
            with col2:
                if st.button("Disable User"):
                    if await handlers['auth'].update_user_status(selected_user, 'disabled'):
                        self.show_success(f"User {selected_user} has been disabled")
                        st.rerun()
            with col3:
                if st.button("Delete User"):
                    if await handlers['auth'].delete_user(selected_user):
                        self.show_success(f"User {selected_user} has been deleted")
                        st.rerun()
            
            # Edit user form
            if st.session_state.get('editing_user'):
                await self.render_edit_user(handlers, st.session_state['editing_user'])
        else:
            st.info("No users found.")

    async def render_add_user(self, handlers: Dict[str, Any]):
        st.header("Add New User")
        
        with st.form("add_user_form"):
            email = st.text_input("Email")
            name = st.text_input("Name")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["user", "admin"])
            
            if st.form_submit_button("Add User"):
                try:
                    result = await handlers['auth'].add_user(
                        email=email,
                        name=name,
                        password=password,
                        role=role,
                        added_by=st.session_state.user['email']
                    )
                    if result:
                        self.show_success(f"User {email} added successfully!")
                        # Log activity
                        await handlers['audit'].log_event(
                            st.session_state.user['email'],
                            'user_added',
                            {'added_user': email}
                        )
                    else:
                        self.show_error("Failed to add user")
                except ValueError as ve:
                    self.show_error(str(ve))
                except Exception as e:
                    logger.error(f"Error adding user: {str(e)}")
                    self.show_error("An error occurred while adding the user")

    async def render_edit_user(self, handlers: Dict[str, Any], user_email: str):
        st.subheader(f"Edit User: {user_email}")
        
        user = await handlers['auth'].get_user(user_email)
        if user:
            with st.form("edit_user_form"):
                name = st.text_input("Name", value=user['name'])
                role = st.selectbox("Role", ["user", "admin"], index=["user", "admin"].index(user['role']))
                status = st.selectbox("Status", ["active", "disabled"], index=["active", "disabled"].index(user['status']))
                
                if st.form_submit_button("Update User"):
                    updates = {
                        'name': name,
                        'role': role,
                        'status': status
                    }
                    if await handlers['auth'].update_user(user_email, updates):
                        self.show_success(f"User {user_email} updated successfully!")
                        # Log activity
                        await handlers['audit'].log_event(
                            st.session_state.user['email'],
                            'user_updated',
                            {'updated_user': user_email, 'updates': updates}
                        )
                        st.session_state.pop('editing_user')
                        st.rerun()
                    else:
                        self.show_error("Failed to update user")
        else:
            st.error(f"User {user_email} not found")

    async def render_roles_permissions(self, handlers: Dict[str, Any]):
        st.header("Roles & Permissions")
        
        # Get all roles and permissions
        roles = await handlers['auth'].get_all_roles()
        
        if roles:
            for role in roles:
                st.subheader(role['name'].capitalize())
                
                # Display current permissions
                st.write("Current Permissions:")
                for perm in role['permissions']:
                    st.write(f"- {perm}")
                
                # Add/Remove permissions
                new_perm = st.text_input(f"Add permission to {role['name']}")
                if st.button(f"Add to {role['name']}"):
                    if await handlers['auth'].add_permission_to_role(role['name'], new_perm):
                        self.show_success(f"Added {new_perm} to {role['name']}")
                        st.rerun()
                
                remove_perm = st.selectbox(f"Remove permission from {role['name']}", role['permissions'])
                if st.button(f"Remove from {role['name']}"):
                    if await handlers['auth'].remove_permission_from_role(role['name'], remove_perm):
                        self.show_success(f"Removed {remove_perm} from {role['name']}")
                        st.rerun()
                
                st.markdown("---")
            
            # Create new role
            st.subheader("Create New Role")
            with st.form("create_role_form"):
                new_role_name = st.text_input("New Role Name")
                new_role_permissions = st.text_area("Permissions (one per line)")
                
                if st.form_submit_button("Create Role"):
                    permissions = [p.strip() for p in new_role_permissions.split('\n') if p.strip()]
                    if await handlers['auth'].create_role(new_role_name, permissions):
                        self.show_success(f"Created new role: {new_role_name}")
                        st.rerun()
                    else:
                        self.show_error("Failed to create new role")
        else:
            st.info("No roles defined.")

    async def render_audit_log(self, handlers: Dict[str, Any]):
        st.header("Audit Log")
        
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=(datetime.now() - timedelta(days=30)).date()
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now().date()
            )
        
        # Get audit log entries
        audit_log = await handlers['audit'].get_audit_log(start_date, end_date)
        
        if audit_log:
            df = pd.DataFrame(audit_log)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Display audit log
            st.dataframe(df[['timestamp', 'user_email', 'action', 'details']])
            
            # Export option
            if st.button("Export Audit Log"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"audit_log_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No audit log entries found for the selected date range.")