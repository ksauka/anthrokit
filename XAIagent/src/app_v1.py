"""Entry point for HighA Fixed condition
Anthropomorphism: High (warmth=0.70 fixed)
Explanation: feature_importance
Personality: None (fixed preset)
"""
import os, sys, streamlit as st
os.environ['ANTHROKIT_EXPLANATION'] = 'feature_importance'
os.environ['ANTHROKIT_ANTHRO'] = 'high'
os.environ['ADAPTIVE_MODE'] = 'disabled'
os.environ['PERSONALITY_ADAPTATION'] = 'disabled'
sys.path.append('src')
exec(open('src/app.py').read())
