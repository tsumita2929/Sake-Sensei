"""
Sake Sensei - History Page

View and manage tasting history and statistics.
"""

import io
import json
import sys
from datetime import datetime
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.auth import show_login_dialog
from utils.backend_helper import BackendError, backend_client
from utils.session import SessionManager

st.set_page_config(page_title="History - Sake Sensei", page_icon="📚", layout="wide")


def main():
    """Main page function."""
    st.title("📚 テイスティング履歴")
    st.markdown("あなたの日本酒の旅を振り返りましょう")

    # Check authentication
    if not SessionManager.is_authenticated():
        st.warning("⚠️ この機能を使用するにはログインが必要です")
        show_login_dialog()
        return

    st.markdown("---")

    # Statistics
    st.markdown("### 📊 統計情報")

    col1, col2, col3, col4 = st.columns(4)

    # Get statistics from backend
    try:
        stats = backend_client.get_tasting_statistics()

        with col1:
            total_records = stats.get("total_records", 0)
            monthly_records = stats.get("monthly_records", 0)
            st.metric("試飲記録", f"{total_records} 本", delta=f"今月 +{monthly_records}")

        with col2:
            favorites = stats.get("favorites_count", 0)
            st.metric("お気に入り", f"{favorites} 本")

        with col3:
            breweries_explored = stats.get("breweries_explored", 0)
            st.metric("探索した蔵", f"{breweries_explored} 軒")

        with col4:
            avg_rating = stats.get("average_rating", 0.0)
            st.metric("平均評価", f"{avg_rating:.1f} ⭐")

    except (BackendError, Exception):
        with col1:
            st.metric("試飲記録", "0 本", delta="今月 +0")
        with col2:
            st.metric("お気に入り", "0 本")
        with col3:
            st.metric("探索した蔵", "0 軒")
        with col4:
            st.metric("平均評価", "0.0 ⭐")

    st.markdown("---")

    # Filter options
    st.markdown("### 🔍 フィルター")

    col1, col2, col3 = st.columns(3)

    with col1:
        # TODO: Implement date range filtering
        _date_range = st.selectbox(
            "期間", ["すべて", "今週", "今月", "過去3ヶ月", "過去1年", "カスタム"]
        )

    with col2:
        # TODO: Implement sake type filtering
        _sake_type_filter = st.multiselect(
            "日本酒タイプ", ["純米酒", "純米吟醸", "純米大吟醸", "本醸造", "吟醸", "大吟醸"]
        )

    with col3:
        # TODO: Implement rating filtering
        _rating_filter = st.select_slider(
            "評価",
            options=["すべて", "1⭐以上", "2⭐以上", "3⭐以上", "4⭐以上", "5⭐のみ"],
            value="すべて",
        )

    st.markdown("---")

    # Statistics Graphs
    st.markdown("### 📈 統計グラフ")

    # Get tasting records for graphs
    try:
        records = backend_client.get_tasting_records(limit=100)

        if records and len(records) > 0:
            # Create DataFrame for visualization
            df = pd.DataFrame(records)

            # Graph tabs
            tab1, tab2, tab3 = st.tabs(["📊 評価分布", "🍶 タイプ別", "📅 時系列"])

            with tab1:
                # Rating distribution chart
                if "overall_rating" in df.columns or "rating" in df.columns:
                    rating_col = "overall_rating" if "overall_rating" in df.columns else "rating"
                    rating_counts = df[rating_col].value_counts().reset_index()
                    rating_counts.columns = ["rating", "count"]

                    chart = (
                        alt.Chart(rating_counts)
                        .mark_bar()
                        .encode(
                            x=alt.X("rating:O", title="評価"),
                            y=alt.Y("count:Q", title="記録数"),
                            color=alt.Color(
                                "rating:O",
                                scale=alt.Scale(scheme="goldorange"),
                                legend=None,
                            ),
                            tooltip=["rating", "count"],
                        )
                        .properties(width=600, height=400, title="評価の分布")
                    )
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("評価データがありません")

            with tab2:
                # Sake type distribution
                if "sake_type" in df.columns or "type" in df.columns:
                    type_col = "sake_type" if "sake_type" in df.columns else "type"
                    type_counts = df[type_col].value_counts().reset_index()
                    type_counts.columns = ["type", "count"]

                    chart = (
                        alt.Chart(type_counts)
                        .mark_arc(innerRadius=50)
                        .encode(
                            theta=alt.Theta("count:Q"),
                            color=alt.Color("type:N", legend=alt.Legend(title="タイプ")),
                            tooltip=["type", "count"],
                        )
                        .properties(width=400, height=400, title="日本酒タイプの分布")
                    )
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("タイプ別データがありません")

            with tab3:
                # Timeline chart
                if "tasting_date" in df.columns or "created_at" in df.columns:
                    date_col = "tasting_date" if "tasting_date" in df.columns else "created_at"

                    # Convert to datetime
                    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

                    # Group by date
                    daily_counts = df.groupby(df[date_col].dt.date).size().reset_index()
                    daily_counts.columns = ["date", "count"]

                    chart = (
                        alt.Chart(daily_counts)
                        .mark_line(point=True)
                        .encode(
                            x=alt.X("date:T", title="日付"),
                            y=alt.Y("count:Q", title="テイスティング数"),
                            tooltip=["date", "count"],
                        )
                        .properties(width=600, height=400, title="テイスティング履歴の推移")
                    )
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("日付データがありません")

        else:
            st.info("グラフを表示するにはテイスティング記録が必要です")

    except (BackendError, Exception) as e:
        st.warning(f"グラフの読み込みに失敗しました: {str(e)}")

    st.markdown("---")

    # Tasting records
    st.markdown("### 📝 テイスティング記録")

    # Fetch records from backend
    if st.button("データをロード"):
        with st.spinner("データを読み込み中..."):
            try:
                records = backend_client.get_tasting_records(limit=50)

                if records:
                    st.success(f"✅ {len(records)}件の記録を読み込みました")

                    for record in records:
                        sake_name = record.get("sake_name", "不明")
                        tasting_date = record.get("tasting_date", record.get("tasted_at", "不明"))

                        with st.expander(f"{sake_name} - {tasting_date}"):
                            col1, col2 = st.columns([2, 1])

                            with col1:
                                st.markdown(f"**{sake_name}**")
                                if record.get("brewery_name"):
                                    st.markdown(f"蔵元: {record['brewery_name']}")
                                st.markdown(f"日付: {tasting_date}")

                                if record.get("location"):
                                    st.markdown(f"場所: {record['location']}")

                            with col2:
                                overall_rating = record.get("overall_rating", 0)
                                st.metric("総合評価", f"{overall_rating} ⭐")

                            # Detailed ratings
                            if any(
                                key in record
                                for key in [
                                    "aroma_rating",
                                    "taste_rating",
                                    "sweetness",
                                    "body",
                                    "finish",
                                ]
                            ):
                                st.markdown("**詳細評価**")
                                col_a, col_b, col_c = st.columns(3)

                                with col_a:
                                    if record.get("aroma_rating"):
                                        st.write(f"香り: {record['aroma_rating']}/5")
                                    if record.get("taste_rating"):
                                        st.write(f"味わい: {record['taste_rating']}/5")

                                with col_b:
                                    if record.get("sweetness"):
                                        st.write(f"甘さ: {record['sweetness']}/5")
                                    if record.get("body"):
                                        st.write(f"ボディ: {record['body']}/5")

                                with col_c:
                                    if record.get("finish"):
                                        st.write(f"余韻: {record['finish']}/5")

                            # Tasting notes
                            if record.get("aroma_notes") or record.get("taste_notes"):
                                st.markdown("**テイスティングノート**")
                                if record.get("aroma_notes"):
                                    st.write(f"香り: {', '.join(record['aroma_notes'])}")
                                if record.get("taste_notes"):
                                    st.write(f"味: {', '.join(record['taste_notes'])}")

                            if record.get("comments"):
                                st.markdown("**コメント**")
                                st.write(record["comments"])

                            # Action buttons
                            col_a, col_b, col_c = st.columns(3)

                            with col_a:
                                record_id = record.get("record_id", record.get("id", ""))
                                if st.button("✏️ 編集", key=f"edit_{record_id}"):
                                    st.info("編集機能は実装予定です")

                            with col_b:
                                if st.button("🗑️ 削除", key=f"delete_{record_id}"):
                                    st.warning("削除機能は実装予定です")

                            with col_c:
                                if st.button("📤 共有", key=f"share_{record_id}"):
                                    st.info("共有機能は実装予定です")
                else:
                    st.info(
                        """
                    📝 **テイスティング記録がまだありません**

                    「Rating」ページで飲んだ日本酒を記録してみましょう！
                    """
                    )

                    if st.button("⭐ テイスティング記録へ", type="primary"):
                        st.switch_page("pages/3_⭐_Rating.py")

            except BackendError as e:
                st.error(f"❌ エラー: {str(e)}")
            except Exception as e:
                st.error(f"❌ 予期しないエラーが発生しました: {str(e)}")

    st.markdown("---")

    # Export options
    st.markdown("### 📤 エクスポート")

    try:
        records = backend_client.get_tasting_records(limit=1000)

        if records and len(records) > 0:
            col1, col2, col3 = st.columns(3)

            with col1:
                # CSV Export
                df = pd.DataFrame(records)
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
                csv_data = csv_buffer.getvalue()

                st.download_button(
                    label="📄 CSV エクスポート",
                    data=csv_data,
                    file_name=f"sake_tasting_history_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            with col2:
                # JSON Export
                json_data = json.dumps(records, ensure_ascii=False, indent=2)

                st.download_button(
                    label="📋 JSON エクスポート",
                    data=json_data,
                    file_name=f"sake_tasting_history_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json",
                    use_container_width=True,
                )

            with col3:
                # Summary Report
                summary = {
                    "総テイスティング数": len(records),
                    "平均評価": df["overall_rating"].mean()
                    if "overall_rating" in df.columns
                    else 0,
                    "最高評価": df["overall_rating"].max() if "overall_rating" in df.columns else 0,
                    "最低評価": df["overall_rating"].min() if "overall_rating" in df.columns else 0,
                    "エクスポート日時": datetime.now().isoformat(),
                }

                summary_text = "\n".join([f"{k}: {v}" for k, v in summary.items()])

                st.download_button(
                    label="📊 サマリーレポート",
                    data=summary_text,
                    file_name=f"sake_summary_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

            st.success(f"✅ {len(records)}件の記録をエクスポート可能")

        else:
            st.info("エクスポートできる記録がありません")

    except (BackendError, Exception) as e:
        st.warning(f"エクスポート機能の準備に失敗しました: {str(e)}")


if __name__ == "__main__":
    main()
