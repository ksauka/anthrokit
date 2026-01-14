import streamlit as st

# Load environment variables from .env file
import env_loader

# Configure page FIRST - before any other Streamlit commands
st.set_page_config(page_title="AI Loan Assistant - Credit Pre-Assessment", layout="wide")

# Hide Streamlit branding for anonymous review (CSS + JavaScript)
st.markdown("""
<style>
/* ===== COMPREHENSIVE STREAMLIT BRANDING REMOVAL ===== */

/* Hide header elements */
#MainMenu {visibility: hidden !important;}
header {visibility: hidden !important;}
[data-testid="stHeader"] {display: none !important;}
[data-testid="stToolbar"] {display: none !important;}
[data-testid="stDecoration"] {display: none !important;}
[data-testid="stStatusWidget"] {display: none !important;}
button[kind="header"] {display: none !important;}

/* Hide footer elements - ALL variations */
footer {visibility: hidden !important; display: none !important;}
[data-testid="stFooter"] {display: none !important;}
footer[data-testid="stFooter"] {display: none !important;}
div[role="contentinfo"] {display: none !important;}
[class*="footer"] {display: none !important;}
[class*="Footer"] {display: none !important;}

/* Hide deploy/manage buttons */
[data-testid="manage-app-button"] {display: none !important;}
.stAppDeployButton {display: none !important;}
.stDeployButton {display: none !important;}

/* ===== HIDE ALL CREATOR ATTRIBUTION ===== */

/* Text links to creator profile */
a[href*="streamlit.io"] {display: none !important;}
a[href*="share.streamlit.io/user"] {display: none !important;}
a[href*="/user/ksauka"] {display: none !important;}
a[target="_blank"][href^="https://share.streamlit.io"] {display: none !important;}

/* Image/Avatar links to creator profile */
a[href*="streamlit.io"] img {display: none !important;}
a[href*="share.streamlit.io"] img {display: none !important;}
a img[src*="avatar"] {display: none !important;}
a img[src*="profile"] {display: none !important;}
img[alt*="creator"] {display: none !important;}
img[alt*="author"] {display: none !important;}

/* Viewer badge containers and links */
.viewerBadge_link__qRIco {display: none !important;}
.viewerBadge_link__Ua7HT {display: none !important;}
.viewerBadge_container__r5tak {display: none !important;}
.viewerBadge_container__2QSob {display: none !important;}
a.viewer-badge {display: none !important;}
[class*="viewerBadge"] {display: none !important;}
[class*="ViewerBadge"] {display: none !important;}

/* Profile/Avatar elements */
[class*="avatar"] {display: none !important;}
[class*="Avatar"] {display: none !important;}
[class*="profile"] {display: none !important;}
[class*="Profile"] {display: none !important;}
[data-testid*="avatar"] {display: none !important;}
[data-testid*="profile"] {display: none !important;}

/* Any div containing creator attribution at bottom of page */
div[class*="creator"] {display: none !important;}
div[class*="author"] {display: none !important;}
div[class*="attribution"] {display: none !important;}

/* Catch-all: any link in bottom 100px of page pointing to streamlit.io */
body > div:last-child a[href*="streamlit.io"] {display: none !important;}
.main > div:last-child a[href*="streamlit.io"] {display: none !important;}

/* Nuclear option: hide entire bottom-most div if it contains streamlit links */
div:has(a[href*="streamlit.io"]) {display: none !important;}

/* Disable pointer events on any remaining visible elements */
a[href*="streamlit.io"],
a[href*="share.streamlit.io"],
img[src*="avatar"],
img[src*="profile"] {
    pointer-events: none !important;
    cursor: default !important;
    display: none !important;
}

/* Remove padding after footer removal */
section.main > div {padding-bottom: 0 !important;}

/* Legacy class hiding */
.css-1v0mbdj {display: none !important;}
</style>

<script>
// JavaScript to forcefully remove Streamlit branding (runs continuously)
(function() {
    function removeStreamlitBranding() {
        // Remove footer elements
        const footers = document.querySelectorAll('footer, [data-testid="stFooter"], [class*="footer"], [class*="Footer"]');
        footers.forEach(el => el.remove());
        
        // Remove header elements
        const headers = document.querySelectorAll('header, [data-testid="stHeader"], #MainMenu');
        headers.forEach(el => el.remove());
        
        // Remove any links to streamlit.io
        const streamlitLinks = document.querySelectorAll('a[href*="streamlit.io"], a[href*="share.streamlit.io"]');
        streamlitLinks.forEach(el => el.remove());
        
        // Remove viewer badges
        const badges = document.querySelectorAll('[class*="viewerBadge"], [class*="ViewerBadge"], .viewer-badge');
        badges.forEach(el => el.remove());
        
        // Remove avatars and profile images
        const avatars = document.querySelectorAll('[class*="avatar"], [class*="Avatar"], [class*="profile"], [class*="Profile"]');
        avatars.forEach(el => {
            // Only remove if it's in a link to streamlit
            const parent = el.closest('a');
            if (parent && parent.href && parent.href.includes('streamlit.io')) {
                parent.remove();
            }
        });
        
        // Remove any div that contains streamlit links
        const allLinks = document.querySelectorAll('a[href*="streamlit.io"]');
        allLinks.forEach(link => {
            const container = link.closest('div');
            if (container) {
                container.remove();
            }
        });
    }
    
    // Run immediately
    removeStreamlitBranding();
    
    // Run every 500ms to catch dynamically added elements
    setInterval(removeStreamlitBranding, 500);
    
    // Also run on DOM changes
    const observer = new MutationObserver(removeStreamlitBranding);
    observer.observe(document.body, { childList: true, subtree: true });
})();
</script>

<meta name="robots" content="noindex, nofollow">
""", unsafe_allow_html=True)

# ===== QUALTRICS/PROLIFIC INTEGRATION (robust final) =====
import time
from typing import Dict
from urllib.parse import unquote, urlparse, parse_qsl, urlencode, urlunparse

def _get_query_params():
    try:
        # Streamlit ≥1.32
        return dict(st.query_params)
    except Exception:
        try:
            # Older Streamlit
            return st.experimental_get_query_params()
        except Exception:
            return {}

def _as_str(v):
    if isinstance(v, list):
        return v[0] if v else ""
    return v if isinstance(v, str) else ""

def _is_safe_return(ru: str) -> bool:
    """Allow https/http + any *.qualtrics.com netloc (handles regional subdomains)."""
    if not ru:
        return False
    try:
        d = unquote(ru)
        # tolerate missing scheme (rare). Qualtrics links should always be https
        if not d.startswith(("http://", "https://")):
            d = "https://" + d
        p = urlparse(d)
        return (p.scheme in ("http", "https")) and ("qualtrics.com" in p.netloc)
    except Exception:
        return False

