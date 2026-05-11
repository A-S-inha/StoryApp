import os
import re
from typing import Any, Dict

import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("OPENAI_API_KEY is not set in the environment.")


def call_model(prompt: str, max_tokens: int = 1200, temperature: float = 0.3) -> str:
   
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        stream=False,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message["content"].strip()


def normalize_style(style: str) -> str:
    style_map = {
        "Calm & Cozy": "calm, cozy, soothing",
        "Classic Bedtime": "classic children's storytelling",
        "Silly & Playful": "funny, playful, lighthearted",
        "Magical Adventure": "magical, adventurous, wonder-filled",
        "Animal Adventure": "animal-centered, lively, warm adventure",
        "Friendship Story": "friendship-centered, warm, kind-hearted",
        "Brave Little Quest": "exciting, brave, age-appropriate adventure",
    }
    return style_map.get(style, style.lower())


def build_style_instruction(style: str, custom_style: str = "") -> str:
   
    preset = normalize_style(style)
    custom_style = custom_style.strip()

    if custom_style:
        return f"{preset}. Additional style guidance: {custom_style}"
    return preset


def normalize_length(length: str) -> str:
    length_map = {
        "Short": "about 400 to 600 words",
        "Medium": "about 800 to 1100 words",
        "Long": "about 1600 to 2200 words",
    }
    return length_map.get(length, "about 800 to 1100 words")


def target_word_range(length: str) -> tuple[int, int]:
    ranges = {
        "Short": (400, 600),
        "Medium": (800, 1100),
        "Long": (1600, 2200),
    }
    return ranges.get(length, (800, 1100))


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text or ""))


def should_include_child_name(user_request: str, child_name: str) -> bool:
   
    if not child_name.strip():
        return False

    req = user_request.lower()
    name = child_name.lower().strip()
    if name and name in req:
        return True

    explicit_phrases = [
        "use my child",
        "use my kid",
        "use my son",
        "use my daughter",
        "use my child's name",
        "use my kids name",
        "include my child",
        "include my kid",
        "include my son",
        "include my daughter",
        "include their name",
        "include the child's name",
        "name the character",
        "call the character",
    ]
    return any(phrase in req for phrase in explicit_phrases)


def planner_agent(
    user_request: str,
    age_band: str,
    style: str,
    custom_style: str,
    length: str,
    child_name: str = "",
) -> str:
   
    style_instruction = build_style_instruction(style, custom_style)
    normalized_length = normalize_length(length)

    prompt = f"""
You are a children's story architect for ages {age_band}.

Your job is to build a tight, emotionally resonant story outline that a writer can turn into a vivid bedtime story.

Story arc requirements — use this exact three-act structure:
- Act 1 HOOK: Open with a single vivid sensory detail or action. Never start with "Once upon a time", waking up, or a weather description.
- Act 1 WANT: Within the first two sentences, establish exactly what the main character wants or needs.
- Act 2 OBSTACLE: One clear obstacle that directly blocks the want. Keep it age-appropriate — no real danger, no loss, no scary threat.
- Act 2 ATTEMPTS: The character tries at least twice and fails before succeeding. Persistence, not luck, drives the story forward.
- Act 3 RESOLUTION: The character solves the problem through their own idea or action — never rescued by an adult or by accident.
- Act 3 ECHO: The final moment mirrors the opening image or feeling, but changed in a small, satisfying way.

Additional requirements:
- Style: {style_instruction}
- If custom style guidance is provided, treat it as a required constraint, not a suggestion.
- Target length: {normalized_length}
- Keep vocabulary and sentence complexity appropriate for ages {age_band}.
- The emotional tone of the ending must feel safe, warm, and sleep-ready — even for adventure stories.
- Main character: preserve exactly who the user specified. Do not rename or replace them.
- Child name field: {child_name if child_name else "none"} — only weave this name in if the user explicitly asked for it.

User request:
{user_request}

Return exactly in this format (no extra commentary):

Title idea:
Main character:
Setting:
Opening image (one vivid sentence):
Character want:
Obstacle:
First attempt (fails):
Second attempt (succeeds):
Resolution (character-driven):
Closing echo:
Vocabulary level:
"""
    return call_model(prompt, max_tokens=320, temperature=0.2)


