"""Entry point for NoA Personalized condition
Anthropomorphism: None (warmth=0.00 fixed)
Explanation: feature_importance
Personality: Adapted (TIPI-based personality adjustments enabled)
"""
import os, sys
from pathlib import Path

os.environ['ANTHROKIT_EXPLANATION'] = 'feature_importance'
os.environ['ANTHROKIT_ANTHRO'] = 'none'
os.environ['ADAPTIVE_MODE'] = 'enabled'
os.environ['PERSONALITY_ADAPTATION'] = 'enabled'

# Get absolute path to app.py
app_path = Path(__file__).parent / 'app.py'
exec(app_path.read_text())
