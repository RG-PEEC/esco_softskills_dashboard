import textwrap
from typing import Optional
import plotly.graph_objects as go
from plotly.colors import sample_colorscale
import html
import json
from lm_studio_client import LMStudioClient

# singelton LM Studio Client
lm_studio_client = LMStudioClient(model="openai/gpt-oss-20b")


def visualize_score(
        score: float,
        title: Optional[str] = None,
        explanation: Optional[str] = None,
        steps: int = 50,
        wrap: int = 80,
) -> go.Figure:
    """
    0–100% tachometer (red→green) as Plotly gauge.
    - score: 0–100, values are clamped.
    - title: Title above the plot.
    - explanation: Text below the plot (automatic line wrapping).
    - steps: Number of background bands.
    - wrap: Maximum characters per line for line wrapping.
    Note: No fig.show() -> no double rendering in Jupyter.
    """
    s = max(0.0, min(100.0, float(score)))
    cur_col = sample_colorscale("RdYlGn", s / 100.0)[0]

    # Farbverlauf
    step_ranges = []
    for i in range(steps):
        a = 100.0 * i / steps
        b = 100.0 * (i + 1) / steps
        c = sample_colorscale("RdYlGn", (i + 0.5) / steps)[0]
        step_ranges.append({"range": [a, b], "color": c})

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=s,
            number={"suffix": "%", "valueformat": ".1f"},
            title={"text": title or ""},
            gauge={
                "axis": {"range": [0, 100], "tickvals": [0, 25, 50, 75, 100], "ticks": "outside"},
                "bar": {"color": cur_col, "thickness": 0.25},
                "borderwidth": 1,
                "steps": step_ranges,
                "threshold": {"line": {"color": cur_col, "width": 4}, "thickness": 0.85, "value": s},
            },
            domain={"x": [0, 1], "y": [0, 1]},
        )
    )

    # Explanation grows downwards, line breaks via <br>
    lines = 0
    if explanation:
        wrapped = textwrap.fill(str(explanation), width=wrap)
        text = wrapped.replace("\n", "<br>")
        # start underneath the gauge
        fig.add_annotation(
            x=0.5, xref="paper", xanchor="center",
            y=0, yref="paper", yanchor="top", yshift=-8,
            text=text, showarrow=False, align="center"
        )
        lines = text.count("<br>") + 1

    # Layout: additional space below for explanation
    base_bottom = 36  # base margin bottom
    line_height = 18  # margin bottom per line
    extra = max(0, lines) * line_height
    fig.update_layout(
        margin=dict(l=20, r=20, t=50 if title else 20, b=base_bottom + extra),
        height=340 + int(extra * 0.6),
    )

    return fig


def _find_all_occurrences(text: str, needle: str):
    """
    Finds all occurrences of the substring `needle` in the string `text`.

    Returns a list of tuples, where each tuple contains the start and end indices
    of an occurrence of `needle` in `text`. If `needle` is empty, returns an empty list.

    Args:
        text (str): The string to search in.
        needle (str): The substring to search for.

    Returns:
        List[Tuple[int, int]]: List of (start, end) index pairs for each occurrence.
    """
    idxs, i, L = [], 0, len(needle)
    if not needle:
        return idxs
    while True:
        j = text.find(needle, i)
        if j == -1:
            break
        idxs.append((j, j + L))
        i = j + L
    return idxs


def _coverage_labels(text: str, spans_with_skills):
    """
    Returns a list of sets, one for each character in `text`, indicating which skills and reasons
    cover each character position. Each set contains tuples of (skill, reason, span).

    Args:
        text (str): The text to analyze.
        spans_with_skills (list): List of dicts with keys "span", "skill", "reason".

    Returns:
        List[Set[Tuple[str, str, str]]]: Coverage labels for each character position.
    """
    # Initialize coverage: one set per character in text
    cov = [set() for _ in range(len(text))]
    for entry in spans_with_skills:
        span = entry.get("span")
        skill = entry.get("skill")
        reason = entry.get("reason")
        # Skip if span or skill is missing
        if not span or not skill:
            continue
        # Clean up span string
        span = span.replace('"', '').strip()
        # Skip if span is empty or too short
        if not span or len(span) < 2:
            continue
        # Find all occurrences of the span in text
        for s, e in _find_all_occurrences(text, span):
            # Clamp indices to valid range
            s = max(0, min(s, len(text)))
            e = max(0, min(e, len(text)))
            # Mark coverage for each character in the span
            for i in range(s, e):
                cov[i].add((skill, reason, span))
    return cov


def _segments_from_coverage(text: str, cov):
    """
    Splits the text into segments based on coverage labels.

    Each segment is a tuple (start, end, labels), where 'labels' is the set of coverage labels
    for that segment. Segments are created whenever the coverage labels change.

    Args:
        text (str): The input text.
        cov (list): List of sets, one per character, indicating coverage labels.

    Returns:
        list: List of (start, end, labels) tuples for each segment.
    """
    if not text:
        return []
    if not cov:
        return [(0, len(text), set())]
    segments = []
    prev_labels = cov[0]
    start = 0
    # Iterate through text, split at coverage label changes
    for i in range(1, len(text)):
        if cov[i] != prev_labels:
            segments.append((start, i, prev_labels))
            start = i
            prev_labels = cov[i]
    segments.append((start, len(text), prev_labels))
    return segments


