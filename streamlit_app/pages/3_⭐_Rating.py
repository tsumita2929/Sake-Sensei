"""
Sake Sensei - Rating & Feedback Page

Record and rate sake tasting experiences.
"""

import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.auth import show_login_dialog
from utils.backend_helper import BackendError, backend_client
from utils.gamification import update_user_progress
from utils.session import SessionManager
from utils.ui_components import load_custom_css, render_rating_stars
from utils.validation import sanitize_text_input, validate_sake_name, validate_tasting_record

st.set_page_config(page_title="Rating - Sake Sensei", page_icon="⭐", layout="wide")

# Load custom CSS
load_custom_css()


def main():
    """Main page function."""
    st.markdown('<div class="main-header">⭐ テイスティング記録</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">飲んだ日本酒を記録して、あなただけの酒ノートを作りましょう</div>',
        unsafe_allow_html=True,
    )

    # Check authentication
    if not SessionManager.is_authenticated():
        st.warning("⚠️ この機能を使用するにはログインが必要です")
        show_login_dialog()
        return

    st.markdown("---")

    # Check if coming from image recognition
    recognized_info = None
    if st.session_state.get("from_image_recognition") and st.session_state.get(
        "recognized_sake_info"
    ):
        recognized_info = st.session_state["recognized_sake_info"]
        st.success("✅ 画像認識からの情報が入力されています")
        st.info("💡 必要に応じて情報を修正してください")

        # Clear the flag after reading
        st.session_state["from_image_recognition"] = False

    # Tasting record form with enhanced UI
    with st.form("tasting_record"):
        st.markdown("### 📝 テイスティング記録")
        if not recognized_info:
            st.info("💡 詳しく記録するほど、より精度の高いおすすめが受けられます")

        col1, col2 = st.columns(2)

        with col1:
            sake_name = st.text_input(
                "日本酒の名前",
                value=recognized_info.get("sake_name", "") if recognized_info else "",
                placeholder="例: 獺祭 純米大吟醸",
            )
            brewery_name = st.text_input(
                "蔵元",
                value=recognized_info.get("brewery_name", "") if recognized_info else "",
                placeholder="例: 旭酒造",
            )

        with col2:
            tasting_date = st.date_input("飲んだ日", value=datetime.now())
            location = st.text_input("場所", placeholder="例: 自宅、○○居酒屋")

        # Show recognized additional info if available
        if recognized_info:
            with st.expander("📸 認識された追加情報", expanded=False):
                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    if recognized_info.get("sake_type"):
                        st.metric("タイプ", recognized_info["sake_type"])

                with col_b:
                    if recognized_info.get("rice_polish_ratio"):
                        st.metric("精米歩合", f"{recognized_info['rice_polish_ratio']}%")

                with col_c:
                    if recognized_info.get("alcohol_content"):
                        st.metric("アルコール度数", f"{recognized_info['alcohol_content']}%")

                if recognized_info.get("ingredients"):
                    st.markdown("**原料米**")
                    ingredients = recognized_info["ingredients"]
                    if isinstance(ingredients, list):
                        st.write(", ".join(ingredients))
                    else:
                        st.write(ingredients)

                if recognized_info.get("prefecture"):
                    st.markdown("**産地**")
                    st.write(recognized_info["prefecture"])

        st.markdown("#### 評価")

        col1, col2 = st.columns(2)

        with col1:
            overall_rating = st.slider("総合評価", 1, 5, 3, help="1=低い、5=高い")
            aroma_rating = st.slider("香り", 1, 5, 3)
            taste_rating = st.slider("味わい", 1, 5, 3)

        with col2:
            sweetness = st.slider("甘さ", 1, 5, 3, help="1=辛口、5=甘口")
            body = st.slider("ボディ", 1, 5, 3, help="1=軽い、5=重い")
            finish = st.slider("余韻", 1, 5, 3, help="1=短い、5=長い")

        st.markdown("#### テイスティングノート")

        col1, col2 = st.columns(2)

        with col1:
            aroma_notes = st.multiselect(
                "香りの特徴",
                [
                    "フルーティー",
                    "フローラル",
                    "ナッツ",
                    "米",
                    "柑橘",
                    "バナナ",
                    "リンゴ",
                    "メロン",
                    "ハーブ",
                ],
            )

        with col2:
            taste_notes = st.multiselect(
                "味の特徴",
                [
                    "クリーン",
                    "リッチ",
                    "クリーミー",
                    "シャープ",
                    "複雑",
                    "バランス良い",
                    "エレガント",
                ],
            )

        serving_temp = st.selectbox("飲んだ温度", ["冷酒", "花冷え", "常温", "ぬる燗", "熱燗"])

        paired_food = st.text_input("合わせた料理", placeholder="例: 刺身盛り合わせ")

        comments = st.text_area(
            "コメント", placeholder="感想や気づいたことを自由に記入してください", height=150
        )

        st.markdown("---")

        # Submit button
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            submit = st.form_submit_button("💾 保存", use_container_width=True, type="primary")

        if submit:
            # Validate sake name
            is_valid, error_msg = validate_sake_name(sake_name)
            if not is_valid:
                st.error(f"⚠️ {error_msg}")
                return

            # Collect tasting record
            record = {
                "sake_name": sanitize_text_input(sake_name, max_length=200),
                "brewery_name": sanitize_text_input(brewery_name, max_length=200),
                "tasting_date": tasting_date.isoformat(),
                "location": sanitize_text_input(location, max_length=200),
                "overall_rating": overall_rating,
                "aroma_rating": aroma_rating,
                "taste_rating": taste_rating,
                "sweetness": sweetness,
                "body": body,
                "finish": finish,
                "aroma_notes": aroma_notes,
                "taste_notes": taste_notes,
                "serving_temperature": serving_temp,
                "paired_food": sanitize_text_input(paired_food, max_length=200),
                "comments": sanitize_text_input(comments, max_length=1000),
                "user_id": SessionManager.get_user_id(),
                "tasted_at": tasting_date.isoformat(),
            }

            # Validate record
            is_valid, errors = validate_tasting_record(record)
            if not is_valid:
                st.error("⚠️ 入力内容にエラーがあります")
                for error in errors:
                    st.error(f"• {error}")
                return

            # Save to backend
            try:
                with st.spinner("保存中..."):
                    record_id = backend_client.create_tasting_record(record)
                    if record_id:
                        # Update gamification progress
                        user_id = SessionManager.get_user_id()
                        update_user_progress(
                            user_id, "tasting", {"sake_type": record.get("sake_type")}
                        )

                        st.balloons()
                        st.success("✅ テイスティング記録を保存しました！")
                        st.info(
                            f"💡 「History」ページで過去の記録を確認できます (ID: {record_id[:8]}...)"
                        )

                        # Display rating stars
                        st.markdown("**あなたの評価:**")
                        st.markdown(
                            render_rating_stars(float(overall_rating)), unsafe_allow_html=True
                        )

                        # Quick actions
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            if st.button("📚 履歴を見る", use_container_width=True):
                                st.switch_page("pages/5_📚_History.py")

                        with col2:
                            if st.button("🔄 別の日本酒を記録", use_container_width=True):
                                st.rerun()

                        with col3:
                            if st.button("🤖 おすすめを見る", use_container_width=True):
                                st.switch_page("pages/2_🤖_AI_Recommendations.py")

                        # Display saved record
                        with st.expander("保存された記録の詳細"):
                            st.json(record)
                    else:
                        st.warning("⚠️ 保存に失敗しました")
            except BackendError as e:
                st.error(f"❌ エラー: {str(e)}")


if __name__ == "__main__":
    main()
