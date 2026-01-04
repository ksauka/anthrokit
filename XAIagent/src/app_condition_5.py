"""Entry point for Condition 5: E_feature_importance_A_low (Adaptive)
Explanation: feature_importance | Anthropomorphism: low (explores 0.2-0.4)"""
import os, sys, streamlit as st
os.environ['ANTHROKIT_EXPLANATION'] = 'feature_importance'
os.environ['ANTHROKIT_ANTHRO'] = 'low'
os.environ['ADAPTIVE_MODE'] = 'enabled'
os.environ['ADAPTIVE_RANGE_MIN'] = '0.2'
os.environ['ADAPTIVE_RANGE_MAX'] = '0.4'
os.environ['ADAPTIVE_TOKENS'] = 'warmth,empathy'
sys.path.append('src')
exec(open('src/app.py').read())
