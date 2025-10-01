"""
Sake Sensei - Gamification System

Achievement badges, progress tracking, and user engagement features.
"""

from typing import Any

import streamlit as st


class Achievement:
    """Achievement/Badge definition."""

    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        icon: str,
        requirement: int,
        badge_type: str = "primary",
    ):
        self.id = id
        self.title = title
        self.description = description
        self.icon = icon
        self.requirement = requirement
        self.badge_type = badge_type


# Achievement definitions
ACHIEVEMENTS = [
    Achievement(
        id="first_taste",
        title="初めての一杯",
        description="最初のテイスティング記録を作成",
        icon="🍶",
        requirement=1,
        badge_type="success",
    ),
    Achievement(
        id="sake_explorer",
        title="日本酒探求者",
        description="10種類の日本酒をテイスティング",
        icon="🗺️",
        requirement=10,
        badge_type="primary",
    ),
    Achievement(
        id="sake_master",
        title="日本酒マスター",
        description="50種類の日本酒をテイスティング",
        icon="👑",
        requirement=50,
        badge_type="warning",
    ),
    Achievement(
        id="sake_legend",
        title="日本酒レジェンド",
        description="100種類の日本酒をテイスティング",
        icon="🏆",
        requirement=100,
        badge_type="warning",
    ),
    Achievement(
        id="preference_complete",
        title="プリファレンス完了",
        description="好みのプリファレンスを登録",
        icon="🎯",
        requirement=1,
        badge_type="primary",
    ),
    Achievement(
        id="ai_enthusiast",
        title="AI愛用者",
        description="AIおすすめを5回取得",
        icon="🤖",
        requirement=5,
        badge_type="primary",
    ),
    Achievement(
        id="reviewer",
        title="レビュアー",
        description="5件のテイスティングノートを記録",
        icon="📝",
        requirement=5,
        badge_type="success",
    ),
    Achievement(
        id="sake_connoisseur",
        title="日本酒通",
        description="すべてのタイプの日本酒を試飲",
        icon="🎓",
        requirement=8,  # 8 types of sake
        badge_type="warning",
    ),
    Achievement(
        id="social_drinker",
        title="ソーシャルドリンカー",
        description="友人と一緒に10回飲んだ記録",
        icon="👥",
        requirement=10,
        badge_type="success",
    ),
    Achievement(
        id="sake_photographer",
        title="ラベルコレクター",
        description="画像認識を10回使用",
        icon="📸",
        requirement=10,
        badge_type="primary",
    ),
]


def get_user_progress(user_id: str) -> dict[str, Any]:
    """
    Get user progress data.

    Args:
        user_id: User ID

    Returns:
        Dictionary with progress data
    """
    # Get from session state (in production, fetch from DynamoDB)
    progress_key = f"user_progress_{user_id}"
    if progress_key not in st.session_state:
        st.session_state[progress_key] = {
            "tastings_count": 0,
            "recommendations_count": 0,
            "preferences_set": False,
            "image_recognitions": 0,
            "reviews_count": 0,
            "unique_types": set(),
            "social_tastings": 0,
            "earned_achievements": set(),
        }

    return st.session_state[progress_key]


def check_achievements(user_id: str) -> list[Achievement]:
    """
    Check which achievements user has earned.

    Args:
        user_id: User ID

    Returns:
        List of newly earned achievements
    """
    progress = get_user_progress(user_id)
    newly_earned = []

    for achievement in ACHIEVEMENTS:
        # Skip if already earned
        if achievement.id in progress["earned_achievements"]:
            continue

        # Check achievement requirements
        earned = False

        if achievement.id == "first_taste" and progress["tastings_count"] >= 1 or achievement.id == "sake_explorer" and progress["tastings_count"] >= 10 or achievement.id == "sake_master" and progress["tastings_count"] >= 50 or achievement.id == "sake_legend" and progress["tastings_count"] >= 100 or achievement.id == "preference_complete" and progress["preferences_set"] or achievement.id == "ai_enthusiast" and progress["recommendations_count"] >= 5 or achievement.id == "reviewer" and progress["reviews_count"] >= 5 or achievement.id == "sake_connoisseur" and len(progress["unique_types"]) >= 8 or achievement.id == "social_drinker" and progress["social_tastings"] >= 10 or achievement.id == "sake_photographer" and progress["image_recognitions"] >= 10:
            earned = True

        if earned:
            progress["earned_achievements"].add(achievement.id)
            newly_earned.append(achievement)

    return newly_earned


def update_user_progress(user_id: str, action: str, metadata: dict | None = None) -> None:
    """
    Update user progress based on action.

    Args:
        user_id: User ID
        action: Action type (tasting, recommendation, preference_set, etc.)
        metadata: Additional metadata
    """
    progress = get_user_progress(user_id)
    metadata = metadata or {}

    if action == "tasting":
        progress["tastings_count"] += 1
        progress["reviews_count"] += 1

        # Track unique sake types
        sake_type = metadata.get("sake_type")
        if sake_type:
            progress["unique_types"].add(sake_type)

        # Track social tastings
        if metadata.get("drinking_scene") == "友人と":
            progress["social_tastings"] += 1

    elif action == "recommendation":
        progress["recommendations_count"] += 1

    elif action == "preference_set":
        progress["preferences_set"] = True

    elif action == "image_recognition":
        progress["image_recognitions"] += 1

    # Check for new achievements
    newly_earned = check_achievements(user_id)

    # Show achievement notifications
    for achievement in newly_earned:
        show_achievement_earned(achievement)


