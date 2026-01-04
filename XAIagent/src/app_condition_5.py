"""Entry point for LowA Fixed condition
Anthropomorphism: Low (warmth=0.25 fixed)
Explanation: feature_importance
Personality: None (fixed preset)
"""
import os, sys
from pathlib import Path

os.environ['ANTHROKIT_EXPLANATION'] = 'feature_importance'
os.environ['ANTHROKIT_ANTHRO'] = 'low'
os.environ['ADAPTIVE_MODE'] = 'disabled'
os.environ['PERSONALITY_ADAPTATION'] = 'disabled'

# Get absolute path to app.py
app_path = Path(__file__).parent / 'app.py'
exec(app_path.read_text())
