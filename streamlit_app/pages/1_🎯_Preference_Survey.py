"""
Sake Sensei - Preference Survey Page

User preferences survey to personalize sake recommendations.
"""

import sys
from pathlib import Path

import streamlit as st

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.auth import show_login_dialog
from utils.backend_helper import BackendError, backend_client
from utils.gamification import update_user_progress
from utils.session import SessionManager
from utils.ui_components import load_custom_css, render_progress_bar
from utils.validation import sanitize_text_input, validate_preferences

st.set_page_config(page_title="Preference Survey - Sake Sensei", page_icon="🎯", layout="wide")

# Load custom CSS
load_custom_css()


def main():
    """Main page function."""
    st.markdown('<div class="main-header">🎯 プリファレンス調査</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">あなたの好みを教えてください。より精度の高いおすすめができます！</div>',
        unsafe_allow_html=True,
    )

    # Check authentication
    if not SessionManager.is_authenticated():
        st.warning("⚠️ この機能を使用するにはログインが必要です")
        show_login_dialog()
        return

    st.markdown("---")

    # Progress indicator
    current_prefs = SessionManager.get_preferences()
    completion_status = calculate_completion_status(current_prefs)

    st.markdown("### 📊 完了状況")
    render_progress_bar(completion_status / 100, label="プリファレンス設定", show_percentage=True)

    st.markdown("---")

    # Survey form with enhanced UX
    with st.form("preference_survey"):
        st.markdown("### 📋 好みのアンケート")
        st.info("💡 すべての項目に回答すると、より精度の高いおすすめが受けられます")

        # Sake type preference
        st.markdown("#### 1. 好きな日本酒のタイプ")
        sake_types = st.multiselect(
            "該当するものをすべて選択してください",
            [
                "純米酒",
                "純米吟醸",
                "純米大吟醸",
                "本醸造",
                "吟醸",
                "大吟醸",
                "特別純米",
                "特別本醸造",
            ],
            help="複数選択可能です",
        )

        st.markdown("#### 2. 味わいの好み")
        col1, col2 = st.columns(2)

        with col1:
            sweetness = st.select_slider(
                "甘辛度",
                options=[
                    "とても甘口",
                    "甘口",
                    "やや甘口",
                    "中口",
                    "やや辛口",
                    "辛口",
                    "とても辛口",
                ],
                value="中口",
            )

        with col2:
            body = st.select_slider(
                "ボディ",
                options=[
                    "とても軽い",
                    "軽い",
                    "やや軽い",
                    "中程度",
                    "やや重い",
                    "重い",
                    "とても重い",
                ],
                value="中程度",
            )

        st.markdown("#### 3. 香りの好み")
        aroma_preference = st.multiselect(
            "好きな香りのタイプ",
            ["フルーティー", "フローラル", "ナッツ", "米", "柑橘", "バナナ", "リンゴ", "メロン"],
            help="複数選択可能です",
        )

        st.markdown("#### 4. 飲用シーン")
        drinking_scene = st.multiselect(
            "よく飲むシーン",
            ["食事中", "食前酒", "食後酒", "一人で", "友人と", "家族と", "特別な日"],
            help="複数選択可能です",
        )

        st.markdown("#### 5. 好きな料理との組み合わせ")
        food_pairing = st.multiselect(
            "よく合わせる料理",
            [
                "刺身",
                "寿司",
                "焼き魚",
                "天ぷら",
                "鍋料理",
                "焼き鳥",
                "チーズ",
                "和食全般",
                "洋食",
                "中華",
            ],
            help="複数選択可能です",
        )

        st.markdown("#### 6. 温度の好み")
        temperature_preference = st.multiselect(
            "好きな飲み方",
            [
                "冷酒（5-10℃）",
                "花冷え（10-15℃）",
                "常温（15-20℃）",
                "ぬる燗（40-45℃）",
                "熱燗（50-55℃）",
            ],
            help="複数選択可能です",
        )

        st.markdown("#### 7. 価格帯")
        price_range = st.select_slider(
            "通常購入する価格帯（720ml あたり）",
            options=[
                "～1,000円",
                "1,000～2,000円",
                "2,000～3,000円",
                "3,000～5,000円",
                "5,000円～",
            ],
            value="2,000～3,000円",
        )

        st.markdown("#### 8. 日本酒の経験")
        col1, col2 = st.columns(2)

        with col1:
            experience_level = st.selectbox(
                "日本酒を飲む頻度",
                ["初めて", "月に1回程度", "月に2-3回", "週に1回以上", "ほぼ毎日"],
            )

        with col2:
            knowledge_level = st.selectbox(
                "日本酒の知識レベル",
                ["初心者", "少し知っている", "ある程度知っている", "詳しい", "専門家レベル"],
            )

        st.markdown("#### 9. その他の好み")
        other_preferences = st.text_area(
            "その他、好みや要望があれば記入してください",
            placeholder="例: スパークリング日本酒が好き、地酒を探している、など",
            height=100,
        )

        st.markdown("---")

        # Submit button
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            submit = st.form_submit_button("💾 保存", use_container_width=True, type="primary")

        if submit:
            # Collect preferences
            preferences = {
                "sake_types": sake_types,
                "sweetness": sweetness,
                "body": body,
                "aroma_preference": aroma_preference,
                "drinking_scene": drinking_scene,
                "food_pairing": food_pairing,
                "temperature_preference": temperature_preference,
                "price_range": price_range,
                "experience_level": experience_level,
                "knowledge_level": knowledge_level,
                "other_preferences": sanitize_text_input(other_preferences, max_length=500),
            }

            # Validate preferences
            is_valid, errors = validate_preferences(preferences)
            if not is_valid:
                st.error("⚠️ 入力内容にエラーがあります")
                for error in errors:
                    st.error(f"• {error}")
                return

            # Store in session
            SessionManager.set_preferences(preferences)

            # Update gamification progress
            user_id = SessionManager.get_user_id()
            update_user_progress(user_id, "preference_set")

            # Save to backend
            try:
                with st.spinner("保存中..."):
                    success = backend_client.save_user_preferences(preferences)
                    if success:
                        st.balloons()
                        st.success("✅ プリファレンスを保存しました！")
                        st.info(
                            "💡 「Recommendations」ページでおすすめの日本酒を見ることができます"
                        )
                    else:
                        st.warning("⚠️ 保存に失敗しました。セッションには保存されています。")
            except BackendError as e:
                st.error(f"❌ エラー: {str(e)}")
                st.info("💡 セッションには保存されています")

    # Show current preferences if exists
    current_prefs = SessionManager.get_preferences()
    if current_prefs:
        st.markdown("---")
        st.markdown("### 📊 現在の設定")

        with st.expander("設定内容を表示"):
            st.json(current_prefs)


def calculate_completion_status(preferences: dict | None) -> float:
    """
    Calculate completion percentage of preferences.

    Args:
        preferences: User preferences dictionary

    Returns:
        Completion percentage (0-100)
    """
    if not preferences:
        return 0.0

    total_fields = 9  # Total number of preference categories
    completed_fields = 0

    if preferences.get("sake_types"):
        completed_fields += 1
    if preferences.get("sweetness"):
        completed_fields += 1
    if preferences.get("body"):
        completed_fields += 1
    if preferences.get("aroma_preference"):
        completed_fields += 1
    if preferences.get("drinking_scene"):
        completed_fields += 1
    if preferences.get("food_pairing"):
        completed_fields += 1
    if preferences.get("temperature_preference"):
        completed_fields += 1
    if preferences.get("price_range"):
        completed_fields += 1
    if preferences.get("experience_level"):
        completed_fields += 1

    return (completed_fields / total_fields) * 100


if __name__ == "__main__":
    main()
