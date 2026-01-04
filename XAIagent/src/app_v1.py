"""Entry point for Condition 6: E_feature_importance_A_high (Adaptive)
Explanation: feature_importance | Anthropomorphism: high (explores 0.6-0.8)"""
import os, sys, streamlit as st
os.environ['ANTHROKIT_EXPLANATION'] = 'feature_importance'
os.environ['ANTHROKIT_ANTHRO'] = 'high'
os.environ['ADAPTIVE_MODE'] = 'enabled'
os.environ['ADAPTIVE_RANGE_MIN'] = '0.6'
os.environ['ADAPTIVE_RANGE_MAX'] = '0.8'
os.environ['ADAPTIVE_TOKENS'] = 'warmth,empathy'
sys.path.append('src')
exec(open('src/app.py').read())
