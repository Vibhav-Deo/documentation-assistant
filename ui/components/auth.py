import streamlit as st
from services.auth import auth_service

def render_login_page():
    """Render login/registration page"""
    st.title("🔐 Welcome to AI Assistant")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        render_login_form()
    
    with tab2:
        render_register_form()
    
    st.divider()
    render_oauth_options()

def render_login_form():
    """Render login form"""
    st.subheader("Sign In")
    
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="your.email@company.com")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Sign In", use_container_width=True):
            if email and password:
                with st.spinner("Signing in..."):
                    print(f"UI Form: Attempting login for {email}")
                    result = auth_service.login(email, password)
                    print(f"UI Form: Login result: {result is not None}")
                    if result:
                        print(f"UI Form: Result keys: {list(result.keys())}")
                        st.session_state.auth_token = result["access_token"]
                        st.session_state.user_info = result
                        # Store in browser localStorage
                        import json
                        token = result["access_token"]
                        user_info_json = json.dumps(result).replace("'", "\\'").replace('"', '\\"')
                        st.markdown(f"""
                        <script>
                        localStorage.setItem('auth_token', '{token}');
                        localStorage.setItem('user_info', '{user_info_json}')
                        </script>
                        """, unsafe_allow_html=True)
                        st.success("✅ Signed in successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
                        print("UI Form: Login failed - no result returned")
            else:
                st.error("Please fill in all fields")

def render_register_form():
    """Render registration form"""
    st.subheader("Create Account")
    
    with st.form("register_form"):
        name = st.text_input("Full Name", placeholder="John Doe")
        email = st.text_input("Email", placeholder="john@company.com")
        organization = st.text_input("Organization", placeholder="Your Company")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        if st.form_submit_button("Create Account", use_container_width=True):
            if all([name, email, organization, password, confirm_password]):
                if password != confirm_password:
                    st.error("Passwords don't match")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    with st.spinner("Creating account..."):
                        result = auth_service.register(email, password, name, organization)
                        if result:
                            st.session_state.auth_token = result["access_token"]
                            st.session_state.user_info = result
                            st.success("✅ Account created successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Registration failed. Email might already exist.")
            else:
                st.error("Please fill in all fields")

def render_oauth_options():
    """Render OAuth login options"""
    st.subheader("Or sign in with")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Google", use_container_width=True):
            google_url = auth_service.get_google_auth_url()
            if google_url:
                st.markdown(f'<a href="{google_url}" target="_blank">Continue with Google</a>', unsafe_allow_html=True)
            else:
                st.error("Google OAuth not configured")
    
    with col2:
        if st.button("🏢 Microsoft", use_container_width=True):
            microsoft_url = auth_service.get_microsoft_auth_url()
            if microsoft_url:
                st.markdown(f'<a href="{microsoft_url}" target="_blank">Continue with Microsoft</a>', unsafe_allow_html=True)
            else:
                st.error("Microsoft OAuth not configured")

def render_user_info():
    """Render user information in sidebar"""
    if "user_info" in st.session_state:
        user = st.session_state.user_info["user"]
        org = st.session_state.user_info["organization"]
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 👤 User Info")
        st.sidebar.write(f"**Name:** {user['name']}")
        st.sidebar.write(f"**Email:** {user['email']}")
        st.sidebar.write(f"**Role:** {user['role'].title()}")
        
        st.sidebar.markdown("### 🏢 Organization")
        st.sidebar.write(f"**Name:** {org['name']}")
        st.sidebar.write(f"**Plan:** {org['plan'].title()}")
        
        # Quota information
        if org['plan'] != 'enterprise':
            quota_used = org['used_quota']
            quota_total = org['monthly_quota']
            quota_pct = (quota_used / quota_total) * 100 if quota_total > 0 else 0
            
            st.sidebar.markdown("### 📊 Usage")
            st.sidebar.progress(quota_pct / 100)
            st.sidebar.write(f"{quota_used}/{quota_total} requests used")
            
            if quota_pct > 80:
                st.sidebar.warning("⚠️ Approaching quota limit")
        else:
            st.sidebar.markdown("### 📊 Usage")
            st.sidebar.write("✨ Unlimited requests")
        
        if st.sidebar.button("🚪 Logout"):
            auth_service.logout()

def check_authentication():
    """Check if user is authenticated"""
    if "auth_token" not in st.session_state:
        # Try to restore from localStorage
        st.markdown("""
        <script>
        const token = localStorage.getItem('auth_token');
        if (token) {
            window.parent.postMessage({type: 'auth_token', token: token}, '*');
        }
        </script>
        """, unsafe_allow_html=True)
        return False
    
    # Validate token with backend
    token = st.session_state.auth_token
    user_info = auth_service.get_current_user(token)
    
    if user_info:
        st.session_state.user_info = user_info
        return True
    else:
        # Token invalid, clear session
        auth_service.logout()
        return False