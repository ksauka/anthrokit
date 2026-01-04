"""
Analytics dashboard for AnthroKit session tracking.

Run with: streamlit run analytics_dashboard.py

Shows:
- Which apps users interacted with
- What anthropomorphism levels were used
- User outcomes by app and preset
- Session completion rates
"""

import streamlit as st
from pathlib import Path
import sys

# Import from anthrokit
from anthrokit.tracking import (
    load_all_sessions,
    get_anthropomorphism_distribution,
    get_app_usage_stats,
    get_sessions_by_app,
    get_sessions_by_preset,
    export_analytics
)

st.set_page_config(
    page_title="AnthroKit Analytics",
    page_icon="📊",
    layout="wide"
)

st.title("📊 AnthroKit Session Analytics")
st.markdown("Track user interactions, anthropomorphism levels, and outcomes across apps")

# Load data
all_sessions = load_all_sessions()
session_starts = [s for s in all_sessions if s.get('event') == 'session_start']
session_ends = [s for s in all_sessions if s.get('event') == 'session_end']

if not all_sessions:
    st.info("No session data yet. Sessions will appear here after users interact with apps.")
    st.stop()

# Summary metrics
st.header("📈 Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Sessions", len(session_starts))

with col2:
    completion_rate = (len(session_ends) / len(session_starts) * 100) if session_starts else 0
    st.metric("Completion Rate", f"{completion_rate:.1f}%")

with col3:
    unique_users = len(set(s.get('user_id') for s in session_starts if s.get('user_id')))
    st.metric("Unique Users", unique_users)

with col4:
    unique_apps = len(set(s.get('app_name') for s in session_starts if s.get('app_name')))
    st.metric("Apps Used", unique_apps)

# Anthropomorphism distribution
st.header("🎭 Anthropomorphism Level Distribution")
anthro_dist = get_anthropomorphism_distribution()

if anthro_dist:
    col1, col2 = st.columns(2)
    
    with col1:
        st.bar_chart(anthro_dist)
    
    with col2:
        st.markdown("**Preset Counts:**")
        for preset, count in sorted(anthro_dist.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / sum(anthro_dist.values()) * 100)
            st.write(f"- **{preset}**: {count} sessions ({percentage:.1f}%)")

# App usage statistics
st.header("🖥️ App Usage Statistics")
app_stats = get_app_usage_stats()

