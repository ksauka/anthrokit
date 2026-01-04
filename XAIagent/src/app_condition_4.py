"""Entry point for Condition 4: E_counterfactual_A_high (Adaptive)
Explanation: counterfactual | Anthropomorphism: high (explores 0.6-0.8)"""
import os, sys, streamlit as st
os.environ['ANTHROKIT_EXPLANATION'] = 'counterfactual'
os.environ['ANTHROKIT_ANTHRO'] = 'high'
os.environ['ADAPTIVE_MODE'] = 'enabled'
os.environ['ADAPTIVE_RANGE_MIN'] = '0.6'
os.environ['ADAPTIVE_RANGE_MAX'] = '0.8'
os.environ['ADAPTIVE_TOKENS'] = 'warmth,empathy'
sys.path.append('src')
exec(open('src/app.py').read())