def insert_highlights_old(text: str, spans_with_skills):
    """
    Inserts HTML highlights into the text for spans covered by skills and reasons.

    Each segment of the text that is covered by one or more skills/reasons is wrapped in a
    <span> and <mark> tag with a background color. A tooltip card is added for each segment,
    showing the skill, reason, and span information.

    Args:
        text (str): The input text to highlight.
        spans_with_skills (list): List of dicts with keys "span", "skill", "reason".

    Returns:
        str: HTML string with highlights and tooltips.
    """
    cov = _coverage_labels(text, spans_with_skills)
    segs = _segments_from_coverage(text, cov)

    # Color palette for highlights
    palette = [
        "#fde68a", "#fca5a5", "#93c5fd", "#a7f3d0", "#c4b5fd",
        "#f9a8d4", "#fdba74", "#86efac", "#fcd34d", "#fca5a5"
    ]
    combo2color = {}

    parts = []
    for s, e, labels in segs:
        seg_txt_raw = text[s:e]
        seg_txt = html.escape(seg_txt_raw)

        # If no labels or segment is empty, just append the text
        if not labels or seg_txt_raw.strip() == "":
            parts.append(seg_txt)
            continue

        # Create a key for the combination of skills/reasons/spans
        key = tuple(sorted((str(sk) or "", str(rs) or "", str(spa) or "") for (sk, rs, spa) in labels))
        if key not in combo2color:
            combo2color[key] = palette[len(combo2color) % len(palette)]
        color = combo2color[key]

        # Build tooltip card HTML
        tip_rows = []
        for sk, rs, spa in key:
            tip_rows.append(
                f'<div class="row">'
                f'<div class="skill"><b>{html.escape(sk)}</b></div>'
                f'<div class="reason"><strong>Reason</strong>:<br> {html.escape(rs)}</div>'
                f'<div class="span"><strong>Span</strong>:<br> "{html.escape(spa)}"</div>'
                f'<br>'
                f'</div>'
            )
        tip_html = "".join(tip_rows)

        # Wrap the segment in highlight and tooltip HTML
        parts.append(
            f'<span class="es-tooltip">'
            f'<mark style="background:{color}">{seg_txt}</mark>'
            f'<span class="es-card">{tip_html}</span>'
            f'</span>'
        )
    return "".join(parts)


def insert_highlights(text: str, spans_with_skills):
    """
    Inserts HTML highlights into the text for spans covered by skills and reasons.

    Each segment of the text that is covered by one or more skills/reasons is wrapped in a
    <span> and <mark> tag with a background color. A tooltip card is added for each segment,
    showing the skill, reason, and span information.

    Args:
        text (str): The input text to highlight.
        spans_with_skills (list): List of dicts with keys "span", "skill", "reason".

    Returns:
        str: HTML string with highlights and tooltips.
    """
    cov = _coverage_labels(text, spans_with_skills)
    segs = _segments_from_coverage(text, cov)

    # Color palette for highlights
    palette = ["#fde68a", "#fca5a5", "#93c5fd", "#a7f3d0", "#c4b5fd",
               "#f9a8d4", "#fdba74", "#86efac", "#fcd34d", "#fca5a5"]
    combo2color = {}

    parts = []
    for s, e, labels in segs:
        seg_txt_raw = text[s:e]
        seg_txt = html.escape(seg_txt_raw)

        # If no labels or segment is empty, just append the text
        if not labels or seg_txt_raw.strip() == "":
            parts.append(seg_txt)
            continue

        # Consistent color per combination of skills/reasons/spans
        key = tuple(sorted((str(sk) or "", str(rs) or "", str(spa) or "") for (sk, rs, spa) in labels))
        if key not in combo2color:
            combo2color[key] = palette[len(combo2color) % len(palette)]
        color = combo2color[key]

        # Tooltip content: one .es-item per skill in the same span
        items_html = []
        for sk, rs, spa in key:
            items_html.append(f"""
    <div class="es-item">
      <div class="es-skill">{html.escape(sk)}</div>
      <div class="es-span">{html.escape(spa)}</div>
      <details class="es-acc">
        <summary>Reason</summary>
        <div class="es-reason">{html.escape(rs)}</div>
      </details>
    </div>
    """.strip())

        tip_html = (
                '<div class="es-tip">' +
                "".join(items_html) +
                '</div>'
        )

        # Wrap the segment in highlight and tooltip HTML
        parts.append(
            f'<div class="es-tooltip">'
            f'  <mark style="background:{color}">{seg_txt}</mark>'
            f'  <div class="es-card">{tip_html}</div>'
            f'</div>'
        )

    return "".join(parts)


