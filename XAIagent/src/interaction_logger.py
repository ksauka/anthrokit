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
            
        # CRITICAL: participant_id must be explicit Prolific ID - no auto-generation
        if not participant_id:
            raise ValueError("participant_id is required and must be the Prolific ID")
        self.participant_id = participant_id
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
            "turns": [],
            
            # Task fidelity tracking (per requirements)
            "decision_seen": False,
            "why_triggered": False,
            "num_corrections": 0,
            
            # Categorical tone settings (will be set in start_session)
            "emoji_policy_final": None,
            "selfref_final": None,
            
            # Generation metadata
            "model_name": None,
            "temperature_base": None,
            "temperature_final": None,
            "temp_boost_applied": False
        }
        
        # Current turn tracking
        self.current_turn = None
        self.turn_counter = 0
        
    def start_session(self, condition_preset: str, condition_adapt: bool, personality_scores: Dict = None,
                     base_tone: Dict = None, final_tone: Dict = None):
        """
        Start a new session.
        
        Args:
            condition_preset: "HighA" or "LowA"
            condition_adapt: True if personality adaptation enabled
            personality_scores: TIPI Big Five scores {E, A, C, N, O}
            base_tone: Base tone configuration (warmth, empathy, formality, hedging)
            final_tone: Final tone after personality adjustments
        """
        self.session_data["condition_preset"] = condition_preset
        self.session_data["condition_adapt"] = condition_adapt
        self.session_data["personality_scores"] = personality_scores or {}
        
        # REQUIRED: Set tone configuration (base and final)
        if base_tone:
            self.session_data["warmth_base"] = base_tone.get("warmth")
            self.session_data["empathy_base"] = base_tone.get("empathy")
            self.session_data["formality_base"] = base_tone.get("formality")
            self.session_data["hedging_base"] = base_tone.get("hedging")
            
        if final_tone:
            self.session_data["warmth_final"] = final_tone.get("warmth")
            self.session_data["empathy_final"] = final_tone.get("empathy")
            self.session_data["formality_final"] = final_tone.get("formality")
            self.session_data["hedging_final"] = final_tone.get("hedging")
            self.session_data["emoji_policy_final"] = final_tone.get("emoji", 0)
            self.session_data["selfref_final"] = 1 if final_tone.get("self_reference") else 0
        
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
            "timestamp": datetime.now().isoformat(),
        }
        
        # Only add fields if they have values
        if prompt_id:
            self.current_turn["prompt_id"] = prompt_id
        if user_input:
            self.current_turn["user_input"] = user_input
        
    def log_output(self, assistant_output: str):
        """
        Log assistant's generated output.
        
        Args:
            assistant_output: Generated text
        """
        if self.current_turn and assistant_output:
            self.current_turn["assistant_output"] = assistant_output
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
    
    def log_task_event(self, event_type: str):
        """
        Log task fidelity events (per requirements).
        
        Args:
            event_type: "decision_seen" | "why_triggered" | "correction"
        """
        if event_type == "decision_seen":
            self.session_data["decision_seen"] = True
        elif event_type == "why_triggered":
            self.session_data["why_triggered"] = True
        elif event_type == "correction":
            self.session_data["num_corrections"] += 1
    
    def set_generation_metadata(self, model_name: str, temp_base: float, 
                                temp_final: float, temp_boost: bool):
        """
        Set generation metadata for the session (REQUIRED).
        
        Args:
            model_name: Model identifier (e.g., "gpt-4o-mini")
            temp_base: Base temperature from preset
            temp_final: Final temperature after boost
            temp_boost: Whether temperature boost was applied
        """
        self.session_data["model_name"] = model_name
        self.session_data["temperature_base"] = temp_base
        self.session_data["temperature_final"] = temp_final
        self.session_data["temp_boost_applied"] = temp_boost
    
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
        
        # Calculate time_on_task_sec
        if self.session_data["start_timestamp"] and self.session_data["end_timestamp"]:
            start = datetime.fromisoformat(self.session_data["start_timestamp"])
            end = datetime.fromisoformat(self.session_data["end_timestamp"])
            self.session_data["time_on_task_sec"] = (end - start).total_seconds()
        
        # Note: Tone configuration should already be set in start_session
        
        # Validate critical fields for calibration analysis
        required_fields = [
            "warmth_base", "warmth_final",
            "empathy_base", "empathy_final", 
            "formality_base", "formality_final",
            "hedging_base", "hedging_final",
            "temperature_base", "temperature_final",
            "model_name", "condition_preset"
        ]
        missing = [f for f in required_fields if self.session_data.get(f) is None]
        if missing:
            print(f"⚠️ WARNING: Missing calibration fields: {', '.join(missing)}")
        
        # Save final session log
        self._save_session(backup=False)
        
        print(f"[InteractionLogger] Session ended: {completion_status}")
        print(f"  Total turns: {self.session_data['total_turns']}")
        print(f"  Log saved: {self._get_log_path()}")
    
    def _clean_data(self, data):
        """Recursively remove null, empty dict, empty list, and 0 values from data."""
        if isinstance(data, dict):
            return {
                k: self._clean_data(v) 
                for k, v in data.items() 
                if v is not None and v != {} and v != [] and v != ""
            }
        elif isinstance(data, list):
            return [self._clean_data(item) for item in data]
        else:
            return data
    
    def _save_session(self, backup: bool = False):
        """Save session data to GitHub private repo via API."""
        if not self.github_token or not self.repo_path:
            print("[InteractionLogger] Warning: GitHub credentials not configured. Skipping save.")
            return
            
        suffix = "_backup" if backup else ""
        filename = f"{self.session_id}{suffix}.json"
        
        # Get condition name from session data or use 'unknown'
        condition_name = self.session_data.get("condition_preset", "unknown_condition")
        
        # File path in GitHub repo - organized by condition
        file_path = f"interaction_logs/{condition_name}/{filename}"
        
        # Clean session data - remove null/empty fields
        clean_data = self._clean_data(self.session_data)
        
        # Prepare file content
        file_content = json.dumps(clean_data, indent=2)
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
            "message": f"{'Backup' if backup else 'Final'} log for session {self.session_id} ({condition_name})",
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

def create_logger_from_secrets(secrets, config, participant_id: str = None) -> InteractionLogger:
    """
    Create logger from Streamlit secrets and ab_config.
    
    Args:
        secrets: Streamlit secrets (st.secrets) with GITHUB_TOKEN and GITHUB_REPO
        config: The ab_config module with condition settings
        participant_id: Prolific ID (REQUIRED - no auto-generation)
    
    Returns:
        Initialized InteractionLogger
    
    Raises:
        ValueError: If participant_id is not provided
    """
    if not participant_id:
        raise ValueError("participant_id (Prolific ID) is required - no auto-generation allowed")
    
    # Get GitHub credentials from secrets
    github_token = secrets.get("GITHUB_TOKEN", None)
    github_repo = secrets.get("GITHUB_REPO", None)
    
    # Create logger with GitHub credentials and Prolific ID
    logger = InteractionLogger(
        github_token=github_token,
        github_repo=github_repo,
        participant_id=participant_id
    )
    
    return logger

# End of InteractionLogger module
