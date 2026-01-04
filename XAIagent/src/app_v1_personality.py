"""Entry point for HighA + Personality-Adapted condition
Anthropomorphism: High (warmth=0.70 base) + TIPI-based personality adjustments (±0.30)
Explanation: feature_importance
"""
import os, sys
from pathlib import Path

# Set base configuration for HighA
os.environ['ANTHROKIT_EXPLANATION'] = 'feature_importance'
os.environ['ANTHROKIT_ANTHRO'] = 'high'
os.environ['ADAPTIVE_MODE'] = 'disabled'

# Enable personality personalization
os.environ['PERSONALITY_ADAPTATION'] = 'enabled'

# Get absolute path to app.py
app_path = Path(__file__).parent / 'app.py'
exec(app_path.read_text())
