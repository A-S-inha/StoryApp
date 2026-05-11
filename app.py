import streamlit as st
import openai
import html

from story_engine import (
    generate_story_pipeline,
    revise_story_with_feedback,
    parse_judge_scores,
)

st.set_page_config(
    page_title="Dream Up a Story",
    page_icon="✨",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root {
        --bg: #fbfaf7;
        --card: #ffffff;
        --text: #2f3b4c;
        --muted: #6f7a88;
        --line: #ece8e1;
        --yellow: #f3c55b;
        --peach: #f6b29d;
        --pink: #f4c9c6;
        --blue: #c9d8e6;
        --mint: #d8eadb;
        --lavender: #ddd7ef;
        --shadow: 0 8px 24px rgba(39, 52, 67, 0.06);
        --radius: 22px;
    }

    .stApp {
        background: linear-gradient(180deg, #fcfbf8 0%, #f8f6f2 100%);
        color: var(--text);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1240px;
    }

    h1, h2, h3 {
        color: var(--text);
        letter-spacing: -0.02em;
    }

    .hero {
        background: rgba(255,255,255,0.55);
        border: 1px solid rgba(236,232,225,0.9);
        border-radius: 28px;
        padding: 1.6rem 1.8rem;
        box-shadow: var(--shadow);
        margin-bottom: 1.25rem;
    }

    .hero-title {
        font-size: 3rem;
        line-height: 1.05;
        font-weight: 800;
        margin: 0;
        color: #334155;
    }

    .hero-subtitle {
        color: var(--muted);
        font-size: 1.08rem;
        margin-top: 0.35rem;
    }

    .card {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: var(--radius);
        padding: 1.2rem 1.2rem 1.15rem 1.2rem;
        box-shadow: var(--shadow);
    }

    .section-title {
        font-size: 1.35rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
        color: #2f3b4c;
    }

    .section-subtle {
        color: var(--muted);
        font-size: 0.95rem;
        margin-bottom: 0.8rem;
    }

    .story-shell {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 26px;
        padding: 1.4rem 1.5rem;
        box-shadow: var(--shadow);
        min-height: 520px;
    }

    .story-kicker {
        color: #6a7280;
        font-weight: 600;
        margin-bottom: 0.65rem;
        font-size: 1rem;
    }

    .story-title {
        font-size: 2.1rem;
        line-height: 1.1;
        font-weight: 800;
        color: #2f3b4c;
        margin-bottom: 1rem;
    }

    .story-body {
        color: #384454;
        font-size: 1.07rem;
        line-height: 1.95;
    }

    .pill {
        display: inline-block;
        background: #fff5f0;
        color: #b96f60;
        border: 1px solid #f4ddd6;
        border-radius: 999px;
        padding: 0.35rem 0.75rem;
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
    }

    .judge-wrap {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 26px;
        padding: 1.2rem;
        box-shadow: var(--shadow);
        margin-top: 1rem;
    }

    .score-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 0.8rem;
        margin-top: 0.9rem;
    }

    .score-card {
        border-radius: 20px;
        padding: 1rem 0.9rem;
        border: 1px solid rgba(0,0,0,0.04);
        min-height: 120px;
    }

    .score-title {
        font-size: 0.9rem;
        color: #506072;
        margin-bottom: 0.6rem;
        font-weight: 600;
    }

    .score-value {
        font-size: 1.65rem;
        font-weight: 800;
        color: #334155;
    }

    .score-note {
        font-size: 0.85rem;
        color: #6f7a88;
        margin-top: 0.2rem;
    }

    .bg-yellow { background: #fff8e8; }
    .bg-peach { background: #fff2ed; }
    .bg-blue { background: #eef6fb; }
    .bg-lavender { background: #f5f2fb; }
    .bg-mint { background: #f1f8f1; }

    .tiny-footer {
        text-align: center;
        color: #8390a0;
        font-size: 0.96rem;
        margin-top: 1.2rem;
    }

    .divider-space {
        height: 0.6rem;
    }

    .stTextArea textarea, .stTextInput input {
        border-radius: 16px !important;
        border: 1px solid #eae5dc !important;
        background: #fffdfb !important;
        color: #334155 !important;
        caret-color: #1f2937 !important;
        cursor: text !important;
    }

    .stTextArea textarea::placeholder,
    .stTextInput input::placeholder {
        color: #6f7a88 !important;
        opacity: 1 !important;
    }

    .stTextArea label,
    .stTextInput label,
    .stSelectbox label {
        color: #334155 !important;
        font-weight: 600 !important;
    }

    .stTextArea textarea:focus,
    .stTextInput input:focus,
    .stSelectbox [data-baseweb="select"] > div:focus-within {
        border-color: #d9b560 !important;
        box-shadow: 0 0 0 2px rgba(217, 181, 96, 0.25) !important;
        outline: none !important;
    }

    .stSelectbox [data-baseweb="select"] > div {
        border-radius: 16px !important;
        border: 1px solid #eae5dc !important;
        background: #fffdfb !important;
        min-height: 48px;
        cursor: pointer !important;
    }

    .stSelectbox [data-baseweb="select"] span,
    .stSelectbox [data-baseweb="select"] div,
    .stSelectbox [data-baseweb="select"] input {
        color: #334155 !important;
    }

    .stSelectbox [data-baseweb="select"] svg {
        fill: #6f7a88 !important;
    }

    .stButton > button {
        background: linear-gradient(180deg, #f3c55b 0%, #ecb845 100%);
        color: white;
        border: none;
        border-radius: 16px;
        padding: 0.82rem 1.2rem;
        font-weight: 700;
        font-size: 1rem;
        box-shadow: 0 8px 18px rgba(236, 184, 69, 0.26);
    }

    .stButton > button:hover {
        background: linear-gradient(180deg, #f1bf4a 0%, #e6af36 100%);
        color: white;
    }

    .secondary-button .stButton > button {
        background: linear-gradient(180deg, #f2a996 0%, #ea937f 100%);
        box-shadow: 0 8px 18px rgba(234, 147, 127, 0.22);
    }

    .stExpander {
        border-radius: 18px !important;
        border: 1px solid #ece8e1 !important;
        background: rgba(255,255,255,0.72) !important;
    }

    @media (max-width: 1000px) {
        .score-grid {
            grid-template-columns: repeat(2, 1fr);
        }
        .hero-title {
            font-size: 2.2rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def initialize_session_state() -> None:
    defaults = {
        "user_request": "",
        "age_band": "5-7",
        "style": "Classic Bedtime",
        "custom_style": "",
        "length": "Medium",
        "story_plan": "",
        "draft_story": "",
        "judge_feedback": "",
        "final_story": "",
        "scores": {},
        "generated": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def validate_user_input(user_request: str) -> str:
    if not user_request or not user_request.strip():
        return "Tell us what happens in your story!"
    if len(user_request.strip()) < 10:
        return "Add a few more words so we can dream up something great!"
    return ""


def render_judge_summary(scores: dict) -> None:
    if not scores:
        return

    age = scores.get("Age appropriateness", "—")
    language = scores.get("Language simplicity", "—")
    coherence = scores.get("Coherence", "—")
    bedtime = scores.get("Bedtime suitability", "—")
    overall = scores.get("Overall quality", "—")

    st.markdown(
        f"""
        <div class="judge-wrap">
            <div class="section-title">⭐ Story Judge Summary</div>
            <div class="section-subtle">A quick quality check for clarity, age fit, and emotional safety.</div>
            <div class="score-grid">
                <div class="score-card bg-yellow">
                    <div class="score-title">Age Appropriateness</div>
                    <div class="score-value">{age}/5</div>
                    <div class="score-note">Suitable for the chosen age</div>
                </div>
                <div class="score-card bg-peach">
                    <div class="score-title">Language Simplicity</div>
                    <div class="score-value">{language}/5</div>
                    <div class="score-note">Clear and easy to read</div>
                </div>
                <div class="score-card bg-blue">
                    <div class="score-title">Coherence</div>
                    <div class="score-value">{coherence}/5</div>
                    <div class="score-note">Has a clear story arc</div>
                </div>
                <div class="score-card bg-lavender">
                    <div class="score-title">Bedtime Suitability</div>
                    <div class="score-value">{bedtime}/5</div>
                    <div class="score-note">Emotionally safe ending</div>
                </div>
                <div class="score-card bg-mint">
                    <div class="score-title">Overall Quality</div>
                    <div class="score-value">{overall}/5</div>
                    <div class="score-note">Final story experience</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    revise_value = scores.get("Revise", "UNKNOWN")
    if revise_value == "YES":
        st.info("The judge suggested another refinement pass.")
    elif revise_value == "NO":
        st.success("The judge approved this version without requiring another rewrite.")


def extract_story_title(story_text: str) -> str:
    if not story_text:
        return "Your Adventure"
    lines = [line.strip() for line in story_text.splitlines() if line.strip()]
    if not lines:
        return "Your Adventure"
    first_line = lines[0]
    if len(first_line) < 70:
        return first_line
    return "Your Adventure"


def extract_story_body(story_text: str, story_title: str) -> str:
    if not story_text:
        return ""

    story_lines = [line.strip() for line in story_text.splitlines() if line.strip()]
    if not story_lines:
        return ""

    if story_lines[0] == story_title and len(story_lines) > 1:
        return "\n\n".join(story_lines[1:])

    # If the model returned only a title line, keep full text visible instead of blank body.
    return story_text.strip()


initialize_session_state()

st.markdown(
    """
    <div class="hero">
        <div style="display:flex; align-items:center; justify-content:space-between; gap:1rem; flex-wrap:wrap;">
            <div>
                <div style="font-size:2rem;">🌙 🌈 ☁️</div>
                <h1 class="hero-title">Dream Up a Story ✨</h1>
                <div class="hero-subtitle">Pick a mood, add a spark, and jump into a magical story made just for you.</div>
            </div>
            <div style="font-size:4rem; opacity:0.9;">🌟</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

left_col, right_col = st.columns([0.95, 2.05], gap="large")

with left_col:
    st.markdown(
        """
        <div class="card">
            <div class="section-title">🌈 Let's build your adventure</div>
            <div class="section-subtle">Choose your story style, add your idea, and we'll turn it into something fun, cozy, or wild.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    user_request = st.text_area(
        "What should happen in your story?",
        value=st.session_state["user_request"],
        placeholder="A dragon who is scared to fly finds a secret map in the clouds.",
        height=160,
    )

    age_options = ["5-7", "8-10"]
    age_index = age_options.index(st.session_state["age_band"]) if st.session_state["age_band"] in age_options else 0
    age_band = st.selectbox("Who is this story for?", options=age_options, index=age_index)

    style_options = [
        "Calm & Cozy",
        "Classic Bedtime",
        "Silly & Playful",
        "Magical Adventure",
        "Animal Adventure",
        "Friendship Story",
        "Brave Little Quest",
    ]
    style_index = style_options.index(st.session_state["style"]) if st.session_state["style"] in style_options else 1
    style = st.selectbox("Choose the vibe", options=style_options, index=style_index)

    custom_style = st.text_input(
        "Extra magic (optional)",
        value=st.session_state["custom_style"],
        placeholder="Examples: super silly, magical, lots of talking animals, exciting but not scary",
    )

    length_options = ["Short", "Medium", "Long"]
    length_index = length_options.index(st.session_state["length"]) if st.session_state["length"] in length_options else 1
    length = st.selectbox("How long should the adventure be?", options=length_options, index=length_index)

    generate_clicked = st.button("✨ Start the Story", use_container_width=True)

    st.caption("💛 Made to feel fun, imaginative, and bedtime-friendly.")

    if generate_clicked:
        error_message = validate_user_input(user_request)

        if error_message:
            st.error(error_message)
        else:
            st.session_state["user_request"] = user_request
            st.session_state["age_band"] = age_band
            st.session_state["style"] = style
            st.session_state["custom_style"] = custom_style
            st.session_state["length"] = length

            try:
                with st.spinner("Dreaming up your story..."):
                    result = generate_story_pipeline(
                        user_request=user_request,
                        age_band=age_band,
                        style=style,
                        custom_style=custom_style,
                        length=length,
                    )

                st.session_state["story_plan"] = result["story_plan"]
                st.session_state["draft_story"] = result["draft_story"]
                st.session_state["judge_feedback"] = result["judge_feedback"]
                st.session_state["final_story"] = result["final_story"]
                st.session_state["scores"] = parse_judge_scores(result["judge_feedback"])
                st.session_state["generated"] = True
            except openai.error.RateLimitError:
                st.error(
                    "OpenAI quota limit reached for this API key. "
                    "Please add billing/credits to your OpenAI account or use a different key."
                )
            except openai.error.AuthenticationError:
                st.error("Invalid API key. Please set a valid OPENAI_API_KEY and try again.")
            except openai.error.OpenAIError as exc:
                st.error(f"OpenAI API error: {exc}")
            except Exception as exc:
                st.error(f"Unexpected error while generating story: {exc}")

with right_col:
    if st.session_state["generated"]:
        story_title = extract_story_title(st.session_state["final_story"])

        story_text = st.session_state["final_story"]
        story_body = extract_story_body(story_text, story_title)
        safe_title = html.escape(story_title)
        safe_body = html.escape(story_body).replace("\n", "<br><br>")
        if story_body.strip():
            st.markdown(
                f"""
                <div class="story-shell">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; flex-wrap:wrap;">
                        <div>
                            <div class="story-kicker">📖 Your Adventure</div>
                            <div class="story-title">{safe_title}</div>
                        </div>
                    </div>
                    <div class="story-body">{safe_body}</div>
                    <div style="text-align:right; font-size:4rem; opacity:0.75; margin-top:0.4rem;">
                        🐢 ✨
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info(
                "Hmm, the story came back empty. Tap ✨ Start the Story again or try a little more detail in your idea."
            )

        render_judge_summary(st.session_state["scores"])

        with st.expander("View story plan"):
            st.write(st.session_state["story_plan"])

        with st.expander("View judge feedback"):
            st.text(st.session_state["judge_feedback"])

        with st.expander("View first draft"):
            st.write(st.session_state["draft_story"])

        st.markdown('<div class="divider-space"></div>', unsafe_allow_html=True)

        st.markdown(
            """
            <div class="card">
                <div class="section-title">🪄 Change the story</div>
                <div class="section-subtle">Make it funnier, add more magic, change a name, or keep the adventure going.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        user_feedback = st.text_input(
            "Revision request",
            placeholder="Examples: more jokes, add a friendly dragon, change a name, extra sparkle at the end",
            label_visibility="collapsed",
        )

        st.markdown('<div class="secondary-button">', unsafe_allow_html=True)
        revise_clicked = st.button("🪄 Make It Even Better", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if revise_clicked:
            if not user_feedback.strip():
                st.error("Type what you would like to change first!")
            else:
                try:
                    with st.spinner("Sprinkling more magic on your story..."):
                        revision_result = revise_story_with_feedback(
                            user_request=st.session_state["user_request"],
                            current_story=st.session_state["final_story"],
                            user_feedback=user_feedback,
                            age_band=st.session_state["age_band"],
                            style=st.session_state["style"],
                            custom_style=st.session_state["custom_style"],
                            length=st.session_state["length"],
                        )

                    st.session_state["final_story"] = revision_result["revised_story"]
                    st.session_state["judge_feedback"] = revision_result["judge_feedback"]
                    st.session_state["scores"] = parse_judge_scores(revision_result["judge_feedback"])

                    st.success("Story revised successfully.")
                    st.rerun()
                except openai.error.RateLimitError:
                    st.error(
                        "OpenAI quota limit reached for this API key. "
                        "Please add billing/credits to your OpenAI account or use a different key."
                    )
                except openai.error.AuthenticationError:
                    st.error("Invalid API key. Please set a valid OPENAI_API_KEY and try again.")
                except openai.error.OpenAIError as exc:
                    st.error(f"OpenAI API error: {exc}")
                except Exception as exc:
                    st.error(f"Unexpected error while revising story: {exc}")
    else:
        st.markdown(
            """
            <div class="story-shell" style="display:flex; align-items:center; justify-content:center; text-align:center;">
                <div>
                    <div style="font-size:4.2rem; margin-bottom:0.5rem;">☁️🌙✨</div>
                    <div class="section-title" style="font-size:1.8rem;">Your adventure begins here ✨</div>
                    <div class="section-subtle" style="font-size:1rem;">
                        Add your idea on the left, pick your vibe, and watch your story come to life.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown(
    """
    <div class="tiny-footer">💗 Packed with imagination, sparkle, and story magic ✨</div>
    """,
    unsafe_allow_html=True,
)