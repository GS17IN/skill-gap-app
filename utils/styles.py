def inject_styles():
    """
    Inject global CSS design system.
    Call at top of every page.
    """
    import streamlit as st
    st.markdown("""
    <style>
    /* ── Google Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

    /* ── CSS Variables ── */
    :root {
        --bg-primary:    #0A0E1A;
        --bg-secondary:  #111827;
        --bg-card:       #161D2E;
        --bg-card-hover: #1C2438;
        --accent-cyan:   #00D4FF;
        --accent-amber:  #FFB800;
        --accent-green:  #00E676;
        --accent-red:    #FF4560;
        --text-primary:  #E8EDF5;
        --text-secondary:#8892A4;
        --border:        rgba(0, 212, 255, 0.15);
        --border-hover:  rgba(0, 212, 255, 0.4);
        --glow-cyan:     0 0 20px rgba(0, 212, 255, 0.15);
        --glow-amber:    0 0 20px rgba(255, 184, 0, 0.15);
        --font-mono:     'Space Mono', monospace;
        --font-body:     'DM Sans', sans-serif;
        --radius:        12px;
        --radius-sm:     8px;
    }

    /* ── Base ── */
    .stApp {
        background: var(--bg-primary) !important;
        font-family: var(--font-body) !important;
    }

    /* ── Hide Streamlit branding ── */
    #MainMenu, footer, header { visibility: hidden; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] * {
        font-family: var(--font-body) !important;
    }

    /* ── Page title ── */
    h1 {
        font-family: var(--font-mono) !important;
        color: var(--text-primary) !important;
        letter-spacing: -0.5px !important;
        border-bottom: 2px solid var(--accent-cyan) !important;
        padding-bottom: 12px !important;
        margin-bottom: 24px !important;
    }

    /* ── Subheaders ── */
    h2, h3 {
        font-family: var(--font-mono) !important;
        color: var(--text-primary) !important;
        letter-spacing: -0.3px !important;
    }
    h3::before {
        content: '▸ ';
        color: var(--accent-cyan);
    }

    /* ── Metric cards ── */
    [data-testid="metric-container"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 16px !important;
        box-shadow: var(--glow-cyan) !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="metric-container"]:hover {
        border-color: var(--border-hover) !important;
        box-shadow: 0 0 30px rgba(0, 212, 255, 0.25) !important;
    }
    [data-testid="metric-container"] label {
        color: var(--text-secondary) !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        font-family: var(--font-mono) !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: var(--accent-cyan) !important;
        font-family: var(--font-mono) !important;
        font-size: 1.6rem !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: transparent !important;
        border: 1.5px solid var(--accent-cyan) !important;
        color: var(--accent-cyan) !important;
        font-family: var(--font-mono) !important;
        font-size: 0.85rem !important;
        letter-spacing: 1px !important;
        padding: 10px 24px !important;
        border-radius: var(--radius-sm) !important;
        transition: all 0.2s ease !important;
        text-transform: uppercase !important;
    }
    .stButton > button:hover {
        background: var(--accent-cyan) !important;
        color: var(--bg-primary) !important;
        box-shadow: var(--glow-cyan) !important;
    }
    .stButton > button[kind="primary"] {
        background: var(--accent-cyan) !important;
        color: var(--bg-primary) !important;
        font-weight: 700 !important;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 0 30px rgba(0, 212, 255, 0.4) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Input fields ── */
    .stTextInput input, .stSelectbox select,
    .stNumberInput input {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: var(--radius-sm) !important;
        font-family: var(--font-body) !important;
    }
    .stTextInput input:focus, .stSelectbox select:focus {
        border-color: var(--accent-cyan) !important;
        box-shadow: var(--glow-cyan) !important;
    }

    /* ── File uploader ── */
    [data-testid="stFileUploader"] {
        background: var(--bg-card) !important;
        border: 2px dashed var(--border) !important;
        border-radius: var(--radius) !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: var(--accent-cyan) !important;
        box-shadow: var(--glow-cyan) !important;
    }

    /* ── DataFrames ── */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        overflow: hidden !important;
    }

    /* ── Expanders ── */
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-primary) !important;
        font-family: var(--font-mono) !important;
        font-size: 0.85rem !important;
    }
    .streamlit-expanderContent {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
        border-radius: 0 0 var(--radius-sm) var(--radius-sm) !important;
    }

    /* ── Alerts ── */
    .stSuccess {
        background: rgba(0, 230, 118, 0.1) !important;
        border-left: 3px solid var(--accent-green) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--accent-green) !important;
    }
    .stWarning {
        background: rgba(255, 184, 0, 0.1) !important;
        border-left: 3px solid var(--accent-amber) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--accent-amber) !important;
    }
    .stError {
        background: rgba(255, 69, 96, 0.1) !important;
        border-left: 3px solid var(--accent-red) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--accent-red) !important;
    }
    .stInfo {
        background: rgba(0, 212, 255, 0.08) !important;
        border-left: 3px solid var(--accent-cyan) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-primary) !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-card) !important;
        border-radius: var(--radius-sm) !important;
        padding: 4px !important;
        gap: 4px !important;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: var(--font-mono) !important;
        font-size: 0.8rem !important;
        color: var(--text-secondary) !important;
        border-radius: 6px !important;
        padding: 8px 16px !important;
    }
    .stTabs [aria-selected="true"] {
        background: var(--accent-cyan) !important;
        color: var(--bg-primary) !important;
    }

    /* ── Progress bar ── */
    .stProgress > div > div {
        background: linear-gradient(
            90deg, var(--accent-cyan), #0099FF
        ) !important;
        border-radius: 4px !important;
    }

    /* ── Sliders ── */
    .stSlider [data-baseweb="slider"] [role="slider"] {
        background: var(--accent-cyan) !important;
        border-color: var(--accent-cyan) !important;
    }

    /* ── Multiselect ── */
    .stMultiSelect [data-baseweb="tag"] {
        background: rgba(0, 212, 255, 0.15) !important;
        border: 1px solid var(--accent-cyan) !important;
        color: var(--accent-cyan) !important;
        font-family: var(--font-mono) !important;
        font-size: 0.75rem !important;
    }

    /* ── Spinner ── */
    .stSpinner > div {
        border-top-color: var(--accent-cyan) !important;
    }

    /* ── Code blocks ── */
    .stCode, code {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        font-family: var(--font-mono) !important;
        color: var(--accent-cyan) !important;
    }

    /* ── Custom components ── */

    /* Stat card */
    .stat-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 20px 24px;
        box-shadow: var(--glow-cyan);
        transition: all 0.2s ease;
        margin-bottom: 12px;
    }
    .stat-card:hover {
        border-color: var(--border-hover);
        box-shadow: 0 0 30px rgba(0,212,255,0.2);
        transform: translateY(-2px);
    }
    .stat-card .label {
        color: var(--text-secondary);
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-family: var(--font-mono);
        margin-bottom: 8px;
    }
    .stat-card .value {
        color: var(--accent-cyan);
        font-size: 2rem;
        font-family: var(--font-mono);
        font-weight: 700;
        line-height: 1;
    }
    .stat-card .sub {
        color: var(--text-secondary);
        font-size: 0.8rem;
        margin-top: 4px;
    }

    /* Section divider */
    .section-divider {
        height: 1px;
        background: linear-gradient(
            90deg,
            var(--accent-cyan),
            transparent
        );
        margin: 28px 0;
        border: none;
    }

    /* Skill badge */
    .skill-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-family: var(--font-mono);
        margin: 3px;
        font-weight: 500;
    }
    .skill-badge.high {
        background: rgba(0,230,118,0.12);
        border: 1px solid rgba(0,230,118,0.4);
        color: #00E676;
    }
    .skill-badge.medium {
        background: rgba(255,184,0,0.12);
        border: 1px solid rgba(255,184,0,0.4);
        color: #FFB800;
    }
    .skill-badge.missing {
        background: rgba(255,69,96,0.12);
        border: 1px solid rgba(255,69,96,0.4);
        color: #FF4560;
    }
    .skill-badge.neutral {
        background: rgba(0,212,255,0.1);
        border: 1px solid rgba(0,212,255,0.3);
        color: #00D4FF;
    }

    /* Page header banner */
    .page-banner {
        background: linear-gradient(
            135deg,
            rgba(0,212,255,0.08) 0%,
            rgba(0,153,255,0.04) 50%,
            transparent 100%
        );
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 24px 28px;
        margin-bottom: 28px;
        position: relative;
        overflow: hidden;
    }
    .page-banner::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 3px; height: 100%;
        background: linear-gradient(
            180deg, var(--accent-cyan), transparent
        );
    }
    .page-banner h2 {
        margin: 0 0 8px 0 !important;
        font-size: 1.4rem !important;
        border: none !important;
    }
    .page-banner p {
        margin: 0 !important;
        color: var(--text-secondary) !important;
        font-size: 0.9rem !important;
    }

    /* Gap score bar */
    .gap-bar-wrap {
        background: rgba(255,255,255,0.06);
        border-radius: 6px;
        height: 14px;
        overflow: hidden;
        margin: 8px 0;
    }
    .gap-bar-fill {
        height: 100%;
        border-radius: 6px;
        transition: width 0.8s ease;
    }

    /* Step indicator */
    .step-label {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(0,212,255,0.08);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 6px 14px;
        margin-bottom: 12px;
        font-family: var(--font-mono);
        font-size: 0.75rem;
        color: var(--accent-cyan);
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .step-label .num {
        background: var(--accent-cyan);
        color: var(--bg-primary);
        width: 20px; height: 20px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.7rem;
    }

    /* Job match card */
    .job-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 18px 22px;
        margin-bottom: 10px;
        transition: all 0.2s ease;
    }
    .job-card:hover {
        border-color: var(--border-hover);
        box-shadow: var(--glow-cyan);
    }
    .job-card .score-pill {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-family: var(--font-mono);
        font-size: 0.8rem;
        font-weight: 700;
    }
    .score-high   { background:rgba(0,230,118,0.15);
                    color:#00E676; border:1px solid rgba(0,230,118,0.3); }
    .score-medium { background:rgba(255,184,0,0.15);
                    color:#FFB800; border:1px solid rgba(255,184,0,0.3); }
    .score-low    { background:rgba(255,69,96,0.15);
                    color:#FF4560; border:1px solid rgba(255,69,96,0.3); }

    /* Pipeline log */
    .pipeline-log {
        background: #0D1117;
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 16px;
        font-family: var(--font-mono);
        font-size: 0.8rem;
        color: var(--accent-green);
        line-height: 1.8;
        max-height: 300px;
        overflow-y: auto;
    }

    /* Trend badge */
    .trend-up   { color: #00E676; font-family: var(--font-mono);
                  font-size: 0.85rem; }
    .trend-down { color: #FF4560; font-family: var(--font-mono);
                  font-size: 0.85rem; }

    </style>
    """, unsafe_allow_html=True)


