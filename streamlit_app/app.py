"""
Sake Sensei - Main Streamlit Application

AI-powered sake recommendation system powered by Amazon Bedrock AgentCore.
"""

import streamlit as st

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

    # Check authentication status
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
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

        # Show login/signup forms if requested
        if st.session_state.get("show_login", False):
            show_login_form()

        if st.session_state.get("show_signup", False):
            show_signup_form()


def show_login_form():
    """Display login form."""
    st.markdown("---")
    st.markdown("### ログイン")

    with st.form("login_form"):
        email = st.text_input("メールアドレス", placeholder="your.email@example.com")
        password = st.text_input("パスワード", type="password")

        col1, col2 = st.columns([3, 1])
        with col2:
            submit = st.form_submit_button("ログイン", use_container_width=True)

        if submit:
            if email and password:
                # TODO: Implement Cognito authentication
                st.info("🚧 Cognito認証機能は実装中です")
                # For now, allow mock login
                if email == "demo@example.com":
                    st.session_state.authenticated = True
                    st.session_state.user_id = "demo-user"
                    st.session_state.user_email = email
                    st.success("✅ ログイン成功！")
                    st.rerun()
                else:
                    st.error("❌ 認証に失敗しました")
            else:
                st.warning("⚠️ メールアドレスとパスワードを入力してください")


def show_signup_form():
    """Display signup form."""
    st.markdown("---")
    st.markdown("### 新規登録")

    with st.form("signup_form"):
        email = st.text_input("メールアドレス", placeholder="your.email@example.com")
        password = st.text_input("パスワード", type="password")
        password_confirm = st.text_input("パスワード（確認）", type="password")
        name = st.text_input("お名前", placeholder="山田 太郎")

        col1, col2 = st.columns([3, 1])
        with col2:
            submit = st.form_submit_button("登録", use_container_width=True)

        if submit:
            if email and password and password_confirm and name:
                if password != password_confirm:
                    st.error("❌ パスワードが一致しません")
                else:
                    # TODO: Implement Cognito signup
                    st.info("🚧 Cognito登録機能は実装中です")
                    st.info("デモ用: demo@example.com でログインしてください")
            else:
                st.warning("⚠️ すべての項目を入力してください")


def show_main_app():
    """Display main application for authenticated users."""

    # Sidebar
    with st.sidebar:
        st.markdown("### 👤 ユーザー情報")
        st.write(f"**Email**: {st.session_state.get('user_email', 'Unknown')}")
        st.write(f"**User ID**: {st.session_state.get('user_id', 'Unknown')}")

        st.markdown("---")

        st.markdown("### 📱 メニュー")
        st.info("各機能はサイドバーのページから選択できます")

        st.markdown("---")

        if st.button("🚪 ログアウト", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.user_email = None
            st.rerun()

    # Main content
    st.markdown("## 🏠 ホーム")

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
