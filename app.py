# app.py
import concurrent.futures
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh  # pip install streamlit-autorefresh
from streamlit import components  # client side plotly animation
from functions import insert_highlights, _worker  # (text, spans_with_skills) -> HTML
from data import data_df, persons

# ---- Streamlit Setup ----
st.set_page_config(page_title="ESCO Dashboard", layout="wide")

# ---- CSS for Tooltips ----
st.markdown("""
<style>
/* Container overflows */
[data-testid="stMarkdownContainer"],
[data-testid="stElementContainer"],
[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]{ overflow: visible !important; }

/* Trigger */
.es-tooltip{ position:relative; display:inline-block; }
.es-tooltip mark{ background:#fef08a; padding:0 .14em; border-radius:4px; }
.es-tooltip mark:focus-visible{ outline:2px solid #2563eb; outline-offset:2px; }

/* Card with flip helpers */
.es-card{
  position:absolute; inset:auto auto auto 0;
  z-index:9999; min-width:260px; max-width:420px;
  padding:12px 14px; border:1px solid #e2e8f0; border-radius:10px; background:#fff;
  box-shadow:0 10px 32px rgba(0,0,0,.15);
  font-size:.92em; line-height:1.5;
  visibility:hidden; opacity:0; translate:0 8px;
  transition:opacity .12s ease, translate .12s ease;
  max-height:42vh; overflow:auto; word-wrap:break-word;
}
.es-tooltip[data-pos="right"] .es-card{ inset:auto 0 auto auto; }
.es-tooltip[data-pos="top"] .es-card{ inset:auto auto 100% 0; translate:0 -8px; }

@media (max-width:900px){ .es-card{ left:auto; right:0; } }

/* Show rules */
.es-tooltip:hover .es-card,
.es-tooltip:focus-within .es-card,
.es-card:hover{ visibility:visible; opacity:1; translate:0 0; }

/* Caret + hover bridge */
.es-card::before{
  content:""; position:absolute; top:-8px; left:16px; width:0; height:0;
  border:8px solid transparent; border-bottom-color:#fff;
  filter:drop-shadow(0 -1px 0 #e2e8f0);
}
.es-card::after{ content:""; position:absolute; top:-10px; left:0; right:0; height:12px; }
.es-tooltip[data-pos="top"] .es-card::before{
  top:auto; bottom:-8px; border:8px solid transparent; border-top-color:#fff;
  filter:drop-shadow(0 1px 0 #e2e8f0);
}

/* Tooltip inner container */
.es-tip{ max-width:520px; padding:4px 0; }

/* Triplet-Container mit Rahmen */
.es-item{
  display:grid; grid-template-rows:auto auto auto; gap:8px;
  padding:10px; border:1px solid #e5e7eb; border-radius:10px;
  margin:10px 0; background:#fff;
}
.es-item + .es-item{ margin-top:12px; }
.es-item:hover{ box-shadow:0 6px 18px rgba(0,0,0,.06); }

/* 1) Grüner Kreis = Skill */
.es-skill{
  width:100%; height:80px; border-radius:8px;
  background:#10b981; color:#fff; display:grid; place-items:center;
  font-weight:700; font-size:14pt; line-height:1; text-align:center;
  border:1px solid #059669; padding:4px;
  word-break:break-word;
}

/* 2) Graues Quadrat = Span */
.es-span{
  display:flex; align-items:center; justify-content:flex-start;
  min-height:44px; min-width:44px; padding:6px 8px;
  border:1px solid #e2e8f0; border-radius:8px;
  background:#f3f4f6; color:#374151;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  font-size:12px; line-height:1.35; word-break:break-word;
}

/* 3) Reason als Accordion-Button */
.es-acc{ border:0; padding:0; }
.es-acc>summary{
  display:inline-flex; align-items:center; gap:8px;
  padding:6px 10px; border:1px solid #e5e7eb; border-radius:8px;
  background:#f9fafb; color:#111827; font-weight:600; font-size:.9em;
  cursor:pointer; list-style:none; user-select:none;
  transition:background .12s ease, border-color .12s ease;
}
.es-acc>summary:hover{ background:#f3f4f6; }
.es-acc>summary::-webkit-details-marker{ display:none; }
.es-acc>summary::after{ content:"▸"; font-size:.9em; transform:translateY(1px); margin-left:4px; }
.es-acc[open]>summary::after{ content:"▾"; }

/* Inhalt des Accordions */
.es-reason{
  margin-top:8px; padding:8px 10px;
  border:1px dashed #d1d5db; border-radius:8px;
  background:#fff; color:#374151; font-size:.88em; line-height:1.4;
}
</style>

""", unsafe_allow_html=True)

