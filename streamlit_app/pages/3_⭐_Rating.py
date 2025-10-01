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
from utils.session import SessionManager
from utils.validation import sanitize_text_input, validate_sake_name, validate_tasting_record

st.set_page_config(page_title="Rating - Sake Sensei", page_icon="⭐", layout="wide")


def main():
    """Main page function."""
    st.title("⭐ テイスティング記録")
    st.markdown("飲んだ日本酒を記録して、あなただけの酒ノートを作りましょう")

    # Check authentication
    if not SessionManager.is_authenticated():
        st.warning("⚠️ この機能を使用するにはログインが必要です")
        show_login_dialog()
        return

    st.markdown("---")

    # Tasting record form
    with st.form("tasting_record"):
        st.markdown("### 📝 テイスティング記録")

        col1, col2 = st.columns(2)

        with col1:
            sake_name = st.text_input("日本酒の名前", placeholder="例: 獺祭 純米大吟醸")
            brewery_name = st.text_input("蔵元", placeholder="例: 旭酒造")

        with col2:
            tasting_date = st.date_input("飲んだ日", value=datetime.now())
            location = st.text_input("場所", placeholder="例: 自宅、○○居酒屋")

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
                        st.success("✅ テイスティング記録を保存しました！")
                        st.info(
                            f"💡 「History」ページで過去の記録を確認できます (ID: {record_id[:8]}...)"
                        )

                        # Display saved record
                        with st.expander("保存された記録"):
                            st.json(record)
                    else:
                        st.warning("⚠️ 保存に失敗しました")
            except BackendError as e:
                st.error(f"❌ エラー: {str(e)}")


if __name__ == "__main__":
    main()
