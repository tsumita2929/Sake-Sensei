"""
Sake Sensei - Main Streamlit Application

AI-powered sake recommendation system powered by Amazon Bedrock AgentCore.
"""

import streamlit as st
from components.agent_client import render_agent_chat
from components.auth import CognitoAuth
from utils.session import SessionManager

# Configure page
st.set_page_config(
    page_title="Sake Sensei 🍶",
    page_icon="🍶",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "# Sake Sensei\nAI-powered sake recommendation system"},
)

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #2E4057;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #5C6B73;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sake-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #C9ADA7;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #e7f3ff;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #0066cc;
        margin: 1rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


def main():
    """Main application entry point."""

    # Header
    st.markdown('<div class="main-header">🍶 Sake Sensei</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">あなたにぴったりの日本酒を AI がご提案します</div>',
        unsafe_allow_html=True,
    )

    # Check authentication status using SessionManager
    if not SessionManager.is_authenticated():
        show_welcome_page()
    else:
        show_main_app()


def show_welcome_page():
    """Display welcome page for unauthenticated users."""

    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("## ようこそ Sake Sensei へ！")

        st.markdown("""
        ### 🎯 Sake Sensei でできること

        **1. パーソナライズされた日本酒推薦**
        - あなたの好みに合わせた日本酒を AI が提案
        - 味わい、香り、価格帯から最適な一本を発見

        **2. テイスティング記録**
        - 飲んだ日本酒の評価を記録
        - 自分だけの酒ノートを作成

        **3. ラベル認識**
        - 写真を撮るだけで日本酒の情報を取得
        - 銘柄、蔵元、特徴を即座に確認

        **4. 酒蔵探索**
        - 全国の酒蔵情報をチェック
        - 歴史や特徴を学ぶ
        """)

        st.markdown("---")

        st.markdown(
            """
        <div class="info-box">
        <strong>🚀 はじめるには</strong><br>
        サイドバーから「ログイン」を選択してください。<br>
        初めての方は「新規登録」からアカウントを作成できます。
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Authentication buttons
        st.markdown("### 認証")

        col_login, col_signup = st.columns(2)

        with col_login:
            if st.button("🔐 ログイン", use_container_width=True, type="primary"):
                st.session_state.show_login = True
                st.rerun()

        with col_signup:
            if st.button("✨ 新規登録", use_container_width=True):
                st.session_state.show_signup = True
                st.rerun()

        # Show login/signup/confirmation forms if requested
        if st.session_state.get("show_login", False):
            show_login_form()

        if st.session_state.get("show_signup", False):
            show_signup_form()

        if st.session_state.get("pending_confirmation_email"):
            show_confirmation_form()


def show_login_form():
    """Display login form."""
    auth = CognitoAuth()

    st.markdown("---")
    st.markdown("### 🔐 ログイン")

    # Show error message if exists
    if "login_error" in st.session_state:
        st.error(st.session_state["login_error"])
        del st.session_state["login_error"]

    with st.form("login_form"):
        email = st.text_input("メールアドレス", placeholder="your.email@example.com")
        password = st.text_input("パスワード", type="password")

        col1, col2, col3 = st.columns([2, 1, 1])
        with col2:
            cancel = st.form_submit_button("キャンセル", use_container_width=True)
        with col3:
            submit = st.form_submit_button("ログイン", use_container_width=True, type="primary")

        if cancel:
            st.session_state.show_login = False
            st.rerun()

        if submit:
            if email and password:
                with st.spinner("認証中..."):
                    success, message, tokens = auth.sign_in(email, password)

                    if success and tokens:
                        # Extract user info
                        user_info = tokens.get("user_info", {})
                        user_id = user_info.get("sub", email)
                        user_name = user_info.get("name", "")

                        # Store in session
                        SessionManager.login(
                            user_id=user_id,
                            email=email,
                            name=user_name,
                            access_token=tokens["access_token"],
                            id_token=tokens["id_token"],
                            refresh_token=tokens.get("refresh_token"),
                        )

                        # Clear login form state
                        st.session_state.show_login = False

                        # Rerun immediately without showing success message
                        st.rerun()
                    else:
                        st.session_state["login_error"] = message
                        st.rerun()
            else:
                st.warning("⚠️ メールアドレスとパスワードを入力してください")


def show_signup_form():
    """Display signup form."""
    auth = CognitoAuth()

    st.markdown("---")
    st.markdown("### ✨ 新規登録")

    with st.form("signup_form"):
        name = st.text_input("お名前", placeholder="山田 太郎")
        email = st.text_input("メールアドレス", placeholder="your.email@example.com")
        password = st.text_input("パスワード (12文字以上)", type="password")
        password_confirm = st.text_input("パスワード（確認）", type="password")

        st.info("💡 パスワード要件: 12文字以上、大文字・小文字・数字・記号を含む")

        col1, col2, col3 = st.columns([2, 1, 1])
        with col2:
            cancel = st.form_submit_button("キャンセル", use_container_width=True)
        with col3:
            submit = st.form_submit_button("登録", use_container_width=True, type="primary")

        if cancel:
            st.session_state.show_signup = False
            st.rerun()

        if submit:
            if name and email and password and password_confirm:
                if password != password_confirm:
                    st.error("❌ パスワードが一致しません")
                elif len(password) < 12:
                    st.error("❌ パスワードは12文字以上である必要があります")
                else:
                    with st.spinner("登録中..."):
                        success, message = auth.sign_up(email, password, name)

                        if success:
                            st.success(message)
                            st.session_state["pending_confirmation_email"] = email
                            st.session_state.show_signup = False
                            st.rerun()
                        else:
                            st.error(message)
            else:
                st.warning("⚠️ すべての項目を入力してください")


def show_confirmation_form():
    """Display confirmation code input form."""
    auth = CognitoAuth()
    email = st.session_state.get("pending_confirmation_email", "")

    st.markdown("---")
    st.markdown("### 📧 メール確認")

    # Show resend confirmation message if exists
    if "resend_message" in st.session_state:
        if st.session_state["resend_message"]["success"]:
            st.success(st.session_state["resend_message"]["text"])
        else:
            st.error(st.session_state["resend_message"]["text"])
        del st.session_state["resend_message"]

    with st.form("confirmation_form"):
        st.info(f"📨 {email} に送信された確認コードを入力してください")

        confirmation_code = st.text_input("確認コード (6桁)", placeholder="123456", max_chars=6)

        col1, col2, col3 = st.columns([2, 1, 1])
        with col2:
            cancel = st.form_submit_button("キャンセル", use_container_width=True)
        with col3:
            submit = st.form_submit_button("確認", use_container_width=True, type="primary")

        if cancel:
            del st.session_state["pending_confirmation_email"]
            st.rerun()

        if submit:
            if confirmation_code:
                with st.spinner("確認中..."):
                    success, message = auth.confirm_sign_up(email, confirmation_code)

                    if success:
                        st.success(message)
                        del st.session_state["pending_confirmation_email"]
                        st.session_state.show_login = True
                        st.rerun()
                    else:
                        st.error(message)
            else:
                st.warning("⚠️ 確認コードを入力してください")

    # Resend button outside the form
    if st.button("🔄 確認コードを再送信", use_container_width=False):
        with st.spinner("再送信中..."):
            success, message = auth.resend_confirmation_code(email)
            st.session_state["resend_message"] = {"success": success, "text": message}
            st.rerun()


def show_ai_chat_section():
    """Display AI chat section for asking questions to Sake Sensei."""
    try:
        st.markdown("---")
        st.markdown("### 🤖 Sake Sensei に質問")

        # Use agent_client component for AI chat
        render_agent_chat()

    except Exception as e:
        st.error(f"AI Chatセクションの表示中にエラーが発生しました: {str(e)}")


def show_main_app():
    """Display main application for authenticated users."""
    auth = CognitoAuth()

    # Sidebar
    with st.sidebar:
        st.markdown("### 👤 ユーザー情報")
        user_info = SessionManager.get_user_info()
        st.write(f"**名前**: {user_info.get('name', '未設定')}")
        st.write(f"**Email**: {user_info.get('email', 'Unknown')}")

        st.markdown("---")

        st.markdown("### 📱 メニュー")
        st.info("各機能はサイドバーのページから選択できます")

        st.markdown("---")

        if st.button("🚪 ログアウト", use_container_width=True):
            access_token = st.session_state.get("access_token")
            if access_token:
                auth.sign_out(access_token)
            SessionManager.logout()
            st.rerun()

    # Main content
    st.markdown("## 🏠 ホーム")

    # AI Chat Section
    show_ai_chat_section()

    st.markdown("""
    ### ようこそ、Sake Sensei へ！

    左のサイドバーから各機能をご利用いただけます：
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        #### 🎯 おすすめ機能

        - **Preference Survey** - あなたの好みを教えてください
        - **Recommendations** - AI が日本酒を提案します
        - **Rating** - 飲んだ日本酒を評価しましょう
        """)

    with col2:
        st.markdown("""
        #### 📸 便利機能

        - **Image Recognition** - ラベル写真から情報を取得
        - **History** - あなたのテイスティング履歴
        """)

    st.markdown("---")

    # Quick stats (placeholder)
    st.markdown("### 📊 あなたの統計")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("試飲記録", "0 本")

    with col2:
        st.metric("お気に入り", "0 本")

    with col3:
        st.metric("探索した蔵", "0 軒")

    with col4:
        st.metric("おすすめ取得", "0 回")

    st.markdown("---")

    st.markdown(
        """
    <div class="info-box">
    <strong>💡 ヒント</strong><br>
    まずは「Preference Survey」であなたの好みを登録すると、<br>
    より精度の高いおすすめを受け取ることができます！
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
