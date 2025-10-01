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
from utils.gamification import update_user_progress
from utils.session import SessionManager
from utils.ui_components import load_custom_css

st.set_page_config(page_title="AI Recommendations - Sake Sensei", page_icon="🤖", layout="wide")

# Load custom CSS
load_custom_css()


def main():
    """Main page function."""
    st.markdown('<div class="main-header">🤖 AI おすすめ日本酒</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Sake Sensei AI があなたにぴったりの日本酒をご提案します</div>',
        unsafe_allow_html=True,
    )

    # Check authentication
    if not SessionManager.is_authenticated():
        st.warning("⚠️ この機能を使用するにはログインが必要です")
        show_login_dialog()
        return

    st.markdown("---")

    # Check if preferences are set
    preferences = SessionManager.get_preferences()

    if not preferences:
        st.markdown(
            """
        <div class="info-box">
            <h4>💡 プリファレンス調査がまだ完了していません</h4>
            <p>より精度の高いおすすめを受け取るために、まず「Preference Survey」ページで好みを登録してください。</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🎯 プリファレンス調査へ", type="primary", use_container_width=True):
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
        with st.spinner("🤖 AI が最適な日本酒を探しています..."):
            try:
                # Get user preferences
                preferences = SessionManager.get_preferences()

                # Call recommendation Lambda via AgentCore
                recommendations = backend_client.get_recommendations(preferences, limit=5)

                if recommendations:
                    # Update gamification progress
                    user_id = SessionManager.get_user_id()
                    update_user_progress(user_id, "recommendation")

                    st.markdown("#### ✨ おすすめの日本酒")
                    st.success(f"✅ {len(recommendations)}件のおすすめを取得しました")

                    # Add filtering options
                    col1, col2 = st.columns([2, 1])

                    with col2:
                        sort_by = st.selectbox(
                            "並び替え",
                            ["おすすめ順", "価格: 安い順", "価格: 高い順", "精米歩合: 低い順"],
                            key="sort_recommendations",
                        )

                    # Sort recommendations based on selection
                    sorted_recommendations = sort_recommendations(recommendations, sort_by)

                    render_sake_list(sorted_recommendations, show_details=True)

                    # Quick actions
                    st.markdown("---")
                    st.markdown("### 🎯 次のステップ")

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if st.button("🔄 別のおすすめを取得", use_container_width=True):
                            st.session_state["get_recommendations"] = True
                            st.rerun()

                    with col2:
                        if st.button("⭐ テイスティング記録へ", use_container_width=True):
                            st.switch_page("pages/3_⭐_Rating.py")

                    with col3:
                        if st.button("🎯 好みを更新", use_container_width=True):
                            st.switch_page("pages/1_🎯_Preference_Survey.py")
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


def sort_recommendations(recommendations: list, sort_by: str) -> list:
    """
    Sort recommendations based on criteria.

    Args:
        recommendations: List of sake recommendations
        sort_by: Sort criteria

    Returns:
        Sorted list of recommendations
    """
    if sort_by == "おすすめ順":
        return recommendations

    try:
        if sort_by == "価格: 安い順":
            return sorted(recommendations, key=lambda x: extract_price(x.get("price_range", "")))
        elif sort_by == "価格: 高い順":
            return sorted(
                recommendations, key=lambda x: extract_price(x.get("price_range", "")), reverse=True
            )
        elif sort_by == "精米歩合: 低い順":
            return sorted(
                recommendations,
                key=lambda x: x.get("rice_polish_ratio", 100)
                if x.get("rice_polish_ratio") != "N/A"
                else 100,
            )
    except (KeyError, ValueError, TypeError):
        pass

    return recommendations


def extract_price(price_range: str) -> int:
    """
    Extract numeric price from price range string.

    Args:
        price_range: Price range string (e.g., "2,000～3,000円")

    Returns:
        Numeric price value
    """
    if not price_range or price_range == "N/A":
        return 999999

    # Extract first number from range
    import re

    match = re.search(r"(\d+,?\d*)", price_range)
    if match:
        return int(match.group(1).replace(",", ""))

    return 999999


if __name__ == "__main__":
    main()
