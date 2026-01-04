"""Entry point for Condition 3: E_counterfactual_A_low (Adaptive)
Explanation: counterfactual | Anthropomorphism: low (explores 0.2-0.4)"""
import os, sys, streamlit as st
os.environ['ANTHROKIT_EXPLANATION'] = 'counterfactual'
os.environ['ANTHROKIT_ANTHRO'] = 'low'
os.environ['ADAPTIVE_MODE'] = 'enabled'
os.environ['ADAPTIVE_RANGE_MIN'] = '0.2'
os.environ['ADAPTIVE_RANGE_MAX'] = '0.4'
os.environ['ADAPTIVE_TOKENS'] = 'warmth,empathy'
sys.path.append('src')
exec(open('src/app.py').read())
