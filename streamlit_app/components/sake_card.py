"""
Sake Sensei - Sake Display Card Component

Reusable component for displaying sake information in a card format.
"""

from typing import Any

import streamlit as st
from utils.ui_components import render_badge, render_rating_stars


def render_sake_card(sake: dict[str, Any], show_details: bool = True, key_suffix: str = ""):
    """
    Render a sake information card with enhanced interactions.

    Args:
        sake: Dictionary containing sake information
        show_details: Whether to show detailed information
        key_suffix: Suffix for unique widget keys
    """
    with st.container():
        st.markdown('<div class="sake-card">', unsafe_allow_html=True)

        # Header with sake name and badges
        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown(f"### {sake.get('name', '未知の日本酒')}")
            st.markdown(f"**{sake.get('brewery_name', '蔵元不明')}**")

            # Type badge
            sake_type = sake.get("sake_type", "N/A")
            if sake_type != "N/A":
                st.markdown(render_badge(sake_type, "primary"), unsafe_allow_html=True)

        with col2:
            # Favorite button with animation
            is_favorite = st.session_state.get(f"fav_{sake.get('sake_id', '')}_{key_suffix}", False)
            fav_icon = "❤️" if is_favorite else "🤍"

            if st.button(
                fav_icon,
                key=f"favorite_{sake.get('sake_id', '')}_{key_suffix}",
                help="お気に入りに追加",
            ):
                st.session_state[f"fav_{sake.get('sake_id', '')}_{key_suffix}"] = not is_favorite
                st.toast(
                    "❤️ お気に入りに追加しました！"
                    if not is_favorite
                    else "お気に入りから削除しました"
                )
                st.rerun()

        st.markdown("---")

        # Basic info with enhanced metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            sake_type_display = sake.get("sake_type", "N/A")
            st.metric("🍶 タイプ", sake_type_display)

        with col2:
            polish_ratio = sake.get("rice_polish_ratio", "N/A")
            polish_display = f"{polish_ratio}%" if polish_ratio != "N/A" else "N/A"
            st.metric("🌾 精米歩合", polish_display)

        with col3:
            sake_meter = sake.get("sake_meter_value")
            if sake_meter is not None:
                if sake_meter > 0:
                    taste = "辛口"
                    taste_icon = "🌶️"
                elif sake_meter < 0:
                    taste = "甘口"
                    taste_icon = "🍯"
                else:
                    taste = "中口"
                    taste_icon = "⚖️"
                st.metric(f"{taste_icon} 日本酒度", f"{sake_meter} ({taste})")
            else:
                st.metric("日本酒度", "N/A")

        # Detailed information with enhanced styling
        if show_details:
            st.markdown("---")

            # Flavor profile with badges
            if "flavor_profile" in sake:
                st.markdown("**🎨 味わい**")
                flavor = sake["flavor_profile"]

                if isinstance(flavor, dict):
                    flavor_badges = []
                    for key, value in flavor.items():
                        if value and value != "N/A":
                            flavor_badges.append(render_badge(f"{key}: {value}", "secondary"))

                    if flavor_badges:
                        st.markdown(" ".join(flavor_badges), unsafe_allow_html=True)
                elif isinstance(flavor, list):
                    flavor_badges = [render_badge(f, "secondary") for f in flavor]
                    st.markdown(" ".join(flavor_badges), unsafe_allow_html=True)
                else:
                    st.markdown(render_badge(str(flavor), "secondary"), unsafe_allow_html=True)

            # Description
            description = sake.get("description", "")
            if description:
                st.markdown("**📝 説明**")
                st.write(description)

            # Serving recommendations
            serving_temp = sake.get("serving_temperature", "")
            if serving_temp:
                st.markdown(f"**🌡️ おすすめの温度**: {serving_temp}")

            # Food pairing with icons
            food_pairing = sake.get("food_pairing", [])
            if food_pairing:
                st.markdown("**🍽️ 料理との相性**")
                if isinstance(food_pairing, list):
                    pairing_badges = [render_badge(food, "success") for food in food_pairing]
                    st.markdown(" ".join(pairing_badges), unsafe_allow_html=True)
                else:
                    st.markdown(render_badge(str(food_pairing), "success"), unsafe_allow_html=True)

            # Price with icon
            price_range = sake.get("price_range", "")
            if price_range:
                st.markdown(f"**💰 価格帯**: {price_range}")

            # Rating if available
            rating = sake.get("rating")
            if rating:
                st.markdown("**⭐ 評価**")
                st.markdown(render_rating_stars(float(rating)), unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


def render_sake_list(sake_list: list, show_details: bool = False):
    """
    Render a list of sake cards.

    Args:
        sake_list: List of sake dictionaries
        show_details: Whether to show detailed information for each card
    """
    if not sake_list:
        st.info("表示する日本酒がありません")
        return

    for idx, sake in enumerate(sake_list):
        render_sake_card(sake, show_details=show_details, key_suffix=str(idx))
        st.markdown("<br>", unsafe_allow_html=True)


def render_sake_comparison(sake1: dict[str, Any], sake2: dict[str, Any]):
    """
    Render side-by-side comparison of two sake.

    Args:
        sake1: First sake dictionary
        sake2: Second sake dictionary
    """
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 日本酒 A")
        render_sake_card(sake1, show_details=True, key_suffix="compare_a")

    with col2:
        st.markdown("### 日本酒 B")
        render_sake_card(sake2, show_details=True, key_suffix="compare_b")


def render_brewery_card(brewery: dict[str, Any]):
    """
    Render brewery information card.

    Args:
        brewery: Dictionary containing brewery information
    """
    with st.container():
        st.markdown(
            """
        <div class="sake-card">
        """,
            unsafe_allow_html=True,
        )

        # Header
        st.markdown(f"### 🏭 {brewery.get('name', '未知の蔵元')}")

        # Location
        location = brewery.get("location", {})
        if isinstance(location, dict):
            prefecture = location.get("prefecture", "")
            city = location.get("city", "")
            if prefecture or city:
                st.markdown(f"**所在地**: {prefecture} {city}")
        elif isinstance(location, str):
            st.markdown(f"**所在地**: {location}")

        # Founded year
        founded = brewery.get("founded_year")
        if founded:
            st.markdown(f"**創業**: {founded}年")

        # Description
        description = brewery.get("description", "")
        if description:
            st.markdown("---")
            st.write(description)

        # Signature sake
        signature_sake = brewery.get("signature_sake", [])
        if signature_sake:
            st.markdown("**代表銘柄**")
            if isinstance(signature_sake, list):
                for sake in signature_sake:
                    st.markdown(f"- {sake}")
            else:
                st.markdown(f"- {signature_sake}")

        # Website
        website = brewery.get("website", "")
        if website:
            st.markdown(f"**ウェブサイト**: [{website}]({website})")

        st.markdown("</div>", unsafe_allow_html=True)