def writer_agent(
    user_request: str,
    story_plan: str,
    age_band: str,
    style: str,
    custom_style: str,
    length: str,
    child_name: str = "",
) -> str:
    """
    Write the main story using the planner's outline.
    """
    style_instruction = build_style_instruction(style, custom_style)
    normalized_length = normalize_length(length)

    prompt = f"""
You are a master storyteller for children ages {age_band}. Your stories are vivid, warm, and impossible to put down — but always leave children feeling safe and sleepy at the end.

Write a complete bedtime story using the plan below.

Craft requirements:
- Begin with the title on the first line, then a blank line, then the story.
- Open mid-action or mid-scene using the opening image from the plan. Never begin with "Once upon a time", a character waking up, or a description of the weather.
- Show emotions through action and dialogue — not labels. Write "Her tail wagged so fast it blurred" not "She was excited."
- Every paragraph must contain at least one specific sensory detail: a smell, a sound, a texture, a color, or a taste.
- Dialogue must sound natural for a child or creature of that age — short sentences, contractions, real kid-speak.
- Use sentence length for pacing: short punchy sentences for action and tension; longer flowing sentences for calm and wonder.
- The character must try and fail at least once before succeeding. Effort, not luck, earns the win.
- The resolution must come from the character's own idea or action.
- The final paragraph must bring back the opening image or feeling in a changed way, and leave the reader feeling warm, safe, and ready for sleep.

Style and safety requirements:
- Style: {style_instruction}
- If custom style notes are provided, treat them as mandatory constraints.
- For custom suspense: use gentle, age-appropriate tension only — a rustling sound, a wrong turn, a missing object. Never real danger or fear.
- For adventurous or playful styles: allow energy and excitement, but land softly at the end.
- No frightening, graphic, or upsetting content. No unresolved conflict. No sad endings.
- Language: simple, clear, child-friendly. Avoid words a {age_band}-year-old wouldn't know unless the meaning is obvious from context.

Structure:
- Write in short readable paragraphs (3–5 sentences each).
- Length: {normalized_length}
- Main character: use exactly who the user specified. Do not rename or replace them.
- Child name field: {child_name if child_name else "none"} — only use this name if the user explicitly asked for it.

User request:
{user_request}

Story plan:
{story_plan}

Write only the final story. No commentary, no notes.
"""
    max_tokens = 2800 if length == "Long" else 1700
    story = call_model(prompt, max_tokens=max_tokens, temperature=0.65)

    min_words, _ = target_word_range(length)
    if word_count(story) < min_words:
        expand_prompt = f"""
You are expanding a children's story for ages {age_band} that is too short.

Expand it to reach at least {min_words} words while preserving everything that is already working.

Expansion rules:
- Keep the title on the first line.
- Keep every character name exactly as written.
- Add sensory details, dialogue, and one extra attempt or small detour — do not add new plot twists.
- Keep the same tone, style, and emotional arc.
- The ending must remain warm and sleep-ready.
- Style: {style_instruction}

User request:
{user_request}

Current story:
{story}

Return only the expanded final story. No commentary.
"""
        story = call_model(expand_prompt, max_tokens=max_tokens, temperature=0.45)

    return story


def judge_agent(user_request: str, story: str, age_band: str) -> str:
    """
    Evaluate the story for quality and age appropriateness.
    """
    prompt = f"""
You are a rigorous but fair editor for children's bedtime stories targeting ages {age_band}.

Score the story on each criterion from 1 to 5 using the benchmarks below. Be strict — a 5 means a real child of this age could read it aloud without stumbling, and a parent would happily read it at bedtime.

Scoring benchmarks by age band:
- Ages 5–7: sentences should average 8–12 words, no subordinate clauses, concrete nouns only, every character's motivation stated explicitly, zero ambiguous morality.
- Ages 8–10: sentences may average up to 16 words, one subplot is allowed, light irony is fine, character motivation may be implied but not hidden.

Criteria:
1. Age appropriateness — vocabulary, sentence length, and concepts suit the age band.
2. Language simplicity — wording is short, clear, and child-friendly with no unnecessary complexity.
3. Coherence — the story has a clear arc: hook, obstacle, attempts, resolution, and echo ending.
4. Bedtime suitability — no disturbing, overwhelming, or frightening content; ends in a warm, safe, sleep-ready feeling.
5. Instruction following — the story matches what the user asked for in style, characters, and theme.
6. Overall quality — vivid sensory detail, emotions shown through action, natural dialogue, satisfying structure.

Flag specifically if you find:
- Any sentence that exceeds the age-band word limit by more than 50%.
- Abstract vocabulary used more than twice.
- An emotion stated as a label ("she felt sad") rather than shown through action.
- A resolution that relies on luck or an adult rescuing the character.
- An ending that does not feel safe or sleep-ready.
- A mismatch between the requested style and what was written.

Return exactly in this format:

Age appropriateness: <1-5>
Language simplicity: <1-5>
Coherence: <1-5>
Bedtime suitability: <1-5>
Instruction following: <1-5>
Overall quality: <1-5>

Problems:
- ...
- ...

Revise: YES or NO

Revision instructions:
- ...
- ...

User request:
{user_request}

Story:
{story}
"""
    return call_model(prompt, max_tokens=550, temperature=0.1)