def page_banner(icon, title, description):
    """Render a styled page header banner."""
    import streamlit as st
    st.markdown(f"""
    <div class="page-banner">
        <h2>{icon} {title}</h2>
        <p>{description}</p>
    </div>
    """, unsafe_allow_html=True)


def step_label(num, text):
    """Render a step indicator."""
    import streamlit as st
    st.markdown(f"""
    <div class="step-label">
        <span class="num">{num}</span> {text}
    </div>
    """, unsafe_allow_html=True)


def skill_badges(skills, variant="neutral"):
    """Render a row of skill badges."""
    import streamlit as st
    badges = "".join(
        f'<span class="skill-badge {variant}">{s}</span>'
        for s in sorted(skills)
    )
    st.markdown(
        f'<div style="line-height:2.2">{badges}</div>',
        unsafe_allow_html=True
    )


def gap_bar(pct, label=""):
    """Render a colored gap/coverage progress bar."""
    import streamlit as st
    coverage = 100 - pct
    color    = ("#00E676" if coverage >= 70
                else "#FFB800" if coverage >= 40
                else "#FF4560")
    st.markdown(f"""
    <div style="margin:8px 0">
        <div style="display:flex; justify-content:space-between;
                    margin-bottom:4px">
            <span style="font-family:'Space Mono',monospace;
                         font-size:0.75rem; color:#8892A4">
                {label}
            </span>
            <span style="font-family:'Space Mono',monospace;
                         font-size:0.75rem; color:{color}">
                {coverage:.0f}% covered
            </span>
        </div>
        <div class="gap-bar-wrap">
            <div class="gap-bar-fill"
                 style="width:{coverage}%;
                        background:linear-gradient(
                            90deg,{color},{color}88)">
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def section_divider():
    import streamlit as st
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


def chart_style():
    """Return matplotlib style dict for dark theme charts."""
    return {
        "figure.facecolor":  "#161D2E",
        "axes.facecolor":    "#161D2E",
        "axes.edgecolor":    "#1C2438",
        "axes.labelcolor":   "#8892A4",
        "axes.titlecolor":   "#E8EDF5",
        "xtick.color":       "#8892A4",
        "ytick.color":       "#8892A4",
        "text.color":        "#E8EDF5",
        "grid.color":        "#1C2438",
        "grid.linewidth":    0.8,
    }