def _build_final_return(done=True):
    """
    Start with the encoded Qualtrics 'return' URL, decode once,
    ensure it points to Qualtrics, then append pid/cond/done IFF missing.
    """
    rr = st.session_state.get("return_raw", "")
    if not rr or not _is_safe_return(rr):
        return None

    decoded = unquote(rr)
    # normalize scheme if missing (defensive)
    if not decoded.startswith(("http://", "https://")):
        decoded = "https://" + decoded

    p = urlparse(decoded)
    q = dict(parse_qsl(p.query, keep_blank_values=True))

    # only add if not already present
    pid_ss  = st.session_state.get("pid", "")
    cond_ss = st.session_state.get("cond", "")
    prolific_pid_ss = st.session_state.get("prolific_pid", "")
    session_id_ss = st.session_state.get("session_id", "")

    if "pid"  not in q and pid_ss:  q["pid"]  = pid_ss
    if "cond" not in q and cond_ss: q["cond"] = cond_ss
    if "PROLIFIC_PID" not in q and prolific_pid_ss: q["PROLIFIC_PID"] = prolific_pid_ss
    if "session_id" not in q and session_id_ss: q["session_id"] = session_id_ss  # KEY for data linkage
    if "done" not in q:             q["done"] = "1" if done else "0"

    return urlunparse(p._replace(query=urlencode(q, doseq=True)))

# -------------- read & persist params once --------------
_qs      = _get_query_params()
_pid_in  = _as_str(_qs.get("pid", ""))
_cond_in = _as_str(_qs.get("cond", ""))
_ret_in  = _as_str(_qs.get("return", ""))
# Prolific standard parameter
_prolific_pid = _as_str(_qs.get("PROLIFIC_PID", ""))

if "pid" not in st.session_state and _pid_in:
    st.session_state.pid = _pid_in
if "cond" not in st.session_state and _cond_in:
    st.session_state.cond = _cond_in
if "return_raw" not in st.session_state and _ret_in:
    st.session_state.return_raw = _ret_in
# Store Prolific ID separately for research tracking
# Priority: 1) PROLIFIC_PID param (direct from Prolific)
#           2) pid param (from Qualtrics embedded data)
#           3) Manual input (fallback)
if "prolific_pid" not in st.session_state:
    if _prolific_pid:
        st.session_state.prolific_pid = _prolific_pid
    elif _pid_in:
        st.session_state.prolific_pid = _pid_in

# Manual Prolific ID input (ALWAYS show as backup, but optional if coming from Qualtrics)
if not st.session_state.get("prolific_pid"):
    # Coming from Qualtrics but no pid parameter - show manual input
    if st.session_state.get("return_raw"):
        st.warning("⚠️ No participant ID detected. Please enter manually:")
    else:
        st.markdown("### 📋 Study Participation")
        st.markdown("""
        Welcome! To participate in this study, please enter your **Prolific ID**.
        
        You can find this in:
        - Your Prolific dashboard (top-right corner)
        - The study instructions page
        - The Qualtrics survey you came from
        """)
    
    prolific_input = st.text_input(
        "Prolific ID:",
        placeholder="e.g., 5f8e3c2a1b9d4e6f7a8b9c0d",
        help="This identifier connects your app interactions to your survey responses",
        key="prolific_id_input"
    )
    
    if st.button("Continue to Study", type="primary"):
        if prolific_input.strip():
            st.session_state.prolific_pid = prolific_input.strip()
            st.success("✅ ID captured! Loading study...")
            st.rerun()
        else:
            st.error("⚠️ Please enter your Prolific ID to continue.")
    
    st.stop()  # Block execution until ID provided

# boolean flag for UI (sticky footer etc.)
st.session_state.has_return_url = bool(st.session_state.get("return_raw", ""))  # always recompute

# one-shot redirect latch
if "_returned" not in st.session_state:
    st.session_state._returned = False

def back_to_survey(done_flag=True):
    """Single exit path. Call on button click or timeout."""
    if st.session_state._returned:
        return
    
    # Save logger session to GitHub before redirecting
    if 'interaction_logger' in st.session_state:
        try:
            logger = st.session_state.interaction_logger
            logger.end_session(completion_status="completed" if done_flag else "abandoned")
            print(f"[App] Session logged to GitHub: {logger.session_id}")
        except Exception as e:
            print(f"[App] Failed to save logger session: {e}")
    
    final = _build_final_return(done=done_flag)
    if not final:
        st.warning("Return link missing or invalid. Please use your browser Back button.")
        return
    st.session_state._returned = True
    # immediate redirect – robust & no loops
    st.markdown(f'<meta http-equiv="refresh" content="0;url={final}">', unsafe_allow_html=True)
    st.stop()

# handle previously latched redirect (e.g., if Streamlit re-renders mid-redirect)
if st.session_state.get("_returned"):
    final = _build_final_return(done=True)
    if final:
        st.markdown(f'<meta http-equiv="refresh" content="0;url={final}">', unsafe_allow_html=True)
        st.stop()

# set the 3-minute deadline once and track start time
if "deadline_ts" not in st.session_state:
    st.session_state.deadline_ts = time.time() + 180
    st.session_state.start_time = time.time()  # Track when user started

# fire auto-return when time is up (exactly once)
if time.time() >= st.session_state.deadline_ts:
    back_to_survey(done_flag=True)

# expose the function for UI buttons
st.session_state.back_to_survey = back_to_survey

# Prevent restart via browser refresh/back ONLY if user had already started
# Check if this is a fresh session (first visit) vs a refresh (had chat history)
if "loan_assistant" not in st.session_state and st.session_state.get("return_raw"):
    # Only redirect if they had already started (had chat history marker)
    if st.session_state.get("application_started", False):
        # User refreshed or went back after starting - redirect to survey
        back_to_survey(done_flag=True)

# ===== END QUALTRICS/PROLIFIC INTEGRATION =====

# Now import everything else
from agent import Agent
from nlu import NLU
from answer import Answers
from github_saver import save_to_github
from loan_assistant import LoanAssistant
from ab_config import config
from shap_visualizer import display_shap_explanation, explain_shap_visualizations
from interaction_logger import create_logger_from_secrets
from xai_methods import get_friendly_feature_name
import os
import pandas as pd

# Determine condition name based on environment variables
# Map to user-friendly condition names for logging
anthro = os.getenv("ANTHROKIT_ANTHRO", "high")  # high or low
personality = os.getenv("PERSONALITY_ADAPTATION", "disabled")  # enabled or disabled

CONDITION_NAME_MAP = {
    ("low", "enabled"): "lowanthropersonality",
    ("low", "disabled"): "lowanthrofixedperso",
    ("high", "enabled"): "highanthropersonalized",
    ("high", "disabled"): "highanthrofixedperso"
}

condition_name = CONDITION_NAME_MAP.get((anthro, personality), "unknown_condition")