def should_revise(judge_feedback: str) -> bool:
    return "Revise: YES" in judge_feedback


def rewriter_agent(
    user_request: str,
    story: str,
    judge_feedback: str,
    age_band: str,
    style: str,
    custom_style: str,
    length: str,
    child_name: str = "",
) -> str:
    """
    Revise the story using the judge's feedback.
    """
    style_instruction = build_style_instruction(style, custom_style)
    normalized_length = normalize_length(length)

    prompt = f"""
You are a careful editor revising a children's bedtime story for ages {age_band}.

Your job is to fix only what the judge flagged — not to rewrite the whole story.

Preservation rules (follow these first):
- Keep all character names exactly as written.
- Keep any sentence or paragraph not mentioned in the judge's problems.
- Keep the opening sentence unless it was specifically flagged.
- Keep the ending paragraph unless it was specifically flagged.
- Keep all dialogue that was not flagged.
- Make the minimum change that fixes each problem.

Fix rules:
- If a sentence is too long: split it, not rewrite it.
- If a word is too advanced: replace only that word, not the whole sentence.
- If an emotion is labeled ("she felt scared"): rewrite just that phrase as an action ("her hands gripped the blanket").
- If the resolution relies on luck or an adult: give the character a simple idea that solves the problem themselves.
- If the ending isn't sleep-ready: soften only the final paragraph.
- If the style doesn't match: adjust tone and energy without changing the plot.

Non-negotiable requirements:
- Title stays on the first line.
- Content remains age-appropriate and emotionally safe for ages {age_band}.
- Style: {style_instruction} — custom style notes are mandatory constraints.
- Target length: {normalized_length}
- Main character: keep exactly who the user specified.
- Child name field: {child_name if child_name else "none"} — only use if the user explicitly asked for it.

User request:
{user_request}

Original story:
{story}

Judge feedback:
{judge_feedback}

Write only the improved final story. No commentary.
"""
    return call_model(prompt, max_tokens=1700, temperature=0.3)


def feedback_agent(
    user_request: str,
    story: str,
    user_feedback: str,
    age_band: str,
    style: str,
    custom_style: str,
    length: str,
    child_name: str = "",
) -> str:
    """
    Revise the story based on user feedback, preserving as much of the
    existing story as possible unless broader changes are requested.
    """
    style_instruction = build_style_instruction(style, custom_style)
    normalized_length = normalize_length(length)

    prompt = f"""
You are a surgical editor for a children's bedtime story targeting ages {age_band}.

The user wants a specific change. Your job is to make exactly that change and nothing else.

Editing rules — read these before touching anything:
- If the user asks to change a single word, name, sentence, or small detail: update only those specific parts. Every other word stays identical.
- If the user asks to change a scene or section: rewrite only that section. Everything before and after stays word-for-word.
- If the user asks for a broader rewrite (different ending, different character, different tone): then you may rewrite more, but still preserve what does not need to change.
- Do not improve, polish, or "while I'm at it" touch anything the user did not mention.
- Do not change character names unless the user explicitly asks.
- Do not change the tone, pacing, or style unless the user explicitly asks.

Non-negotiable requirements:
- Title stays on the first line.
- Story remains age-appropriate and emotionally safe for ages {age_band}.
- Language stays simple and clear.
- Style: {style_instruction} — custom style notes are mandatory unless the user asks to change them.
- Target length: {normalized_length}
- Main character: keep exactly who the user specified in the original request.
- Child name field: {child_name if child_name else "none"} — only use if the user explicitly asked for it.

Original user request:
{user_request}

Current story:
{story}

User feedback:
{user_feedback}

Write only the revised story. No commentary, no notes.
"""
    return call_model(prompt, max_tokens=1700, temperature=0.2)


def parse_judge_scores(judge_feedback: str) -> Dict[str, Any]:
    """
    Parse judge feedback into a structured dictionary for Streamlit display.
    """
    fields = [
        "Age appropriateness",
        "Language simplicity",
        "Coherence",
        "Bedtime suitability",
        "Instruction following",
        "Overall quality",
    ]

    scores: Dict[str, Any] = {}

    for field in fields:
        pattern = rf"{re.escape(field)}:\s*([1-5])"
        match = re.search(pattern, judge_feedback, re.IGNORECASE)
        scores[field] = int(match.group(1)) if match else None

    revise_match = re.search(r"Revise:\s*(YES|NO)", judge_feedback, re.IGNORECASE)
    scores["Revise"] = revise_match.group(1).upper() if revise_match else "UNKNOWN"

    return scores


def generate_story_pipeline(
    user_request: str,
    age_band: str,
    style: str,
    custom_style: str,
    length: str,
    child_name: str = "",
) -> Dict[str, str]:
    """
    Main generation pipeline:
    planner -> writer -> judge -> optional rewrite
    """
    effective_child_name = child_name if should_include_child_name(user_request, child_name) else ""

    story_plan = planner_agent(
        user_request, age_band, style, custom_style, length, effective_child_name
    )
    draft_story = writer_agent(
        user_request, story_plan, age_band, style, custom_style, length, effective_child_name
    )
    judge_feedback = judge_agent(user_request, draft_story, age_band)

    if should_revise(judge_feedback):
        final_story = rewriter_agent(
            user_request=user_request,
            story=draft_story,
            judge_feedback=judge_feedback,
            age_band=age_band,
            style=style,
            custom_style=custom_style,
            length=length,
            child_name=effective_child_name,
        )
    else:
        final_story = draft_story

    return {
        "story_plan": story_plan,
        "draft_story": draft_story,
        "judge_feedback": judge_feedback,
        "final_story": final_story,
    }


def revise_story_with_feedback(
    user_request: str,
    current_story: str,
    user_feedback: str,
    age_band: str,
    style: str,
    custom_style: str,
    length: str,
    child_name: str = "",
) -> Dict[str, str]:
    """
    User-feedback revision flow, followed by a judge pass.
    """
    effective_child_name = (
        child_name if should_include_child_name(f"{user_request}\n{user_feedback}", child_name) else ""
    )

    revised_story = feedback_agent(
        user_request=user_request,
        story=current_story,
        user_feedback=user_feedback,
        age_band=age_band,
        style=style,
        custom_style=custom_style,
        length=length,
        child_name=effective_child_name,
    )

    judge_feedback = judge_agent(user_request, revised_story, age_band)

    return {
        "revised_story": revised_story,
        "judge_feedback": judge_feedback,
    }


if __name__ == "__main__":
    print("Bedtime Story Engine Test")
    print("-" * 30)

    user_request = input("What kind of story do you want to hear? ").strip()
    age_band = input("Age band (5-7 or 8-10): ").strip() or "5-7"
    style = input(
        "Story style (Calm & Cozy, Classic Bedtime, Silly & Playful, Magical Adventure, Animal Adventure, Friendship Story, Brave Little Quest): "
    ).strip() or "Classic Bedtime"
    custom_style = input("Custom style notes (optional): ").strip()
    length = input("Story length (Short, Medium, Long): ").strip() or "Medium"
    child_name = input("Optional child name: ").strip()

    result = generate_story_pipeline(
        user_request=user_request,
        age_band=age_band,
        style=style,
        custom_style=custom_style,
        length=length,
        child_name=child_name,
    )

    print("\n=== STORY PLAN ===\n")
    print(result["story_plan"])

    print("\n=== JUDGE FEEDBACK ===\n")
    print(result["judge_feedback"])

    print("\n=== FINAL STORY ===\n")
    print(result["final_story"])