if app_stats:
    for app_name, stats in sorted(app_stats.items()):
        with st.expander(f"📱 {app_name}", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Sessions", stats['total_sessions'])
            
            with col2:
                st.metric("Completed", stats['completed_sessions'])
            
            with col3:
                completion = (stats['completed_sessions'] / stats['total_sessions'] * 100) if stats['total_sessions'] > 0 else 0
                st.metric("Completion Rate", f"{completion:.1f}%")
            
            # Presets used
            st.markdown("**Presets Used:**")
            st.write(", ".join(stats['presets_used']) if stats['presets_used'] else "None")
            
            # Average outcomes
            if stats['avg_outcomes']:
                st.markdown("**Average Outcomes:**")
                outcome_cols = st.columns(len(stats['avg_outcomes']))
                for i, (metric, data) in enumerate(stats['avg_outcomes'].items()):
                    with outcome_cols[i]:
                        st.metric(
                            metric.replace('_', ' ').title(),
                            f"{data['mean']:.2f}",
                            f"n={data['count']}"
                        )

# Preset comparison
st.header("🔬 Preset Comparison")
preset_comparison = {}

for session in session_ends:
    preset_name = session.get('preset_name', 'unknown')
    if preset_name not in preset_comparison:
        preset_comparison[preset_name] = {
            'count': 0,
            'outcomes': {}
        }
    
    preset_comparison[preset_name]['count'] += 1
    
    # Aggregate outcomes
    for metric, value in session.get('outcomes', {}).items():
        if metric not in preset_comparison[preset_name]['outcomes']:
            preset_comparison[preset_name]['outcomes'][metric] = []
        preset_comparison[preset_name]['outcomes'][metric].append(value)

if preset_comparison:
    # Calculate averages
    preset_avg = {}
    for preset, data in preset_comparison.items():
        preset_avg[preset] = {}
        for metric, values in data['outcomes'].items():
            preset_avg[preset][metric] = sum(values) / len(values) if values else 0
    
    # Display comparison table
    import pandas as pd
    
    if preset_avg:
        df_data = []
        for preset, metrics in preset_avg.items():
            row = {'Preset': preset, 'Sessions': preset_comparison[preset]['count']}
            row.update(metrics)
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
        
        # Chart of outcomes by preset
        if len(df.columns) > 2:  # Has outcome metrics
            st.markdown("**Outcomes by Preset:**")
            outcome_cols = [c for c in df.columns if c not in ['Preset', 'Sessions']]
            
            for col in outcome_cols:
                st.bar_chart(df.set_index('Preset')[col])

# Recent sessions
st.header("🕐 Recent Sessions")
recent_sessions = sorted(
    session_starts,
    key=lambda x: x.get('timestamp', ''),
    reverse=True
)[:10]

if recent_sessions:
    for session in recent_sessions:
        with st.expander(
            f"Session {session.get('session_id', 'unknown')[:8]} - "
            f"{session.get('app_name', 'unknown')} - "
            f"{session.get('preset_name', 'unknown')}"
        ):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Session Info:**")
                st.json({
                    "session_id": session.get('session_id'),
                    "user_id": session.get('user_id'),
                    "app_name": session.get('app_name'),
                    "preset_name": session.get('preset_name'),
                    "timestamp": session.get('timestamp')
                })
            
            with col2:
                st.markdown("**Preset Configuration:**")
                st.json(session.get('preset_config', {}))
            
            # Find corresponding end session
            session_id = session.get('session_id')
            end_session = next(
                (s for s in session_ends if s.get('session_id') == session_id),
                None
            )
            
            if end_session:
                st.markdown("**Outcomes:**")
                st.json(end_session.get('outcomes', {}))
                
                if end_session.get('feedback'):
                    st.markdown("**Feedback:**")
                    st.json(end_session.get('feedback'))

# Export functionality
st.header("💾 Export Data")
col1, col2 = st.columns(2)

with col1:
    if st.button("📥 Export Analytics Report"):
        report = export_analytics()
        st.download_button(
            "Download JSON",
            data=str(report),
            file_name="anthrokit_analytics.json",
            mime="application/json"
        )

with col2:
    if st.button("📥 Export Raw Session Data"):
        import json
        st.download_button(
            "Download JSONL",
            data="\n".join(json.dumps(s) for s in all_sessions),
            file_name="anthrokit_sessions.jsonl",
            mime="application/x-ndjson"
        )

# Instructions
with st.sidebar:
    st.markdown("""
    ### 📚 How to Use
    
    This dashboard tracks:
    - **App usage**: Which apps users interact with
    - **Anthropomorphism levels**: What presets are used (HighA, LowA, adaptive)
    - **User outcomes**: Trust, satisfaction, acceptance scores
    - **Session metrics**: Completion rates, durations
    
    ### 🔄 Refresh
    
    Data updates automatically when users complete sessions.
    Click **Rerun** to refresh the dashboard.
    
    ### 📊 Metrics
    
    - **Trust**: User's trust in AI decisions (1-5)
    - **Satisfaction**: Overall satisfaction (1-5)
    - **Acceptance**: Acceptance of AI recommendations (1-5)
    - **Perceived Anthropomorphism**: How human-like the AI felt (1-5)
    
    ### 🎯 Research Use
    
    Export data for statistical analysis:
    - Compare outcomes across presets
    - Analyze app-specific effects
    - Track user behavior patterns
    """)