# Initialize GitHub logger with Streamlit secrets
if 'interaction_logger' not in st.session_state:
    # Mock config for logger initialization
    class LoggerConfig:
        show_anthropomorphic = (anthro == "high")
        personality_adaptation_enabled = (personality == "enabled")
        user_personality = None  # Will be set after personality survey
    
    logger_config = LoggerConfig()
    st.session_state.interaction_logger = create_logger_from_secrets(st.secrets, logger_config)
    st.session_state.interaction_logger.condition_name = condition_name
    
    # Add compatibility methods for old data_logger API
    def log_interaction_compat(interaction_type: str, content: Dict):
        """Compatibility wrapper for old data_logger API"""
        logger_inst = st.session_state.interaction_logger
        
        # If this is the first interaction, start a turn
        if not logger_inst.current_turn:
            turn_type = "greet" if "greeting" in interaction_type.lower() else "collect"
            logger_inst.start_turn(turn_type=turn_type)
        
        # Store interaction data (will be logged at end of turn)
        if not hasattr(logger_inst, '_temp_data'):
            logger_inst._temp_data = {}
        logger_inst._temp_data[interaction_type] = content
    
    def update_application_data_compat(field: str, value):
        """Compatibility wrapper"""
        pass  # Not needed for our new logger
    
    def set_prediction_compat(prediction: str, probability: float):
        """Compatibility wrapper"""
        pass  # Not needed for our new logger
    
    def set_feedback_compat(feedback_data: Dict):
        """Compatibility wrapper for feedback"""
        logger_inst = st.session_state.interaction_logger
        if not hasattr(logger_inst, '_feedback'):
            logger_inst._feedback = feedback_data
    
    def build_final_data_compat():
        """Compatibility wrapper"""
        return {}  # Not needed for our new logger
    
    def save_to_github_compat():
        """Compatibility wrapper - save is done in end_session()"""
        pass
    
    st.session_state.interaction_logger.log_interaction = log_interaction_compat
    st.session_state.interaction_logger.update_application_data = update_application_data_compat
    st.session_state.interaction_logger.set_prediction = set_prediction_compat
    st.session_state.interaction_logger.set_feedback = set_feedback_compat
    st.session_state.interaction_logger.build_final_data = build_final_data_compat
    st.session_state.interaction_logger.save_to_github = save_to_github_compat
    
    print(f"[App] Initialized logger for condition: {condition_name}")

logger = st.session_state.interaction_logger

# Define field options for quick selection (based on actual Adult dataset analysis)
field_options = {
    'workclass': ['Private', 'Self-emp-not-inc', 'Self-emp-inc', 'Federal-gov', 'Local-gov', 'State-gov', 'Without-pay', 'Never-worked', '?'],
    'education': ['Bachelors', 'HS-grad', 'Masters', 'Some-college', 'Assoc-acdm', 'Assoc-voc', '11th', '9th', '10th', '12th', '7th-8th', 'Doctorate', '1st-4th', '5th-6th', 'Preschool', 'Prof-school'],
    'marital_status': ['Married-civ-spouse', 'Divorced', 'Never-married', 'Separated', 'Widowed', 'Married-spouse-absent', 'Married-AF-spouse'],
    'occupation': ['Tech-support', 'Craft-repair', 'Other-service', 'Sales', 'Exec-managerial', 'Prof-specialty', 'Handlers-cleaners', 'Machine-op-inspct', 'Adm-clerical', 'Farming-fishing', 'Armed-Forces', 'Priv-house-serv', 'Protective-serv', 'Transport-moving', '?'],
    'sex': ['Male', 'Female'],
    'race': ['Black', 'Asian-Pac-Islander', 'Amer-Indian-Eskimo', 'White', 'Other'],
    'native_country': ['United-States', 'Cambodia', 'Canada', 'China', 'Columbia', 'Cuba', 'Dominican-Republic', 'Ecuador', 'El-Salvador', 'England', 'France', 'Germany', 'Greece', 'Guatemala', 'Haiti', 'Holand-Netherlands', 'Honduras', 'Hong', 'Hungary', 'India', 'Iran', 'Ireland', 'Italy', 'Jamaica', 'Japan', 'Laos', 'Mexico', 'Nicaragua', 'Outlying-US(Guam-USVI-etc)', 'Peru', 'Philippines', 'Poland', 'Portugal', 'Puerto-Rico', 'Scotland', 'South', 'Taiwan', 'Thailand', 'Trinadad&Tobago', 'Vietnam', 'Yugoslavia', '?'],
    'relationship': ['Wife', 'Own-child', 'Husband', 'Not-in-family', 'Other-relative', 'Unmarried']
}

# Str            <h3 style="margin: 0; color: white;">Hi! I'm Luna</h3>amlit compatibility function
def st_rerun():
    """Compatibility function for Streamlit rerun across versions"""
    if hasattr(st, 'rerun'):
        st.rerun()
    else:
        st.experimental_rerun()