def show_achievement_earned(achievement: Achievement) -> None:
    """
    Show achievement earned notification.

    Args:
        achievement: Achievement that was earned
    """
    st.balloons()
    st.toast(f"🏆 実績解除！ {achievement.icon} {achievement.title}", icon="🎉")

    # Show detailed notification
    st.success(f"""
    ### 🎉 実績解除！

    **{achievement.icon} {achievement.title}**

    {achievement.description}
    """)


def render_achievements_panel(user_id: str) -> None:
    """
    Render achievements panel showing earned and locked achievements.

    Args:
        user_id: User ID
    """
    progress = get_user_progress(user_id)
    earned_ids = progress["earned_achievements"]

    st.markdown("### 🏆 実績")

    # Stats
    total_achievements = len(ACHIEVEMENTS)
    earned_count = len(earned_ids)
    completion_rate = (earned_count / total_achievements * 100) if total_achievements > 0 else 0

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("獲得実績", f"{earned_count}/{total_achievements}")

    with col2:
        st.metric("達成率", f"{completion_rate:.1f}%")

    with col3:
        st.metric("レベル", calculate_user_level(earned_count))

    # Progress bar
    st.progress(completion_rate / 100)

    st.markdown("---")

    # Achievement tabs
    tab1, tab2 = st.tabs(["🔓 獲得済み", "🔒 未獲得"])

    with tab1:
        earned_achievements = [a for a in ACHIEVEMENTS if a.id in earned_ids]

        if earned_achievements:
            for achievement in earned_achievements:
                render_achievement_card(achievement, is_earned=True)
        else:
            st.info("まだ実績を獲得していません。日本酒の旅を始めましょう！")

    with tab2:
        locked_achievements = [a for a in ACHIEVEMENTS if a.id not in earned_ids]

        if locked_achievements:
            for achievement in locked_achievements:
                render_achievement_card(achievement, is_earned=False, progress=progress)
        else:
            st.success("🎉 すべての実績を獲得しました！おめでとうございます！")


def render_achievement_card(
    achievement: Achievement, is_earned: bool = False, progress: dict | None = None
) -> None:
    """
    Render a single achievement card.

    Args:
        achievement: Achievement object
        is_earned: Whether achievement is earned
        progress: User progress data (for showing progress to locked achievements)
    """
    opacity = "1.0" if is_earned else "0.5"
    border_color = "var(--success-color)" if is_earned else "var(--border-color)"

    st.markdown(
        f"""
    <div style="
        background: var(--bg-card);
        padding: 1rem;
        border-radius: var(--radius-md);
        border-left: 4px solid {border_color};
        margin-bottom: 1rem;
        opacity: {opacity};
        display: flex;
        align-items: center;
        gap: 1rem;
    ">
        <div style="font-size: 3rem;">{achievement.icon}</div>
        <div style="flex: 1;">
            <h4 style="margin: 0; color: var(--text-primary);">{achievement.title}</h4>
            <p style="margin: 0.25rem 0; color: var(--text-secondary); font-size: 0.875rem;">
                {achievement.description}
            </p>
            {'<span style="color: var(--success-color); font-weight: 600;">✓ 獲得済み</span>' if is_earned else ""}
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Show progress for locked achievements
    if not is_earned and progress:
        current_progress = get_achievement_progress(achievement, progress)
        if current_progress is not None:
            progress_pct = min(current_progress / achievement.requirement, 1.0)
            st.progress(progress_pct)
            st.caption(f"進捗: {current_progress}/{achievement.requirement}")


def get_achievement_progress(achievement: Achievement, progress: dict) -> int | None:
    """
    Get current progress for an achievement.

    Args:
        achievement: Achievement object
        progress: User progress data

    Returns:
        Current progress value or None
    """
    if achievement.id == "first_taste" or achievement.id in ["sake_explorer", "sake_master", "sake_legend"]:
        return progress["tastings_count"]
    elif achievement.id == "preference_complete":
        return 1 if progress["preferences_set"] else 0
    elif achievement.id == "ai_enthusiast":
        return progress["recommendations_count"]
    elif achievement.id == "reviewer":
        return progress["reviews_count"]
    elif achievement.id == "sake_connoisseur":
        return len(progress["unique_types"])
    elif achievement.id == "social_drinker":
        return progress["social_tastings"]
    elif achievement.id == "sake_photographer":
        return progress["image_recognitions"]

    return None


def calculate_user_level(earned_count: int) -> int:
    """
    Calculate user level based on earned achievements.

    Args:
        earned_count: Number of earned achievements

    Returns:
        User level (1-10)
    """
    return min(earned_count // 2 + 1, 10)


def render_user_stats_widget(user_id: str) -> None:
    """
    Render compact user stats widget for sidebar or dashboard.

    Args:
        user_id: User ID
    """
    progress = get_user_progress(user_id)
    earned_count = len(progress["earned_achievements"])
    level = calculate_user_level(earned_count)

    st.markdown(
        f"""
    <div style="
        background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
        color: white;
        padding: 1rem;
        border-radius: var(--radius-md);
        text-align: center;
    ">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">🏆</div>
        <div style="font-size: 1.5rem; font-weight: 700;">レベル {level}</div>
        <div style="font-size: 0.875rem; margin-top: 0.5rem;">
            実績 {earned_count}/{len(ACHIEVEMENTS)} 獲得
        </div>
        <div style="font-size: 0.875rem;">
            テイスティング {progress["tastings_count"]} 本
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )
