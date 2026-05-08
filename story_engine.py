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
    """
    Send a single prompt to the OpenAI model and return the text response.
    We intentionally keep the same model as the starter code.
    """
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
    """
    Combine a preset style with optional free-form user style guidance.
    """
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
    """
    Include child name only when user explicitly asks for it.
    """
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
    """
    Create a short story plan before generating the full story.
    """
    style_instruction = build_style_instruction(style, custom_style)
    normalized_length = normalize_length(length)

    prompt = f"""
You are a planner for children's stories for ages {age_band}.

Your job is to create a short, clear, age-appropriate outline based on the user's request.

Requirements:
- Follow the user's request closely
- The story may be calm, playful, magical, adventurous, or funny depending on the request
- Keep the story emotionally safe and appropriate for children ages {age_band}
- Use a clear beginning, middle, and end
- Include a small challenge or point of tension, but keep it age appropriate
- End with a satisfying, reassuring, or heartwarming resolution
- Style: {style_instruction}
- Treat custom style guidance as required when provided (for example suspense, humor, or dialogue preferences)
- Target story length: {normalized_length}
- Main character priority: strictly preserve the main character from the user's request.
- Child name field: {child_name if child_name else "none"}
- Never replace or rename the main character with the child name unless the user explicitly requests that rename.

User request:
{user_request}

Return exactly in this format:

Title idea:
Main character:
Setting:
Beginning:
Small challenge:
Resolution:
Ending feeling:
Vocabulary level:
"""
    return call_model(prompt, max_tokens=260, temperature=0.2)


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
You are an expert storyteller for children ages {age_band}.

Write an age-appropriate story using the user request and plan below.

Requirements:
- Begin with a short title on the first line
- After the title, write the story in short readable paragraphs
- Use simple, clear language appropriate for ages {age_band}
- Match both the selected style and any custom style notes
- Treat custom style notes as mandatory constraints when provided.
- If custom style notes ask for suspense, include gentle age-appropriate suspense beats.
- The story may be calm, playful, magical, adventurous, funny, or exciting depending on the user's request
- If the story is adventurous or playful, allow energy and excitement while keeping it age-appropriate
- Avoid frightening, graphic, disturbing, or overly intense content
- Include a clear beginning, middle, and end
- End with a satisfying and emotionally safe feeling
- Length: {normalized_length}
- Main character priority: strictly preserve the main character from the user's request.
- Child name field: {child_name if child_name else "none"}
- Never replace or rename the main character with the child name unless the user explicitly requests that rename.

User request:
{user_request}

Story plan:
{story_plan}

Write only the final story.
"""
    max_tokens = 2800 if length == "Long" else 1700
    story = call_model(prompt, max_tokens=max_tokens, temperature=0.65)

    min_words, _ = target_word_range(length)
    if word_count(story) < min_words:
        expand_prompt = f"""
You are improving a children's story for ages {age_band}.

The story is too short for the requested length.
Expand it while preserving the same characters, tone, and plot.

Requirements:
- Keep the title on the first line
- Keep the same main character from the user request
- Do not rename characters
- Keep content age-appropriate and emotionally safe
- Keep style: {style_instruction}
- Ensure the final story is at least {min_words} words

User request:
{user_request}

Current short story:
{story}

Return only the expanded final story.
"""
        story = call_model(expand_prompt, max_tokens=max_tokens, temperature=0.45)

    return story


def judge_agent(user_request: str, story: str, age_band: str) -> str:
    """
    Evaluate the story for quality and age appropriateness.
    """
    prompt = f"""
You are a strict but kind evaluator for children's stories for ages {age_band}.

Evaluate the story on these criteria from 1 to 5:
- age appropriateness
- language simplicity
- coherence
- bedtime suitability
- instruction following
- overall quality

Judge using this guidance:
- Stories should be age appropriate, emotionally safe, and easy to understand
- The energy level should match the requested style
- Adventurous, funny, or magical stories are allowed if they remain suitable for children
- Bedtime suitability means the story should not be disturbing, overwhelming, or frightening, and should end in a reassuring or satisfying way
- Language simplicity means short, clear, child-friendly wording
- Coherence means the story has a clear flow and resolution
- Instruction following means the story matches the user's request

Also look for:
- scary or upsetting content
- vocabulary that is too advanced
- confusing transitions
- too much intensity for the age group
- anything that feels too dense or hard to follow

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
You are revising a story for children ages {age_band}.

Improve the story using the judge's feedback.

Requirements:
- Keep the main story idea and heart of the story
- Keep or improve the title on the first line
- Make the language simpler where needed
- Remove anything scary, confusing, or too intense
- Keep the story aligned with the requested style and energy
- Treat custom style notes as required constraints when provided.
- If custom style notes request suspense, keep it gentle and age-appropriate rather than scary.
- Use short readable paragraphs
- Preserve a clear story arc
- Style: {style_instruction}
- Target length: {normalized_length}
- Main character priority: strictly preserve the main character from the user's request.
- Child name field: {child_name if child_name else "none"}
- Never replace or rename the main character with the child name unless the user explicitly requests that rename.

User request:
{user_request}

Original story:
{story}

Judge feedback:
{judge_feedback}

Write only the improved final story.
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
You are revising a children's story for ages {age_band}.

Revise the story based on the user's feedback while preserving as much of the current story as possible.

Very important editing rules:
- If the user asks for a specific local change, make only that change
- Keep all unchanged parts as close to the original as possible
- Do not rewrite the whole story unless the user clearly asks for a broader rewrite
- If the user asks to change a name, word, sentence, line, or small detail, only update the relevant parts
- Preserve tone, structure, and meaning unless the user asks otherwise
- Preserve the selected style and custom style unless the user asks to change them
- Treat custom style notes as required constraints when provided.
- If custom style notes request suspense, keep it gentle and age-appropriate rather than scary.

Requirements:
- Keep the story age appropriate
- Keep language simple and clear
- Keep or improve the title on the first line
- Use short readable paragraphs
- Style: {style_instruction}
- Target length: {normalized_length}
- Main character priority: strictly preserve the main character from the user's request.
- Child name field: {child_name if child_name else "none"}
- Never replace or rename the main character with the child name unless the user explicitly requests that rename.

Original user request:
{user_request}

Current story:
{story}

User feedback:
{user_feedback}

Write only the revised story.
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