# ---- State ----
DEFAULT_GOAL = "I want to go outside more often"
DEFAULT_INTERESTS = "Computer Games, Cinema, Pets"

if "task_idx" not in st.session_state: st.session_state.task_idx = 0
if "executor" not in st.session_state: st.session_state.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
if "futures" not in st.session_state: st.session_state.futures = {}      # {job_key: Future}
if "poll_counts" not in st.session_state: st.session_state.poll_counts = {}  # {job_key: int}
if "last_score" not in st.session_state: st.session_state.last_score = {}  # {job_key: float 0..100}

# setting per person
if "goals" not in st.session_state:
    st.session_state.goals = {i: DEFAULT_GOAL for i in range(len(persons))}
if "interests" not in st.session_state:
    st.session_state.interests = {i: DEFAULT_INTERESTS for i in range(len(persons))}

NUM_TASKS = len(data_df)

# Headline
st.title("ESCO Dashboard")

# ---- Person-Settings ----
st.markdown("#### Person-Settings")
ps_col1, ps_col2, ps_col3, ps_col4 = st.columns([1,2,2,0.5], vertical_alignment="bottom")
with ps_col1:
    person_idx = st.selectbox(
        "Choose Person",
        options=list(range(len(persons))),
        format_func=lambda i: f"Person {i + 1}",
        key="person_sel",
        label_visibility="visible",
    )

# defaults per person
_cur_goal = st.session_state.goals.get(person_idx, DEFAULT_GOAL)
_cur_interests = st.session_state.interests.get(person_idx, DEFAULT_INTERESTS)
with ps_col2:
    ui_goal = st.text_input("Goal", value=_cur_goal, key=f"goal_{person_idx}")
with ps_col3:
    ui_interests = st.text_input("Interests", value=_cur_interests, key=f"interests_{person_idx}")
with ps_col4:
    if st.button("Set", key="apply_person_settings"):
        st.session_state.goals[person_idx] = ui_goal
        st.session_state.interests[person_idx] = ui_interests
        # Recompute erzwingen
        st.session_state.futures = {}
        st.rerun()

row = data_df.iloc[st.session_state.task_idx]

# ---- Activity-Text + Spans ----
st.markdown("#### Activity Text")
col1, col2, col3 = st.columns([2,1,2], vertical_alignment="bottom")

with col1:
    if st.button("◀", use_container_width=True) and st.session_state.task_idx > 0:
        st.session_state.task_idx -= 1
        st.rerun()
with col2:
    st.button(str(st.session_state.task_idx), use_container_width=True, key="task_id_btn", disabled=True)
with col3:
    if st.button("▶", use_container_width=True) and st.session_state.task_idx < NUM_TASKS-1:
        st.session_state.task_idx += 1
        st.rerun()

