"""
Sake Sensei - Image Recognition Page

Recognize sake information from label photos using Claude vision model.
"""

import base64
import io
import sys
from pathlib import Path

import streamlit as st
from PIL import Image

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.auth import show_login_dialog
from utils.backend_helper import BackendError, backend_client
from utils.config import config
from utils.session import SessionManager
from utils.validation import validate_image_file

st.set_page_config(page_title="Image Recognition - Sake Sensei", page_icon="📸", layout="wide")


def main():
    """Main page function."""
    st.title("📸 ラベル認識")
    st.markdown("日本酒のラベル写真をアップロードして、銘柄情報を取得しましょう")

    # Check authentication
    if not SessionManager.is_authenticated():
        st.warning("⚠️ この機能を使用するにはログインが必要です")
        show_login_dialog()
        return

    # Check feature flag
    if not config.FEATURE_IMAGE_RECOGNITION:
        st.warning("⚠️ この機能は現在無効になっています")
        return

    st.markdown("---")

    st.markdown("""
    ### 📋 使い方

    1. **写真を撮影** - 日本酒のラベルを正面から撮影
    2. **アップロード** - 下のボタンから写真を選択
    3. **認識** - AI がラベルから情報を抽出
    4. **確認** - 認識結果を確認し、必要に応じて修正

    #### 📌 ヒント
    - ラベル全体が写るように撮影してください
    - 明るい場所で撮影すると認識精度が上がります
    - ピントが合った鮮明な写真を使用してください
    """)

    st.markdown("---")

    # File upload
    uploaded_file = st.file_uploader(
        "📷 ラベル写真をアップロード",
        type=["jpg", "jpeg", "png", "webp"],
        help="JPG, PNG, WebP形式の画像ファイルをアップロードしてください",
    )

    if uploaded_file:
        # Display uploaded image
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### アップロード画像")
            image = Image.open(uploaded_file)
            st.image(image, use_container_width=True)

            # Image details
            st.markdown(f"**ファイル名**: {uploaded_file.name}")
            st.markdown(f"**サイズ**: {image.size[0]} x {image.size[1]} px")
            st.markdown(f"**フォーマット**: {image.format}")

        with col2:
            st.markdown("### 認識結果")

            if st.button("🔍 認識開始", use_container_width=True, type="primary"):
                # Validate image file
                is_valid, error_msg = validate_image_file(
                    uploaded_file.name, uploaded_file.size, max_size_mb=10
                )
                if not is_valid:
                    st.error(f"⚠️ {error_msg}")
                else:
                    with st.spinner("AI が画像を分析中..."):
                        try:
                            # Convert image to base64
                            buffered = io.BytesIO()
                            image.save(buffered, format=image.format or "JPEG")
                            img_base64 = base64.b64encode(buffered.getvalue()).decode()

                            # Get media type
                            media_type_map = {
                                "JPEG": "image/jpeg",
                                "PNG": "image/png",
                                "WEBP": "image/webp",
                            }
                            media_type = media_type_map.get(image.format, "image/jpeg")

                            # Call image recognition Lambda via AgentCore
                            result = backend_client.recognize_sake_label(img_base64, media_type)

                            if result and result.get("sake_info"):
                                sake_info = result["sake_info"]
                                confidence = result.get("confidence", 0.0)

                                st.markdown("#### 認識された情報")

                                if confidence > 0.7:
                                    st.success(f"✅ 認識成功 (信頼度: {confidence * 100:.1f}%)")
                                elif confidence > 0.5:
                                    st.warning(
                                        f"⚠️ 認識完了 (信頼度: {confidence * 100:.1f}%) - 結果を確認してください"
                                    )
                                else:
                                    st.info(
                                        f"💡 認識完了 (信頼度: {confidence * 100:.1f}%) - 精度が低い可能性があります"
                                    )

                                with st.container():
                                    st.markdown("**銘柄**")
                                    st.markdown(f"# {sake_info.get('sake_name', '不明')}")

                                    st.markdown("**蔵元**")
                                    st.markdown(f"## {sake_info.get('brewery_name', '不明')}")

                                    col_a, col_b, col_c = st.columns(3)

                                    with col_a:
                                        if sake_info.get("sake_type"):
                                            st.metric("タイプ", sake_info["sake_type"])

                                    with col_b:
                                        if sake_info.get("rice_polish_ratio"):
                                            st.metric(
                                                "精米歩合", f"{sake_info['rice_polish_ratio']}%"
                                            )

                                    with col_c:
                                        if sake_info.get("alcohol_content"):
                                            st.metric(
                                                "アルコール度数", f"{sake_info['alcohol_content']}%"
                                            )

                                    if sake_info.get("ingredients"):
                                        st.markdown("**原料米**")
                                        ingredients = sake_info["ingredients"]
                                        if isinstance(ingredients, list):
                                            st.write(", ".join(ingredients))
                                        else:
                                            st.write(ingredients)

                                    if sake_info.get("prefecture"):
                                        st.markdown("**産地**")
                                        st.write(sake_info["prefecture"])

                                st.markdown("---")

                                # Action buttons
                                col1, col2 = st.columns(2)

                                with col1:
                                    if st.button(
                                        "📝 テイスティング記録へ", use_container_width=True
                                    ):
                                        st.switch_page("pages/3_⭐_Rating.py")

                                with col2:
                                    if st.button("💾 お気に入りに追加", use_container_width=True):
                                        st.toast("お気に入りに追加しました！")
                            else:
                                st.error("❌ 画像から日本酒の情報を認識できませんでした")
                                st.info(
                                    "💡 ラベル全体が写っているか、明るさが適切か確認してください"
                                )

                        except BackendError as e:
                            st.error(f"❌ エラー: {str(e)}")
                        except Exception as e:
                            st.error(f"❌ 予期しないエラーが発生しました: {str(e)}")


if __name__ == "__main__":
    main()