# Custom CSS for better appearance with chat bubbles
st.markdown("""
<style>
    .chat-container {
        max-height: 600px;
        overflow-y: auto;
        padding: 1rem;
        background: linear-gradient(135deg, #e3f2fd 0%, #f8f9fa 100%);
        border-radius: 15px;
        margin: 1rem 0;
        border: 1px solid #e0e0e0;
    }
    .chat-message {
        display: flex;
        margin: 0.8rem 0;
        align-items: flex-end;
        clear: both;
    }
    .user-message {
        justify-content: flex-end;
        flex-direction: row-reverse;
    }
    .assistant-message {
        justify-content: flex-start;
        flex-direction: row;
    }
    .message-bubble {
        padding: 10px 14px;
        border-radius: 18px;
        max-width: 65%;
        word-wrap: break-word;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        position: relative;
        line-height: 1.4;
        font-size: 14px;
    }
    .user-bubble {
        background: #007bff;
        color: white;
        border-bottom-right-radius: 4px;
        margin-right: 8px;
    }
    .user-bubble::after {
        content: '';
        position: absolute;
        right: -8px;
        bottom: 0;
        width: 0;
        height: 0;
        border-left: 8px solid #007bff;
        border-bottom: 8px solid transparent;
    }
    .assistant-bubble {
        background: white;
        color: #333;
        border: 1px solid #e0e0e0;
        border-bottom-left-radius: 4px;
        margin-left: 8px;
    }
    .assistant-bubble::after {
        content: '';
        position: absolute;
        left: -9px;
        bottom: 0;
        width: 0;
        height: 0;
        border-right: 8px solid white;
        border-bottom: 8px solid transparent;
        border-top: 1px solid transparent;
    }
    .assistant-bubble::before {
        content: '';
        position: absolute;
        left: -10px;
        bottom: 0;
        width: 0;
        height: 0;
        border-right: 8px solid #e0e0e0;
        border-bottom: 8px solid transparent;
    }
    .profile-pic {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        margin: 0 5px;
        border: 2px solid #fff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        flex-shrink: 0;
    }
    .user-icon {
        width: 45px;
        height: 40px;
        border-radius: 50%;
        background: #007bff;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 11px;
        margin: 0 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        flex-shrink: 0;
    }
    .progress-bar {
        background-color: #e9ecef;
        border-radius: 10px;
        padding: 3px;
        border: 1px solid #dee2e6;
    }
    .progress-fill {
        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
        height: 22px;
        border-radius: 7px;
        text-align: center;
        line-height: 22px;
        color: white;
        font-weight: bold;
        font-size: 12px;
        box-shadow: 0 2px 4px rgba(0,123,255,0.2);
    }
    .status-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #007bff;
        margin: 0.5rem 0;
    }
    .luna-intro {
        display: flex;
        align-items: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
        .luna-intro img {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        margin-right: 15px;
        border: 3px solid white;
    }
    .option-button {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 8px 12px;
        margin: 3px;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 13px;
        color: #495057;
        display: inline-block;
    }
    .option-button:hover {
        background: #e9ecef;
        border-color: #007bff;
        color: #007bff;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,123,255,0.2);
    }
    .option-button:active {
        background: #007bff;
        color: white;
        transform: translateY(0);
    }
    .options-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

def initialize_system():
    """Initialize the agent and all components"""
    try:
        agent = Agent()
        answers = Answers(
            list_node=[],
            clf=agent.clf,
            clf_display=agent.clf_display,
            current_instance=agent.current_instance,
            question=None,
            l_exist_classes=agent.l_exist_classes,
            l_exist_features=agent.l_exist_features,
            l_instances=agent.l_instances,
            data=agent.data,
            df_display_instance=agent.df_display_instance,
            predicted_class=agent.predicted_class,
            preprocessor=agent.preprocessor
        )
        return agent, answers
    except Exception as e:
        st.error(f"Failed to initialize system: {str(e)}")
        st.error("Please check the console for more details.")
        import traceback
        st.code(traceback.format_exc())
        # Return None values to prevent further errors
        return None, None

# Initialize system
if 'agent' not in st.session_state:
    st.session_state.agent, st.session_state.answers = initialize_system()

# Check if initialization was successful
if st.session_state.agent is None:
    st.error("System initialization failed. Please check the error messages above and try refreshing the page.")
    st.stop()

agent = st.session_state.agent
answers = st.session_state.answers

# ===== PERSONALITY-BASED PERSONALIZATION =====
# Check if personality adaptation is required by environment variable
from anthrokit.personality import get_personality_from_session, save_personality_to_session, BIG_5_ITEMS

personality_required = os.getenv("PERSONALITY_ADAPTATION", "disabled") == "enabled"

if personality_required:
    personality = get_personality_from_session()
    
    if not personality:
        # Mandatory personality survey before proceeding
        st.title("🏦 AI Loan Assistant - Credit Pre-Assessment")
        st.markdown("---")
        st.info("📋 Please complete this brief personality survey to personalize your experience.")
        
        with st.form("personality_form"):
            st.markdown("""### Brief Personality Survey
            
Rate yourself on these traits (1 = Disagree strongly, 7 = Agree strongly):""")
            
            responses = {}
            for trait, items in BIG_5_ITEMS.items():
                for i, (item_text, direction) in enumerate(items):
                    key = f"personality_{trait}_{i}"
                    response = st.slider(
                        f"I see myself as: **{item_text}**",
                        min_value=1,
                        max_value=7,
                        value=4,
                        key=key
                    )
                    responses[key] = (trait, response, direction)
            
            submitted = st.form_submit_button("Submit & Continue")
            
            if submitted:
                # Calculate Big 5 scores
                trait_scores = {trait: [] for trait in BIG_5_ITEMS.keys()}
                
                for key, (trait, response, direction) in responses.items():
                    if direction == -1:
                        score = 8 - response  # Reverse code
                    else:
                        score = response
                    trait_scores[trait].append(score)
                
                personality = {
                    trait: sum(scores) / len(scores)
                    for trait, scores in trait_scores.items()
                }
                
                print(f"\n📊 DEBUG: Big Five Scores Calculated:")
                for trait, score in personality.items():
                    print(f"   {trait.capitalize()}: {score:.2f}")
                
                save_personality_to_session(personality)
                print(f"✅ DEBUG: Personality saved to session state")
                
                # CRITICAL: Refresh config with new personality adjustments
                from ab_config import config
                config.refresh_personality_adjustments()
                
                st.success("✅ Personality profile saved! The assistant will now adapt to your preferences.")
                st_rerun()
        
        st.stop()  # Block main app until survey complete

# ===== END PERSONALITY SECTION =====

# Initialize loan assistant
if 'loan_assistant' not in st.session_state:
    st.session_state.loan_assistant = LoanAssistant(agent)
    st.session_state.chat_history = []

# App header
st.title("🏦 AI Loan Assistant - Credit Pre-Assessment")

# Assistant Introduction (A/B testing)
assistant_avatar = config.get_assistant_avatar()
if assistant_avatar and os.path.exists(assistant_avatar):
    import base64
    with open(assistant_avatar, "rb") as f:
        avatar_pic_b64 = base64.b64encode(f.read()).decode()
    
    st.markdown(f"""
    <div class="luna-intro">
        <img src="data:image/png;base64,{avatar_pic_b64}" alt="{config.assistant_name}">
        <div>
            <h3 style="margin: 0; color: white;">Hi! I'm {config.assistant_name}</h3>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">{config.assistant_intro}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    # Fallback without image
    st.markdown(f"""
    <div class="luna-intro">
        <div style="width: 60px; height: 60px; border-radius: 50%; margin-right: 15px; border: 3px solid white; background: #f093fb; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 24px;">{config.assistant_name[0]}</div>
        <div>
            <h3 style="margin: 0; color: white;">Hi! I'm {config.assistant_name}</h3>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">{config.assistant_intro}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Single conversational interface
st.markdown("---")

# Sidebar - keep minimal to avoid distracting from experimental task
with st.sidebar:
    # No restart option - users should complete one application per session
    # Explanation style is controlled by the experimental condition, not user choice
    
    # A/B Testing Debug Info (only for development/testing - hidden from users)
    # Uncomment the lines below only when debugging A/B testing locally
    # if config.show_debug_info and os.getenv('HICXAI_DEBUG_MODE', 'false').lower() == 'true':
    # What‑if Lab (shown after user asks what-if in counterfactual HIGH anthropomorphism conditions only)
    if config.show_counterfactual and config.show_anthropomorphic and getattr(st.session_state.loan_assistant, 'show_what_if_lab', False):
        st.markdown("---")
        st.subheader("🧪 What‑if Lab")
        st.caption("Adjust inputs to see how the predicted probability changes.")

        # Prepare a baseline instance from current app state if available
        app_state = st.session_state.loan_assistant.application
        def default(v, fallback):
            return v if v is not None else fallback

        # Core numerics
        age = st.slider("Age", min_value=17, max_value=90, value=int(default(app_state.age, 35)))
        hours = st.slider("Hours per week", min_value=1, max_value=99, value=int(default(app_state.hours_per_week, 40)))
        gain = st.number_input("Capital Gain", min_value=0, max_value=99999, step=100, value=int(default(app_state.capital_gain, 0)))
        loss = st.number_input("Capital Loss", min_value=0, max_value=4356, step=50, value=int(default(app_state.capital_loss, 0)))

        # Categorical selectors using known field options
        edu = st.selectbox("Education", options=field_options['education'], index=field_options['education'].index(default(app_state.education, 'HS-grad')))
        occ = st.selectbox("Occupation", options=field_options['occupation'], index=field_options['occupation'].index(default(app_state.occupation, 'Sales')))
        workclass = st.selectbox("Workclass", options=field_options['workclass'], index=field_options['workclass'].index(default(app_state.workclass, 'Private')))
        marital = st.selectbox("Marital Status", options=field_options['marital_status'], index=field_options['marital_status'].index(default(app_state.marital_status, 'Never-married')))
        relationship = st.selectbox("Relationship", options=field_options['relationship'], index=field_options['relationship'].index(default(app_state.relationship, 'Not-in-family')))
        sex = st.selectbox("Sex", options=field_options['sex'], index=field_options['sex'].index(default(app_state.sex, 'Male')))
        race = st.selectbox("Race", options=field_options['race'], index=field_options['race'].index(default(app_state.race, 'White')))
        country = st.selectbox("Native Country", options=field_options['native_country'], index=field_options['native_country'].index(default(app_state.native_country, 'United-States')))

        # Build a hypothetical instance and predict
        try:
            # Start from existing application dict (fill minimal defaults)
            hypo = app_state.to_dict()
            hypo['age'] = age
            hypo['hours_per_week'] = hours
            hypo['education'] = edu
            hypo['occupation'] = occ
            hypo['workclass'] = workclass
            hypo['marital_status'] = marital
            hypo['relationship'] = relationship
            hypo['sex'] = sex
            hypo['race'] = race
            hypo['native_country'] = country
            hypo['capital_gain'] = gain
            hypo['capital_loss'] = loss
            if hypo.get('education_num') is None:
                edu_map = {
                    'Preschool': 1, '1st-4th': 2, '5th-6th': 3, '7th-8th': 4, '9th': 5,
                    '10th': 6, '11th': 7, '12th': 8, 'HS-grad': 9, 'Some-college': 10,
                    'Assoc-voc': 11, 'Assoc-acdm': 12, 'Bachelors': 13, 'Masters': 14,
                    'Prof-school': 15, 'Doctorate': 16
                }
                hypo['education_num'] = edu_map.get(edu, 9)
            # Ensure required fields have plausible defaults
            hypo.setdefault('workclass', 'Private')
            hypo.setdefault('marital_status', 'Never-married')
            hypo.setdefault('relationship', 'Not-in-family')
            hypo.setdefault('race', 'White')
            hypo.setdefault('sex', 'Male')
            hypo.setdefault('capital_gain', 0)
            hypo.setdefault('capital_loss', 0)
            hypo.setdefault('native_country', 'United-States')

            import pandas as pd
            app_df = pd.DataFrame([hypo])
            app_df['income'] = '<=50K'  # dummy
            from preprocessing import preprocess_adult
            processed = preprocess_adult(app_df)
            X = processed.drop('income', axis=1)
            # Align with training features
            train_df = pd.concat([agent.data['X_display'], agent.data['y_display']], axis=1)
            train_df_processed = preprocess_adult(train_df)
            expected = train_df_processed.drop('income', axis=1).columns.tolist()
            for col in expected:
                if col not in X.columns:
                    X[col] = 0
            X = X[expected]
            # Predict probability if available
            prob = None
            if hasattr(agent.clf_display, 'predict_proba'):
                p = agent.clf_display.predict_proba(X)
                # Assume class index 1 corresponds to '>50K'
                prob = float(p[0][1]) if p.shape[1] > 1 else float(p[0][0])
            st.metric(label="Estimated P(>50K)", value=f"{(prob if prob is not None else 0.5)*100:.1f}%")

            # Optional: refresh SHAP visuals for hypo profile (textual SHAP for now)
            # We keep visuals in the main flow; here we just indicate changes
            st.caption("Adjust inputs to explore their impact. Use chat for detailed explanations and visuals.")
        except Exception as e:
            st.caption(f"What‑if Lab unavailable: {e}")
    # Otherwise, no What‑if panel is shown until triggered by user
    #     st.markdown("---")
    #     st.markdown("**🧪 Debug Info**")
    #     st.markdown(f"Version: **{config.version}**")
    #     st.markdown(f"Assistant: **{config.assistant_name}**")
    #     st.markdown(f"SHAP Visuals: **{config.show_shap_visualizations}**")

# Chat interface - Display chat history with enhanced bubbles
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for i, (user_msg, assistant_msg) in enumerate(st.session_state.chat_history):
    # User message (right side, blue bubble)
    if user_msg:
        st.markdown(f"""
        <div class="chat-message user-message">
            <div class="user-icon">You</div>
            <div class="message-bubble user-bubble">
                {user_msg}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Assistant message with profile picture (left side, white bubble)
    if assistant_msg:
        assistant_avatar = config.get_assistant_avatar()
        if assistant_avatar and os.path.exists(assistant_avatar):
            import base64
            with open(assistant_avatar, "rb") as f:
                avatar_pic_b64 = base64.b64encode(f.read()).decode()
            avatar_pic_element = f'<img src="data:image/png;base64,{avatar_pic_b64}" class="profile-pic" alt="{config.assistant_name}">'
        else:
            avatar_pic_element = f'<div class="profile-pic" style="background: #f093fb; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 16px;">{config.assistant_name[0]}</div>'
        
        st.markdown(f"""
        <div class="chat-message assistant-message">
            {avatar_pic_element}
            <div class="message-bubble assistant-bubble">
                {assistant_msg}
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Initialize with welcome message
if len(st.session_state.chat_history) == 0:
    welcome_msg = st.session_state.loan_assistant.handle_message("hello")
    st.session_state.chat_history.append((None, welcome_msg))
    st_rerun()

# Chat input (form enables Enter-to-send and clears on submit automatically)
# Check if current field has clickable options for placeholder
current_field = getattr(st.session_state.loan_assistant, 'current_field', None)
if current_field and current_field in field_options:
    placeholder_text = "💬 Type your answer or use the clickable buttons below..."
else:
    placeholder_text = "Type your message to Luna..."

with st.form("chat_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        user_message = st.text_input("Message to Luna", key="user_input", placeholder=placeholder_text, label_visibility="collapsed")
    with col2:
        send_button = st.form_submit_button("Send", width="stretch")

# Add helper text for clickable features
if current_field and current_field in field_options:
    st.markdown('<div style="text-align: center; color: #666; font-size: 0.85em; margin-top: 5px;">👆 Use the clickable buttons below for faster selection!</div>', unsafe_allow_html=True)

# Show clickable options right after chat input (for immediate visibility)
if current_field and current_field in field_options:
    st.markdown("---")
    st.markdown(f"### 🎯 Quick Select: {current_field.replace('_', ' ').title()}")
    st.markdown("**💡 Click any option below instead of typing:**")
    st.markdown('<div class="options-container">', unsafe_allow_html=True)
    
    options = field_options[current_field]
    
    # Create buttons in rows with enhanced styling
    cols_per_row = 4 if len(options) > 8 else 3
    for i in range(0, len(options), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, option in enumerate(options[i:i+cols_per_row]):
            with cols[j]:
                # Get friendly name for display
                friendly_option = get_friendly_feature_name(f"{current_field}_{option}")
                # If no mapping found, clean up the technical name
                if friendly_option.startswith(current_field.title()):
                    friendly_option = option.replace('-', ' ').replace('_', ' ')
                
                # Enhanced button styling based on option type
                if option == "Other":
                    button_text = f"🔄 {friendly_option}"
                    button_type = "primary"
                elif option == "?":
                    button_text = f"❓ Unknown/Prefer not to say"
                    button_type = "primary"
                elif option in ["Male", "Female"]:
                    button_text = f"👤 {friendly_option}"
                    button_type = "secondary"
                elif option == "United-States":
                    button_text = f"🇺🇸 {friendly_option}"
                    button_type = "primary"
                elif option in ["Private", "Self-emp-not-inc", "Self-emp-inc"]:
                    button_text = f"💼 {friendly_option}"
                    button_type = "secondary"
                elif "gov" in option.lower():
                    button_text = f"🏛️ {friendly_option}"
                    button_type = "secondary"
                else:
                    button_text = f"✨ {friendly_option}"
                    button_type = "secondary"
                
                if st.button(button_text, key=f"option_top_{current_field}_{option}", width="stretch", type=button_type):
                    st.session_state.option_clicked = option
                    st_rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("*💬 Or you can still type your answer in the chat box above*")

# Process user input
if send_button and user_message:
    # Mark that user has started the application
    st.session_state.application_started = True
    
    # Log interaction
    if logger:
        current_field = getattr(st.session_state.loan_assistant, 'current_field', None)
        logger.log_interaction("user_message", {
            "field": current_field,
            "input_method": "typed",
            "content": user_message,
            "conversation_state": st.session_state.loan_assistant.conversation_state.value
        })
    
    # Handle the message through loan assistant
    assistant_response = st.session_state.loan_assistant.handle_message(user_message)
    
    # Log assistant response
    if logger:
        logger.log_interaction("assistant_response", {
            "content": assistant_response
        })
    
    # Add to chat history (form clears input on submit)
    st.session_state.chat_history.append((user_message, assistant_response))
    st_rerun()

# Handle option clicks
if 'option_clicked' in st.session_state and st.session_state.option_clicked:
    option_value = st.session_state.option_clicked
    
    # Mark that user has started the application
    st.session_state.application_started = True
    
    # Log interaction
    if logger:
        current_field = getattr(st.session_state.loan_assistant, 'current_field', None)
        logger.log_interaction("user_message", {
            "field": current_field,
            "input_method": "clicked",
            "content": option_value,
            "conversation_state": st.session_state.loan_assistant.conversation_state.value
        })
    
    assistant_response = st.session_state.loan_assistant.handle_message(option_value)
    
    # Log assistant response
    if logger:
        logger.log_interaction("assistant_response", {
            "content": assistant_response
        })
    
    # Add to chat history
    st.session_state.chat_history.append((option_value, assistant_response))
    st.session_state.option_clicked = None  # Reset
    st_rerun()

# Persistent SHAP visuals section: render when feature_importance explanation is enabled
if config.show_shap_visualizations:
    shap_data = getattr(st.session_state.loan_assistant, 'last_shap_result', None)
    if shap_data:
        st.markdown("---")
        st.subheader("🔎 Visual Explanations")
        display_shap_explanation(shap_data)
        explain_shap_visualizations()

# Quick reply buttons based on current state
st.markdown("---")
st.markdown("**Quick Replies:**")

current_state = st.session_state.loan_assistant.conversation_state.value

if current_state == 'greeting':
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("👋 Start Application", key="quick_start"):
            response = st.session_state.loan_assistant.handle_message("start")
            st.session_state.chat_history.append(("start", response))
            st_rerun()

elif current_state == 'collecting_info':
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Check Progress", key="quick_progress"):
            if logger:
                logger.log_interaction("progress_check", {})
            response = st.session_state.loan_assistant.handle_message("review")
            st.session_state.chat_history.append(("check progress", response))
            st_rerun()
    with col2:
        if st.button("Help", key="quick_help"):
            if logger:
                logger.log_interaction("help_click", {})
            # Get context-aware help
            current_field = getattr(st.session_state.loan_assistant, 'current_field', None)
            if current_field:
                help_msg = st.session_state.loan_assistant._get_field_help(current_field)
                help_msg += f"\n\n💡 **You can also:**\n• Say 'review' to see your progress\n• Click the quick-select buttons below\n• Ask for specific examples"
            else:
                help_msg = ("I'm collecting information for your loan application. Please answer the questions "
                           "as accurately as possible. You can say 'review' to see your progress.")
            st.session_state.chat_history.append(("help", help_msg))
            st_rerun()

elif current_state == 'complete':
    # Only show What-If button in Condition 4 (HIGH anthropomorphism + counterfactual)
    if config.show_counterfactual and config.show_anthropomorphic:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Explain Decision", key="quick_explain", width="stretch"):
                if logger:
                    logger.log_interaction("explanation_request", {"type": "decision_explanation"})
                response = st.session_state.loan_assistant.handle_message("explain")
                st.session_state.chat_history.append(("explain", response))
                st_rerun()
        with col2:
            if st.button("🔧 What If Analysis", key="quick_whatif", width="stretch"):
                # Turn on What‑if Lab and prompt guidance
                try:
                    st.session_state.loan_assistant.show_what_if_lab = True
                except Exception:
                    pass
                response = "What‑if Lab enabled in the sidebar. Adjust Age, Hours, Education, or Occupation to see how the probability changes."
                st.session_state.chat_history.append(("what if analysis", response))
                st_rerun()
    else:
        # Show only Explain button for other conditions
        if st.button("Explain Decision", key="quick_explain", width="stretch"):
            if logger:
                logger.log_interaction("explanation_request", {"type": "decision_explanation"})
            response = st.session_state.loan_assistant.handle_message("explain")
            st.session_state.chat_history.append(("explain", response))
            st_rerun()

# Clickable Options for Current Field (if collecting info)
if current_state == 'collecting_info' and hasattr(st.session_state.loan_assistant, 'current_field') and st.session_state.loan_assistant.current_field:
    current_field = st.session_state.loan_assistant.current_field
    
    if current_field in field_options:
        st.markdown("---")
        st.markdown(f"### 🎯 Quick Select: {current_field.replace('_', ' ').title()}")
        st.markdown("**💡 Click any option below instead of typing:**")
        st.markdown('<div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 15px; border-radius: 10px; margin: 10px 0; border: 1px solid #dee2e6;">', unsafe_allow_html=True)
        
        options = field_options[current_field]
        
        # Create buttons in rows with enhanced styling
        cols_per_row = 4 if len(options) > 8 else 3
        for i in range(0, len(options), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, option in enumerate(options[i:i+cols_per_row]):
                with cols[j]:
                    # Enhanced button styling based on option type
                    # Get friendly name for display
                    friendly_option = get_friendly_feature_name(f"{current_field}_{option}")
                    # If no mapping found, use the option as-is
                    if friendly_option.startswith(current_field.title()):
                        friendly_option = option.replace('-', ' ').replace('_', ' ')
                    
                    if option == "Other":
                        button_text = f"🔄 {friendly_option}"
                        button_type = "primary"
                    elif option == "?":
                        button_text = f"❓ Unknown/Prefer not to say"
                        button_type = "primary"
                    elif option in ["Male", "Female"]:
                        button_text = f"👤 {friendly_option}"
                        button_type = "secondary"
                    elif option == "United-States":
                        button_text = f"🇺🇸 {friendly_option}"
                        button_type = "primary"
                    elif option in ["Private", "Self-emp-not-inc", "Self-emp-inc"]:
                        button_text = f"💼 {friendly_option}"
                        button_type = "secondary"
                    elif "gov" in option.lower():
                        button_text = f"🏛️ {friendly_option}"
                        button_type = "secondary"
                    else:
                        button_text = f"✨ {friendly_option}"
                        button_type = "secondary"
                    
                    if st.button(button_text, key=f"option_{current_field}_{option}", width="stretch", type=button_type):
                        st.session_state.option_clicked = option
                        st_rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("*💬 Or you can still type your answer in the chat box above*")

# Feedback section (appears after application is complete)
if current_state == 'complete' and len(st.session_state.chat_history) > 5:
    st.markdown("---")
    st.markdown("### 📝 Your Feedback")
    st.markdown("Help us improve by sharing your experience:")
    
    with st.form("feedback_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            rating = st.select_slider(
                "How would you rate your experience?",
                options=[1, 2, 3, 4, 5],
                value=3,
                format_func=lambda x: "⭐" * x
            )
            
            ease_of_use = st.radio(
                "Was the application process easy to understand?",
                ["Very Easy", "Easy", "Neutral", "Difficult", "Very Difficult"]
            )
        
        with col2:
            explanation_clarity = st.radio(
                "Were the AI explanations helpful?",
                ["Very Helpful", "Helpful", "Neutral", "Not Helpful", "Confusing"]
            )
            
            would_recommend = st.radio(
                "Would you recommend this service?",
                ["Definitely", "Probably", "Maybe", "Probably Not", "Definitely Not"]
            )
        
        feedback_text = st.text_area(
            "Additional comments (optional):",
            placeholder="“What feature would help you most next time?”\n“What would make this agent's explanations more useful?”..."
        )
        
        submitted = st.form_submit_button("Submit Feedback 🚀")
        
        if submitted:
            # Calculate completion percentage
            completion = st.session_state.loan_assistant.application.calculate_completion()
            
            feedback_data = {
                "rating": rating,
                "ease_of_use": ease_of_use,
                "explanation_clarity": explanation_clarity,
                "would_recommend": would_recommend,
                "additional_comments": feedback_text,
                "conversation_length": len(st.session_state.chat_history),
                "completion_percentage": completion,
                # A/B Testing metadata
                "ab_version": config.version,
                "session_id": config.session_id,
                "assistant_name": config.assistant_name,
                "had_shap_visualizations": config.show_shap_visualizations,
                "timestamp": pd.Timestamp.now().isoformat()
            }
            
            # ===== ANTHROKIT RESEARCH DATA COLLECTION =====
            # Record outcomes with complete treatment documentation
            try:
                import os
                from anthrokit.personality import get_personality_from_session
                from anthrokit.tracking import track_session_end
                
                personality_traits = get_personality_from_session()
                
                # Build outcomes dictionary (optional - usually collected in Qualtrics)
                outcomes = {
                    "social_presence": rating,  # Using overall rating as proxy
                    "trust": would_recommend,
                    "satisfaction": ease_of_use,
                    "explanation_clarity": explanation_clarity,
                    "completion": completion
                }
                
                # Record with adaptive optimizer (if enabled)
                if config.optimizer and config.current_condition:
                    config.optimizer.record_outcome(
                        preset=config.current_condition,
                        outcomes=outcomes,
                        personality=personality_traits
                    )
                    print(f"📊 Recorded outcome with adaptive optimizer")
                
                # Build final tone config
                final_config = config.current_condition or {
                    "warmth": config.warmth,
                    "empathy": config.empathy,
                    "formality": config.formality,
                    "hedging": getattr(config, 'hedging', 0.45),
                    "self_reference": config.self_reference,
                    "emoji": config.emoji_style,
                    "temperature": config.temperature
                }
                
                # Determine condition label
                anthro_level = config.anthro  # "high" or "low"
                personality_mode = os.getenv("PERSONALITY_ADAPTATION", "disabled")
                condition_label = f"{config.anthro_preset}_{personality_mode}"
                
                # Record with session tracker (COMPLETE TREATMENT DOCUMENTATION)
                track_session_end(
                    # Data linkage identifier
                    participant_id=st.session_state.get('prolific_pid'),
                    
                    # Outcomes (optional - usually in Qualtrics)
                    outcomes=outcomes,
                    feedback=None,
                    
                    # Treatment documentation (ESSENTIAL)
                    personality_traits=personality_traits,
                    base_preset=getattr(config, 'base_preset', {}),
                    personality_adjustments=getattr(config, 'personality_adjustments', {}),
                    final_tone_config=final_config,
                    
                    # Condition metadata
                    condition_label=condition_label,
                    anthropomorphism_level=anthro_level,
                    personality_adaptation=personality_mode
                )
                print(f"📊 Logged treatment: {condition_label}, warmth={final_config.get('warmth'):.2f}, empathy={final_config.get('empathy'):.2f}")
                
            except Exception as e:
                print(f"⚠️ Failed to record research outcomes: {e}")
                import traceback
                traceback.print_exc()
                # Don't block user if research tracking fails
            
            # ===== END RESEARCH DATA COLLECTION =====
            
            # Log feedback to data logger
            if logger:
                logger.set_feedback(feedback_data)
                # Save complete session data to GitHub
                logger_saved = logger.save_to_github()
                if not logger_saved:
                    print("⚠️ Failed to save session log to GitHub")
            
            # Save feedback
            try:
                # Try GitHub first (if configured)
                github_token = os.getenv('GITHUB_TOKEN')
                github_repo = os.getenv('GITHUB_REPO', 'your-username/your-repo')
                
                if github_token:
                    import json
                    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"feedback/session_{config.session_id}_{timestamp}.json"
                    
                    success = save_to_github(
                        repo=github_repo,
                        path=filename,
                        content=json.dumps(feedback_data, indent=2),
                        commit_message=f"User feedback - {config.version} - {timestamp}",
                        github_token=github_token
                    )
                    
                    if success:
                        st.success("Thank you for your feedback! 🎉")
                        st.session_state.feedback_submitted = True
                    else:
                        raise Exception("GitHub save failed")
                else:
                    raise Exception("No GitHub token configured")
                    
            except Exception as e:
                st.warning("Feedback saved locally. Thank you!")
                st.session_state.feedback_submitted = True
                
                # Fallback: save to local file
                import json
                os.makedirs('feedback', exist_ok=True)
                timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
                filename = f"feedback/session_{config.session_id}_{timestamp}.json"
                
                with open(filename, "w") as f:
                    f.write(json.dumps(feedback_data, indent=2))
    
    # ============================================================================
    # RETURN TO QUALTRICS (If coming from survey)
    # ============================================================================
    if st.session_state.get("feedback_submitted", False) and st.session_state.get("return_raw"):
        # Participant came from Qualtrics - return them to continue survey
        st.markdown("---")
        st.markdown("### ✅ Interaction Complete!")
        st.markdown("""
        Thank you for completing the interaction phase! 
        
        Please click the button below to **continue the survey**.
        """)
        
        elapsed_time = time.time() - st.session_state.get("start_time", time.time())
        if elapsed_time >= 120:  # 2 minutes minimum engagement
            if st.button("📋 Continue to Survey", type="primary", width="stretch", key="return_to_qualtrics"):
                back_to_survey(done_flag=True)
        else:
            remaining = int(120 - elapsed_time)
            st.info(f"⏱️ Please wait {remaining} seconds before continuing to the survey.")
    
    elif st.session_state.get("feedback_submitted", False):
        # No return URL - standalone completion (shouldn't happen in study)
        st.markdown("---")
        st.success("✅ Thank you for your participation!")
        st.markdown("You may close this window.")

# Footer with dataset information
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>🏦 AI Loan Assistant</p>
    <p><small>🔬 Algorithm trained on the Adult (Census Income) dataset with 32,561 records from the UCI Machine Learning Repository</small></p>
</div>
""", unsafe_allow_html=True)

# Expandable dataset details
with st.expander("📊 Dataset Information - Adult Census Income Dataset"):
    st.markdown("""
    **Dataset Overview:**
    
    The Adult Census Income Dataset is a popular benchmark dataset from the UCI Machine Learning Repository, 
    sometimes referred to as the Census Income or Adult dataset. It includes **32,561 records** and **15 attributes**, 
    each representing a person's social, employment, and demographic information. The dataset originates from the 
    U.S. Census database from 1994.
    
    **Prediction Task:**
    
    The main goal is to determine whether an individual makes more than $50,000 per year based on their attributes. 
    The income is the target variable with two possible classes:
    - **≤50K**: Income less than or equal to $50,000
    - **>50K**: Income greater than $50,000
    
    **Dataset Features:**
    
    The dataset contains both qualitative and numerical attributes:
    
    - **Age**: Numerical value indicating person's age
    - **Workclass**: Type of employment (Private sector, Self-employed, Federal/Local/State government, etc.)
    - **Education / Education-num**: Highest education level (High school graduate, Bachelor's, Master's, Doctorate, etc.)
    - **Marital-status**: Marital status (Married, Divorced, Never married, Separated, Widowed, etc.)
    - **Occupation**: Work area (Professional, Sales, Administrative, Tech support, Management, etc.)
    - **Relationship**: Family role (Husband, Wife, Own-child, Not-in-family, Other-relative, Unmarried)
    - **Race**: Ethnic background (White, Asian-Pacific Islander, Indigenous American, Black, Other)
    - **Sex**: Gender (Male, Female)
    - **Capital-gain / Capital-loss**: Investment gains or losses
    - **Hours-per-week**: Number of working hours per week
    - **Native-country**: Country of origin (42 countries including United States, Canada, Mexico, Philippines, India, China, Germany, England, and many others)
    - **Income**: Target label (≤50K or >50K)
    
    **Model Performance:**
    
    Our trained RandomForest classifier achieves **85.94% accuracy** on this dataset.
    """)

# A/B Testing Debug Info (only for development - hidden from users)
# Only show when HICXAI_DEBUG_MODE environment variable is set to 'true'
if os.getenv('HICXAI_DEBUG_MODE', 'false').lower() == 'true':
    st.markdown("---")
    st.markdown("### 🧪 A/B Testing Information (Debug Mode)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Version:** {config.version}")
        st.markdown(f"**Session ID:** {config.session_id}")
    with col2:
        st.markdown(f"**Assistant:** {config.assistant_name}")
        st.markdown(f"**SHAP Visuals:** {config.show_shap_visualizations}")
    with col3:
        st.markdown(f"**Concurrent Testing:** ✅ Enabled")
        st.markdown(f"**User Isolation:** ✅ Session-based")

# Sticky return footer (only show after 2 minutes of engagement)
if st.session_state.get("return_raw"):
    elapsed_time = time.time() - st.session_state.get("start_time", time.time())
    
    if elapsed_time >= 60:  # 1 minute = 60 seconds
        st.markdown("---")
        col_a, col_b = st.columns([3, 1])
        with col_a:
            remaining = max(0, int(st.session_state.deadline_ts - time.time()))
            m, s = divmod(remaining, 60)
            st.caption(f"⏱️ Up to {m}:{s:02d} remaining. You can return anytime.")
        with col_b:
            if st.button("✅ Continue to survey", type="primary", width="stretch", key="footer_return"):
                back_to_survey()
    else:
        # Show countdown until button appears
        st.markdown("---")
        wait_time = int(60 - elapsed_time)
        m, s = divmod(wait_time, 60)
        remaining_deadline = max(0, int(st.session_state.deadline_ts - time.time()))
        md, sd = divmod(remaining_deadline, 60)
        st.caption(f"⏱️ Session time: up to {md}:{sd:02d} remaining • Continue button appears in: {m}:{s:02d}")