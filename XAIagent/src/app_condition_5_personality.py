"""Entry point for LowA + Personality-Adapted condition
Anthropomorphism: Low (warmth=0.25 base) + TIPI-based personality adjustments (±0.30)
Explanation: feature_importance
"""
import os, sys, streamlit as st

# Set base configuration for LowA
os.environ['ANTHROKIT_EXPLANATION'] = 'feature_importance'
os.environ['ANTHROKIT_ANTHRO'] = 'low'
os.environ['ADAPTIVE_MODE'] = 'disabled'

# Enable personality personalization
os.environ['PERSONALITY_ADAPTATION'] = 'enabled'

sys.path.append('src')
exec(open('src/app.py').read())
