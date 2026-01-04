"""Entry point for Condition 2: E_none_A_high (Adaptive)
Explanation: none | Anthropomorphism: high (explores 0.6-0.8)"""
import os, sys, streamlit as st
os.environ['ANTHROKIT_EXPLANATION'] = 'none'
os.environ['ANTHROKIT_ANTHRO'] = 'high'
os.environ['ADAPTIVE_MODE'] = 'enabled'
os.environ['ADAPTIVE_RANGE_MIN'] = '0.6'
os.environ['ADAPTIVE_RANGE_MAX'] = '0.8'
os.environ['ADAPTIVE_TOKENS'] = 'warmth,empathy'
sys.path.append('src')
exec(open('src/app.py').read())
