"""
Sake Sensei - Sake Display Card Component

Reusable component for displaying sake information in a card format.
"""

from typing import Any

import streamlit as st


def render_sake_card(sake: dict[str, Any], show_details: bool = True, key_suffix: str = ""):
    """
    Render a sake information card.

    Args:
        sake: Dictionary containing sake information
        show_details: Whether to show detailed information
        key_suffix: Suffix for unique widget keys
    """
    with st.container():
        st.markdown(
            """
        <div class="sake-card">
        """,
            unsafe_allow_html=True,
        )

        # Header with sake name
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"### {sake.get('name', '未知の日本酒')}")
            st.markdown(f"**{sake.get('brewery_name', '蔵元不明')}**")

        with col2:
            # Rating or favorite button
            if st.button("⭐", key=f"favorite_{sake.get('sake_id', '')}_{key_suffix}"):
                st.toast("お気に入りに追加しました！")

        # Basic info
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("タイプ", sake.get("sake_type", "N/A"))

        with col2:
            st.metric("精米歩合", f"{sake.get('rice_polish_ratio', 'N/A')}%")

        with col3:
            sake_meter = sake.get("sake_meter_value")
            if sake_meter is not None:
                if sake_meter > 0:
                    taste = "辛口"
                elif sake_meter < 0:
                    taste = "甘口"
                else:
                    taste = "中口"
                st.metric("日本酒度", f"{sake_meter} ({taste})")
            else:
                st.metric("日本酒度", "N/A")

        # Detailed information
        if show_details:
            st.markdown("---")

            # Flavor profile
            if "flavor_profile" in sake:
                st.markdown("**味わい**")
                flavor = sake["flavor_profile"]

                if isinstance(flavor, dict):
                    flavor_tags = []
                    for key, value in flavor.items():
                        if value and value != "N/A":
                            flavor_tags.append(f"`{key}: {value}`")

                    if flavor_tags:
                        st.markdown(" ".join(flavor_tags))
                elif isinstance(flavor, list):
                    st.markdown(" ".join([f"`{f}`" for f in flavor]))
                else:
                    st.markdown(f"`{flavor}`")

            # Description
            description = sake.get("description", "")
            if description:
                st.markdown("**説明**")
                st.write(description)

            # Serving recommendations
            serving_temp = sake.get("serving_temperature", "")
            if serving_temp:
                st.markdown(f"**おすすめの温度**: {serving_temp}")

            # Food pairing
            food_pairing = sake.get("food_pairing", [])
            if food_pairing:
                if isinstance(food_pairing, list):
                    st.markdown(f"**料理との相性**: {', '.join(food_pairing)}")
                else:
                    st.markdown(f"**料理との相性**: {food_pairing}")

            # Price
            price_range = sake.get("price_range", "")
            if price_range:
                st.markdown(f"**価格帯**: {price_range}")

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