def _extract_json_payload(s):
    """
    Extracts a JSON payload from a string, handling code block formatting.

    If the string contains a Markdown code block (```json or ```), it extracts the content inside.
    Tries to parse the extracted string as JSON. If parsing fails, attempts to strip backticks and whitespace and parse again.
    Returns an empty dict if all parsing attempts fail.

    Args:
        s (str): The input string containing JSON or a code block.

    Returns:
        dict: The parsed JSON object, or an empty dict if parsing fails.
    """
    s = s if isinstance(s, str) else str(s)
    # Extract JSON from Markdown code block if present
    if "```json" in s:
        s = s.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in s:
        s = s.split("```", 1)[1].strip()
    try:
        return json.loads(s)
    except Exception:
        try:
            return json.loads(s.strip("` \n"))
        except Exception:
            return {}


def _build_prompt(
        x_text: str,
        detailed_objs: list,
        person_skills: list,
        goal: str,
        interests: str,
        person_idx: int = 0
) -> str:
    """
    Builds a prompt for skill/activity assessment.

    Args:
        x_text (str): The activity text to be assessed.
        detailed_objs (list): List of skill dicts with 'skill', 'needed', 'optional', 'trainable' keys.
        person_skills (list): List of skills the person has.
        goal (str): The user's goal.
        interests (str): The user's interests.
        person_idx (int, optional): Index of the person (default: 0).

    Returns:
        str: The formatted prompt string for the language model.
    """
    # Create comma-separated lists for needed, optional, and trainable skills
    needed_list = ", ".join([d['skill'] for d in detailed_objs if d.get('needed')])
    optional_list = ", ".join([d['skill'] for d in detailed_objs if d.get('optional')])
    train_list = ", ".join([d['skill'] for d in detailed_objs if d.get('trainable')])

    # Build the prompt string with all relevant information and instructions
    return f"""
Person {person_idx + 1} has the following skills: {', '.join(person_skills)}.
User Goal: {goal}
User Interests: {interests}


Task:
Assess if Person {person_idx + 1} can perform the given activity, based on their skills, goal, and interests.

Activity Text:
{x_text}

Needed Skills:
{needed_list}

Optional Skills:
{optional_list}

Trainable Skills:
{train_list}

Response (JSON):
{{"score":0.0,"explanation":"","explanation_short":"","recommend":false}}

Explanation of Response Fields:
- score: A float value between 0.0 and 1.0 indicating how well Person {person_idx + 1} matches the needed skills for the activity. 1.0 means perfect match, 0.0 means no match.
- explanation: A detailed text (styled nicely with markdown) explaining the reasoning behind the score, mentioning specific skills, goals, interests and spans from the activity text that match or are missing.
- explanation_short: A meaningful one-sentence summary of the explanation. Another sentence mentioning the user's goal and if the activity fits to it would be good. Another sentence mentioning the user's interests and if the activity fits to them. (Example: Strong match (score: 0.86) - the person has the ... skills needed for the ... activity. \n ### Goal Fit: The activity aligns well with the user's goal of ... . \n ### Interest Fit: The activity matches the user's interests in ... .)
- recommend: A boolean value indicating whether Person {person_idx + 1} is recommended for the activity based on the score and explanation.

Style the explanations nicely with markdown, using headings, bullet points, and bold text where appropriate.

IMPORTANT: ALWAYS RESPOND IN THE EXACT JSON FORMAT.

Response (JSON):
{{"score":0.0,"explanation":"","explanation_short":"","recommend":false}}

""".strip()


def _worker(x_text, detailed_objs, person_skills, goal, interests, person_idx=0):
    """
    Calls the language model to assess if a person can perform an activity based on their skills, goal, and interests.

    Args:
        x_text (str): The activity text to be assessed.
        detailed_objs (list): List of skill dicts.
        person_skills (list): List of skills the person has.
        goal (str): The user's goal.
        interests (str): The user's interests.
        person_idx (int, optional): Index of the person (default: 0).

    Returns:
        dict: Contains 'score', 'expl' (explanation), and 'expl_short' (short explanation).
    """
    try:
        # Build prompt for the language model
        prompt = _build_prompt(x_text, detailed_objs, person_skills, goal, interests, person_idx)
        # Call LM Studio model
        raw = lm_studio_client.chat([{"role": "user", "content": prompt}], temperature=0)
        # Extract JSON payload from model response
        payload = _extract_json_payload(raw)
        # Clamp score between 0.0 and 1.0
        score = max(0.0, min(1.0, float(payload.get("score", 0.0))))
        # Get explanation and short explanation
        expl = str(payload.get("explanation", "")) or "No explanation"
        expl_short = str(payload.get("explanation_short", "")) or ""
    except Exception:
        # Fallback values if model call fails
        score, expl, expl_short = 0.0, "Model call failed", ""
    return {"score": score, "expl": expl, "expl_short": expl_short}

