"""
Stage B: Real User Interaction Logger
======================================
Comprehensive logging for user sessions with personality-adapted AI assistants.
Captures all data needed for analysis of temperature boost effectiveness and
personality adaptation in real-world usage.

Logs are pushed directly to GitHub private repo using GitHub API.
Works in both local and Streamlit Cloud environments.

Author: AnthroKit Research Team
Date: January 14, 2026
"""

import json
import os
import base64
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import uuid
import requests


class InteractionLogger:
    """Logs user interaction data to GitHub private repo for Stage B analysis."""
    
    def __init__(self, github_token: str = None, github_repo: str = None, participant_id: str = None):
        """
        Initialize interaction logger with GitHub API credentials.
        
        Args:
            github_token: GitHub personal access token (from st.secrets or .env)
            github_repo: GitHub repo URL (e.g., https://github.com/user/repo.git)
            participant_id: Unique participant ID (auto-generated if None)
        """
        self.github_token = github_token
        self.github_repo = github_repo
        
        # Parse repo path from URL
        if github_repo:
            self.repo_path = github_repo.replace("https://github.com/", "").replace(".git", "")
        else:
            self.repo_path = None
            
        self.participant_id = participant_id or f"P{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        self.session_id = f"S{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Session-level data
        self.session_data = {
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "condition_preset": None,  # HighA or LowA
            "condition_adapt": None,   # Personality adaptation enabled?
            "start_timestamp": datetime.now().isoformat(),
            "end_timestamp": None,
            "total_turns": 0,
            "completion_status": "in_progress",  # in_progress, completed, abandoned
            "turns": []
        }
        
        # Current turn tracking
        self.current_turn = None
        self.turn_counter = 0
        
    def start_session(self, condition_preset: str, condition_adapt: bool, personality_scores: Dict = None):
        """
        Start a new session.
        
        Args:
            condition_preset: "HighA" or "LowA"
            condition_adapt: True if personality adaptation enabled
            personality_scores: TIPI Big Five scores {E, A, C, N, O}
        """
        self.session_data["condition_preset"] = condition_preset
        self.session_data["condition_adapt"] = condition_adapt
        self.session_data["personality_scores"] = personality_scores or {}
        
        print(f"[InteractionLogger] Session started: {self.session_id}")
        print(f"  Participant: {self.participant_id}")
        print(f"  Condition: {condition_preset} | Adapt: {condition_adapt}")
    
    def start_turn(self, turn_type: str, prompt_id: str = None, user_input: str = None):
        """
        Start logging a new turn.
        
        Args:
            turn_type: "greet" | "collect" | "correct" | "decision" | "explain" | "whatif"
            prompt_id: Template ID for this turn
            user_input: User's input (if response turn)
        """
        self.turn_counter += 1
        self.current_turn = {
            "turn_id": self.turn_counter,
            "turn_type": turn_type,
            "prompt_id": prompt_id,
            "user_input": user_input,
            "timestamp": datetime.now().isoformat(),
            
            # Will be populated before end_turn()
            "decoding": {},
            "tone_trace": {},
            "deltas": {},
            "assistant_output": None,
            "judge_evaluation": None,
            "latency_ms": None,
            "tokens_used": None,
            "error": None
        }
        
    def log_decoding_params(self, base_temp: float, boost_applied: float, final_temp: float, 
                           max_tokens: int = None, top_p: float = None):
        """
        Log LLM decoding parameters for this turn.
        
        Args:
            base_temp: Base temperature from preset
            boost_applied: Temperature boost added (0.0 if none)
            final_temp: Final temperature used (base + boost, capped at 0.7)
            max_tokens: Max tokens for generation
            top_p: Nucleus sampling parameter (if used)
        """
        if self.current_turn:
            self.current_turn["decoding"] = {
                "base_temp": base_temp,
                "boost_applied": boost_applied,
                "final_temp": final_temp,
                "max_tokens": max_tokens,
                "top_p": top_p
            }
    
    def log_tone_trace(self, base_preset: Dict, personality_adjustments: Dict, final_tone_config: Dict):
        """
        Log tone parameter trace (base → personality → final).
        
        Args:
            base_preset: Base tone config from condition (HighA/LowA)
            personality_adjustments: TIPI Big Five scores applied
            final_tone_config: Final tone config after personality mapping
        """
        if self.current_turn:
            self.current_turn["tone_trace"] = {
                "base_preset": base_preset.copy(),
                "personality_adjustments": personality_adjustments.copy() if personality_adjustments else {},
                "final_tone_config": final_tone_config.copy()
            }
            
            # Calculate deltas (final - base)
            self.current_turn["deltas"] = {}
            for key in ["warmth", "empathy", "formality", "hedging"]:
                if key in base_preset and key in final_tone_config:
                    self.current_turn["deltas"][key] = round(
                        final_tone_config[key] - base_preset[key], 3
                    )
    
    def log_output(self, assistant_output: str, latency_ms: float = None, tokens_used: int = None):
        """
        Log assistant's generated output.
        
        Args:
            assistant_output: Generated text
            latency_ms: API latency in milliseconds
            tokens_used: Total tokens used (prompt + completion)
        """
        if self.current_turn:
            self.current_turn["assistant_output"] = assistant_output
            self.current_turn["latency_ms"] = latency_ms
            self.current_turn["tokens_used"] = tokens_used
            self.current_turn["word_count"] = len(assistant_output.split())
    
    def log_judge_evaluation(self, scores: Dict[str, float], evidence: Dict[str, List[str]]):
        """
        Log LLM-as-a-Judge evaluation (optional - for Stage B analysis).
        
        Args:
            scores: Dimension scores (1-7 scale)
            evidence: Evidence quotes for each dimension
        """
        if self.current_turn:
            self.current_turn["judge_evaluation"] = {
                "scores": scores,
                "evidence": evidence
            }
    
    def log_error(self, error_type: str, error_message: str):
        """Log any errors that occurred during turn."""
        if self.current_turn:
            self.current_turn["error"] = {
                "type": error_type,
                "message": error_message
            }
    
    def end_turn(self):
        """Finalize current turn and add to session."""
        if self.current_turn:
            self.session_data["turns"].append(self.current_turn)
            self.session_data["total_turns"] = len(self.session_data["turns"])
            self.current_turn = None
            
            # Auto-save every 5 turns (in case of crash)
            if len(self.session_data["turns"]) % 5 == 0:
                self._save_session(backup=True)
    
    def end_session(self, completion_status: str = "completed"):
        """
        End session and save final log.
        
        Args:
            completion_status: "completed" | "abandoned" | "error"
        """
        self.session_data["end_timestamp"] = datetime.now().isoformat()
        self.session_data["completion_status"] = completion_status
        self.session_data["total_turns"] = len(self.session_data["turns"])
        
        # Save final session log
        self._save_session(backup=False)
        
        print(f"[InteractionLogger] Session ended: {completion_status}")
        print(f"  Total turns: {self.session_data['total_turns']}")
        print(f"  Log saved: {self._get_log_path()}")
    
    def _save_session(self, backup: bool = False):
        """Save session data to GitHub private repo via API."""
        if not self.github_token or not self.repo_path:
            print("[InteractionLogger] Warning: GitHub credentials not configured. Skipping save.")
            return
            
        suffix = "_backup" if backup else ""
        filename = f"{self.session_id}{suffix}.json"
        
        # File path in GitHub repo
        file_path = f"interaction_logs/{filename}"
        
        # Prepare file content
        file_content = json.dumps(self.session_data, indent=2)
        file_content_encoded = base64.b64encode(file_content.encode()).decode()
        
        # GitHub API headers
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Create/update file via GitHub API
        api_url = f"https://api.github.com/repos/{self.repo_path}/contents/{file_path}"
        
        # Check if file exists (for updates)
        get_response = requests.get(api_url, headers=headers)
        
        commit_data = {
            "message": f"{'Backup' if backup else 'Final'} log for session {self.session_id}",
            "content": file_content_encoded,
            "branch": "main"
        }
        
        # If file exists, include SHA for update
        if get_response.status_code == 200:
            commit_data["sha"] = get_response.json()["sha"]
        
        # Push to GitHub
        response = requests.put(api_url, headers=headers, json=commit_data)
        
        if response.status_code in [200, 201]:
            print(f"[InteractionLogger] ✓ Log saved to GitHub: {file_path}")
        else:
            print(f"[InteractionLogger] ✗ Failed to save log: {response.status_code}")
            print(f"  Error: {response.text[:200]}")
    
    def _get_log_path(self, suffix: str = "") -> str:
        """Get log file path in GitHub repo."""
        filename = f"{self.session_id}{suffix}.json"
        return f"interaction_logs/{filename}"
    
    def get_session_summary(self) -> Dict:
        """Get summary statistics for current session."""
        turns = self.session_data["turns"]
        if not turns:
            return {"total_turns": 0}
        
        # Calculate average scores across turns (if judge evaluations exist)
        avg_scores = {}
        judge_turns = [t for t in turns if t.get("judge_evaluation")]
        if judge_turns:
            for dim in ["anthropomorphism", "warmth", "empathy", "formality", "hedging", "clarity"]:
                scores = [t["judge_evaluation"]["scores"].get(dim, 0) for t in judge_turns]
                avg_scores[f"avg_{dim}"] = round(sum(scores) / len(scores), 2) if scores else 0
        
        return {
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "total_turns": len(turns),
            "completion_status": self.session_data["completion_status"],
            "turn_types": {tt: len([t for t in turns if t["turn_type"] == tt]) 
                          for tt in set(t["turn_type"] for t in turns)},
            "avg_latency_ms": round(
                sum(t.get("latency_ms", 0) for t in turns if t.get("latency_ms")) / len(turns), 2
            ) if any(t.get("latency_ms") for t in turns) else None,
            "total_tokens": sum(t.get("tokens_used", 0) for t in turns if t.get("tokens_used")),
            **avg_scores
        }


# ============================================================================
# Helper Functions for Integration
# ============================================================================

def create_logger_from_secrets(secrets, config) -> InteractionLogger:
    """
    Create logger from Streamlit secrets and ab_config.
    
    Args:
        secrets: Streamlit secrets (st.secrets) with GITHUB_TOKEN and GITHUB_REPO
        config: The ab_config module with condition settings
    
    Returns:
        Initialized InteractionLogger
    """
    # Get GitHub credentials from secrets
    github_token = secrets.get("GITHUB_TOKEN", None)
    github_repo = secrets.get("GITHUB_REPO", None)
    
    # Determine condition
    condition_preset = "HighA" if config.show_anthropomorphic else "LowA"
    condition_adapt = getattr(config, 'personality_adaptation_enabled', False)
    
    # Create logger with GitHub credentials
    logger = InteractionLogger(
        github_token=github_token,
        github_repo=github_repo
    )
    
    # Get personality scores if available
    personality_scores = None
    if hasattr(config, 'user_personality') and config.user_personality:
        personality_scores = {
            "E": config.user_personality.get("extraversion", 4),
            "A": config.user_personality.get("agreeableness", 4),
            "C": config.user_personality.get("conscientiousness", 4),
            "N": config.user_personality.get("neuroticism", 4),
            "O": config.user_personality.get("openness", 4)
        }
    
    logger.start_session(condition_preset, condition_adapt, personality_scores)
    
    return logger


def log_generation(logger: InteractionLogger, turn_type: str, config, 
                  assistant_output: str, latency_ms: float = None):
    """
    Quick helper to log a generation turn.
    
    Args:
        logger: InteractionLogger instance
        turn_type: Type of turn (greet/collect/correct/etc)
        config: ab_config with tone settings
        assistant_output: Generated text
        latency_ms: API latency
    """
    logger.start_turn(turn_type=turn_type)
    
    # Log decoding params
    preset = getattr(config, 'final_tone_config', None)
    if preset:
        base_temp = preset.get("temperature", 0.3)
        warmth = preset.get("warmth", 0.25)
        
        # Calculate boost (replicate production logic)
        boost = 0.25 if warmth > 0.50 else 0.0
        final_temp = min(base_temp + boost, 0.7)
        
        logger.log_decoding_params(
            base_temp=base_temp,
            boost_applied=boost,
            final_temp=final_temp
        )
    
    # Log tone trace
    if hasattr(config, 'base_preset') and hasattr(config, 'final_tone_config'):
        logger.log_tone_trace(
            base_preset=config.base_preset,
            personality_adjustments=getattr(config, 'user_personality', {}),
            final_tone_config=config.final_tone_config
        )
    
    # Log output
    logger.log_output(assistant_output, latency_ms)
    
    logger.end_turn()