detailed = row.get("y_pred_detailed") or []
spans = [d for d in detailed if isinstance(d, dict) and d.get("span") and (d.get("needed") or d.get("optional") or d.get("trainable"))]
text_html = insert_highlights(row["X"], spans)
st.markdown(f"""
<div style="position:relative; overflow:visible;
            border:1px solid #e2e8f0; border-radius:10px;
            padding:12px; background:white">
  {text_html}
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# ---- Gauge + Reason ----

# save Future
pskills = persons[person_idx]
goal_text = st.session_state.goals.get(person_idx, DEFAULT_GOAL)
interests_text = st.session_state.interests.get(person_idx, DEFAULT_INTERESTS)
job_key = f"{st.session_state.task_idx}:{person_idx}"

if job_key not in st.session_state.futures:
    st.session_state.futures[job_key] = st.session_state.executor.submit(
        _worker, row["X"], detailed, pskills, goal_text, interests_text, person_idx
    )
    st.session_state.poll_counts[job_key] = 0

fut = st.session_state.futures[job_key]
if not fut.done():
    st_autorefresh(interval=1000, key=f"poll_{job_key}", limit=30)

# result
res = {"score": 0.0, "expl": "Calculating...", "expl_short": ""}
if fut.done():
    try:
        res = fut.result()
    except Exception as e:
        res = {"score": 0.0, "expl": f"Fehler: {type(e).__name__}", "expl_short": ""}

end_pct  = round(float(res["score"]) * 100.0, 1)
prev_pct = float(st.session_state.last_score.get(job_key, 0.0))

col_gauge, col_expl = st.columns([1,1])

with col_gauge:
    st.subheader("Match Score")

    # Plotly: aniamte start_value to end_value
    fig = go.Figure(
        data=[go.Indicator(
            mode="gauge+number",
            value=prev_pct,
            number={"suffix": "%", "valueformat": ".1f"},
            gauge={"axis": {"range": [0, 100]}},
            title={"text": f"Person {person_idx + 1}"}
        )],
        frames=[go.Frame(data=[go.Indicator(value=end_pct)])] if fut.done() else []
    )
    fig.update_layout(height=320, margin=dict(l=20, r=20, t=40, b=20))

    # html export + client-side animation trigger
    html = fig.to_html(include_plotlyjs="cdn", full_html=False)
    if fut.done():
        html += """
<script>
const gd = window.frameElement ? window.frameElement.parentElement.querySelector('.plotly-graph-div') : document.querySelector('.plotly-graph-div');
if (gd) {
  Plotly.animate(gd, null, {transition:{duration:800, easing:'cubic-in-out'}, frame:{duration:800}});
}
</script>
"""
    components.v1.html(html, height=320)

# set explanation
with col_expl:
    st.subheader("Reason")
    if fut.done():
        st.markdown(res.get("expl_short") or "No short explanation.")
        with st.expander("More details"):
            st.write(res.get("expl") or "")
    else:
        st.write("Berechne...")

# check for final score
if fut.done():
    st.session_state.last_score[job_key] = end_pct

st.markdown("---")

# ---- Skill-table with hover cards ----
st.markdown("#### Skill-Tabelle")

y_true = set(row.get("Y") or [])
y_pred = set(row.get("y_pred") or [])
idx = {}
for d in detailed:
    sk = d.get("skill")
    if sk:
        idx.setdefault(sk, []).append(d)

# helper functions
def _flag_any(skill, key):
    return any(bool(o.get(key)) for o in idx.get(skill, []))

def _uniq_reasons(skill):
    seen, out = set(), []
    for o in idx.get(skill, []):
        r = (o.get("reason") or o.get("why") or "").strip()
        if r and r not in seen:
            seen.add(r); out.append(r)
    return out

def _esc(s: str) -> str:
    return (str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"))

all_skills = sorted(set(y_true) | set(y_pred) | set(idx.keys()))
p_set = set(persons[person_idx])

rows = []
for sk in all_skills:
    needed  = _flag_any(sk, "needed")
    optional= _flag_any(sk, "optional")
    train   = _flag_any(sk, "trainable")
    gt      = sk in y_true

    if gt and needed:         group = 0
    elif gt and optional:     group = 1
    elif (not gt) and needed: group = 3
    elif gt and (not needed): group = 2
    elif gt or needed or optional or train: group = 4
    else:                     group = 5

    reasons = _uniq_reasons(sk)
    if reasons:
        reason_html = "".join(f'<div class="es-reason">{_esc(r)}</div>' for r in reasons)
        skill_cell = (
            f'<span class="es-tooltip" tabindex="0">'
            f'  <mark>{_esc(sk)}</mark>'
            f'  <div class="es-card"><div class="es-tip">'
            f'    <details class="es-acc" open><summary>Reasons</summary>{reason_html}</details>'
            f'  </div></div>'
            f'</span>'
        )
    else:
        skill_cell = _esc(sk)

    rows.append({
        "_group": group,
        "Skill": skill_cell,
        "GT": "x" if gt else "",
        "Needed": "x" if needed else "",
        "Optional": "x" if optional else "",
        "Trainable": "x" if train else "",
        "Person": "x" if sk in p_set else "",
    })

df = pd.DataFrame(rows).sort_values(["_group","Skill"], kind="mergesort").reset_index(drop=True)
row_groups = df["_group"].to_list()
df_disp = df.drop(columns=["_group"])

cmap = {0:"#dcfce7", 1:"#FFE7BA", 2:"#fee2e2", 3:"#ff6961", 4:"#e0e7ff", 5:"#ffffff"}

# manual render of dataframe as HTML table
cols = list(df_disp.columns)
html = [
    '<table class="dataframe" style="width:100%; border-collapse:separate; border-spacing:0; font-size:14px;">',
    '<thead><tr>',
]
for c in cols:
    html.append(f'<th style="text-align:left; padding:8px; border-bottom:1px solid #e2e8f0;">{_esc(c)}</th>')
html.append('</tr></thead><tbody>')

for i, r in df_disp.iterrows():
    bg = cmap.get(int(row_groups[i]), "#ffffff")
    html.append(f'<tr style="background:{bg};">')
    for c in cols:
        html.append(f'<td style="padding:6px 8px; border-bottom:1px solid #f1f5f9;">{r[c]}</td>')
    html.append('</tr>')

html.append('</tbody></table>')
st.markdown("".join(html), unsafe_allow_html=True)