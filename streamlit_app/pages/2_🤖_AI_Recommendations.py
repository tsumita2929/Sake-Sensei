"""
Sake Sensei - AI Recommendations Page

AI-powered sake recommendations powered by AgentCore.
"""

import sys
from pathlib import Path

import streamlit as st

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.agent_client import render_agent_chat
from components.auth import show_login_dialog
from components.sake_card import render_sake_list
from utils.backend_helper import BackendError, backend_client
from utils.session import SessionManager

st.set_page_config(page_title="AI Recommendations - Sake Sensei", page_icon="🤖", layout="wide")


def main():
    """Main page function."""
    st.title("🤖 AI おすすめ日本酒")
    st.markdown("Sake Sensei AI があなたにぴったりの日本酒をご提案します")

    # Check authentication
    if not SessionManager.is_authenticated():
        st.warning("⚠️ この機能を使用するにはログインが必要です")
        show_login_dialog()
        return

    st.markdown("---")

    # Check if preferences are set
    preferences = SessionManager.get_preferences()

    if not preferences:
        st.info("""
        💡 **プリファレンス調査がまだ完了していません**

        より精度の高いおすすめを受け取るために、
        まず「Preference Survey」ページで好みを登録してください。
        """)

        if st.button("🎯 プリファレンス調査へ", type="primary"):
            st.switch_page("pages/1_🎯_Preference_Survey.py")

        st.markdown("---")
        st.markdown("### それでも続ける")
        st.markdown("プリファレンス未登録でも AI に質問できます")

    # Recommendation options
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 🎲 クイックおすすめ")
        st.markdown("ボタンをクリックして即座におすすめを取得")

    with col2:
        if st.button("おすすめを取得", use_container_width=True, type="primary"):
            st.session_state["get_recommendations"] = True

    if st.session_state.get("get_recommendations", False):
        with st.spinner("AI が考え中..."):
            try:
                # Get user preferences
                preferences = SessionManager.get_preferences()

                # Call recommendation Lambda via AgentCore
                recommendations = backend_client.get_recommendations(preferences, limit=5)

                if recommendations:
                    st.markdown("#### おすすめの日本酒")
                    st.success(f"✅ {len(recommendations)}件のおすすめを取得しました")

                    render_sake_list(recommendations, show_details=True)
                else:
                    st.warning("⚠️ おすすめが見つかりませんでした")
                    st.info(
                        "💡 「Preference Survey」で好みを登録すると、より精度の高いおすすめを取得できます"
                    )

            except BackendError as e:
                st.error(f"❌ エラー: {str(e)}")
                st.info("💡 しばらく経ってから再度お試しください")
            except Exception as e:
                st.error(f"❌ 予期しないエラーが発生しました: {str(e)}")

    st.markdown("---")

    # Agent chat interface
    st.markdown("### 💬 AI と対話")
    st.markdown("Sake Sensei AI に自由に質問できます")

    # Render agent chat component
    render_agent_chat()


if __name__ == "__main__":
    main()
