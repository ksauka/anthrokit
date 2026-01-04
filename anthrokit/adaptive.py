"""Adaptive anthropomorphism: Dynamic threshold optimization for research.

This module provides tools for researchers to:
1. Explore anthropomorphism thresholds dynamically
2. Find minimal effective anthropomorphism (MEA)
3. Optimize token values based on SOCIAL PRESENCE (not direct outcomes)
4. Conduct multi-level experiments beyond binary HighA/LowA

CAUSAL MODEL:
    Anthropomorphism → Social Presence → Trust/Acceptance/Satisfaction
    
    - Anthropomorphism (warmth, empathy, etc.) creates social presence
    - Social presence mediates effects on trust and other outcomes
    - Individual differences (Big 5) moderate these relationships

Research Questions:
- What is the minimal anthropomorphism needed for social presence?
- Which tokens have the strongest effects on social presence?
- Are there optimal intermediate levels between HighA and LowA?
- How do personality traits (Big 5) moderate anthropomorphism effects?
- Do optimal thresholds vary by domain or user characteristics?

Example:
    >>> from anthrokit.adaptive import ThresholdOptimizer
    >>> optimizer = ThresholdOptimizer(
    ...     base_preset="LowA",
    ...     target_metric="trust"
    ... )
    >>> preset = optimizer.get_next_condition()
    >>> # User interacts with preset...
    >>> optimizer.record_outcome(preset, trust_score=4.2)
"""

from __future__ import annotations

import random
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import json
from pathlib import Path

from .config import load_preset


@dataclass
class OutcomeRecord:
    """Record of user outcome for a given preset configuration.
    
    Attributes:
        preset_config: Token configuration used
        outcomes: Dictionary of outcome metrics
            - REQUIRED: 'social_presence' (primary optimization target)
            - Optional: 'trust', 'satisfaction', 'acceptance' (mediated outcomes)
        user_id: Optional user identifier
        domain: Optional domain/context
        personality: Optional Big 5 personality traits (for moderation analysis)
        timestamp: Optional timestamp
        
    Causal Model:
        Anthropomorphism (preset_config) → Social Presence → Other Outcomes
    """
    preset_config: Dict[str, Any]
    outcomes: Dict[str, float]  # Must include 'social_presence'
    user_id: Optional[str] = None
    domain: Optional[str] = None
    personality: Optional[Dict[str, float]] = None  # Big 5 traits
    timestamp: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "preset_config": self.preset_config,
            "outcomes": self.outcomes,
            "user_id": self.user_id,
            "domain": self.domain,
            "personality": self.personality,
            "timestamp": self.timestamp,
        }


class ThresholdExplorer:
    """Systematic exploration of anthropomorphism threshold space.
    
    Generates preset variations along specific dimensions to find
    minimal effective anthropomorphism and optimal intermediate levels.
    
    Example:
        >>> explorer = ThresholdExplorer()
        >>> # Generate 5 levels of warmth between LowA and HighA
        >>> presets = explorer.explore_dimension("warmth", n_levels=5)
        >>> for i, preset in enumerate(presets):
        ...     print(f"Level {i}: warmth={preset['warmth']}")
    """
    
    def __init__(
        self,
        base_low: Optional[Dict[str, Any]] = None,
        base_high: Optional[Dict[str, Any]] = None
    ):
        """Initialize explorer with base presets.
        
        Args:
            base_low: LowA preset (default: load from config)
            base_high: HighA preset (default: load from config)
        """
        self.base_low = base_low or load_preset("LowA")
        self.base_high = base_high or load_preset("HighA")
    
    def explore_dimension(
        self,
        dimension: str,
        n_levels: int = 5,
        base: str = "LowA"
    ) -> List[Dict[str, Any]]:
        """Generate presets varying one dimension.
        
        Args:
            dimension: Token to vary (e.g., "warmth", "empathy")
            n_levels: Number of levels to generate
            base: Base preset to start from ("LowA" or "HighA")
            
        Returns:
            List of preset dictionaries with varying dimension
            
        Example:
            >>> presets = explorer.explore_dimension("warmth", n_levels=5)
            >>> # Returns: warmth = [0.25, 0.36, 0.47, 0.59, 0.70]
        """
        base_preset = self.base_low if base == "LowA" else self.base_high
        low_val = self.base_low.get(dimension, 0.0)
        high_val = self.base_high.get(dimension, 1.0)
        
        if isinstance(low_val, (int, float)):
            # Numeric dimension
            values = [
                low_val + (high_val - low_val) * i / (n_levels - 1)
                for i in range(n_levels)
            ]
        else:
            # Categorical dimension - return extremes
            return [
                {**base_preset, dimension: low_val},
                {**base_preset, dimension: high_val}
            ]
        
        return [
            {**base_preset, dimension: val}
            for val in values
        ]
    
    def explore_multi_dimension(
        self,
        dimensions: List[str],
        n_levels: int = 3
    ) -> List[Dict[str, Any]]:
        """Generate presets varying multiple dimensions (factorial design).
        
        Args:
            dimensions: List of tokens to vary
            n_levels: Number of levels per dimension
            
        Returns:
            List of preset combinations (n_levels^len(dimensions) presets)
            
        Warning:
            Grows exponentially! Use cautiously with many dimensions.
            
        Example:
            >>> presets = explorer.explore_multi_dimension(
            ...     ["warmth", "empathy"],
            ...     n_levels=3
            ... )
            >>> len(presets)
            9  # 3^2 combinations
        """
        from itertools import product
        
        dimension_values = {}
        for dim in dimensions:
            low_val = self.base_low.get(dim, 0.0)
            high_val = self.base_high.get(dim, 1.0)
            
            if isinstance(low_val, (int, float)):
                dimension_values[dim] = [
                    low_val + (high_val - low_val) * i / (n_levels - 1)
                    for i in range(n_levels)
                ]
            else:
                dimension_values[dim] = [low_val, high_val]
        
        # Generate all combinations
        presets = []
        for combo in product(*dimension_values.values()):
            preset = dict(self.base_low)  # Start with LowA base
            for dim, val in zip(dimensions, combo):
                preset[dim] = val
            presets.append(preset)
        
        return presets
    
    def find_minimal_effective(
        self,
        dimension: str,
        outcome_function: Callable[[Dict[str, Any]], float],
        threshold: float = 0.8,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """Find minimal anthropomorphism level achieving outcome threshold.
        
        Uses binary search to find the lowest level of a dimension that
        still achieves the desired outcome.
        
        Args:
            dimension: Token to optimize
            outcome_function: Function that takes preset and returns outcome metric
            threshold: Minimum acceptable outcome value
            max_iterations: Maximum search iterations
            
        Returns:
            Minimal effective preset configuration
            
        Example:
            >>> def measure_trust(preset):
            ...     # Simulate user study
            ...     return preset['warmth'] * 5  # Trust score 0-5
            >>> minimal = explorer.find_minimal_effective(
            ...     "warmth",
            ...     measure_trust,
            ...     threshold=3.5
            ... )
            >>> minimal['warmth']
            0.7  # Minimal warmth for trust ≥ 3.5
        """
        low = self.base_low.get(dimension, 0.0)
        high = self.base_high.get(dimension, 1.0)
        
        for _ in range(max_iterations):
            mid = (low + high) / 2
            test_preset = {**self.base_low, dimension: mid}
            outcome = outcome_function(test_preset)
            
            if outcome >= threshold:
                high = mid  # Can go lower
            else:
                low = mid  # Need to go higher
            
            if abs(high - low) < 0.01:  # Convergence
                break
        
        return {**self.base_low, dimension: high}


class ThresholdOptimizer:
    """Multi-armed bandit optimizer for anthropomorphism thresholds.
    
    Balances exploration (trying new configurations) with exploitation
    (using known good configurations) to find optimal thresholds online.
    
    Uses Thompson Sampling for Bayesian optimization.
    
    Example:
        >>> optimizer = ThresholdOptimizer(
        ...     tokens=["warmth", "empathy"],
        ...     n_levels=5
        ... )
        >>> 
        >>> # In experiment loop:
        >>> for user in users:
        ...     preset = optimizer.get_next_condition()
        ...     outcome = run_experiment(user, preset)
        ...     optimizer.record_outcome(preset, {"trust": outcome})
        >>> 
        >>> best = optimizer.get_best_preset()
        >>> print(f"Optimal: {best}")
    """
    
    def __init__(
        self,
        tokens: Optional[List[str]] = None,
        n_levels: int = 5,
        base_preset: str = "LowA",
        exploration_rate: float = 0.2,
        target_metric: str = "social_presence",
        threshold_range: Optional[tuple[float, float]] = None
    ):
        """Initialize optimizer.
        
        Args:
            tokens: Tokens to optimize (default: numeric tokens)
            n_levels: Number of levels per token
            base_preset: Base preset to start from
            exploration_rate: Probability of exploring vs exploiting
            target_metric: Metric to optimize (default: "social_presence")
                          NOTE: Optimize SOCIAL PRESENCE, not trust/acceptance
                          Causal model: Anthropomorphism → Social Presence → Outcomes
            threshold_range: Optional (min, max) range to constrain exploration
                           e.g., (0.6, 0.8) for high anthro, (0.2, 0.4) for low
        """
        self.tokens = tokens or ["warmth", "formality", "empathy", "hedging"]
        self.n_levels = n_levels
        self.base_preset = base_preset
        self.exploration_rate = exploration_rate
        self.target_metric = target_metric
        self.threshold_range = threshold_range
        
        # Generate preset pool
        explorer = ThresholdExplorer()
        self.preset_pool: List[Dict[str, Any]] = []
        
        if threshold_range:
            # Generate presets within specified range for each token
            base = load_preset(base_preset)
            for token in self.tokens:
                for i in range(n_levels):
                    # Generate values within the threshold range
                    val = threshold_range[0] + (threshold_range[1] - threshold_range[0]) * i / (n_levels - 1)
                    preset = dict(base)
                    preset[token] = val
                    self.preset_pool.append(preset)
        else:
            # Standard exploration across full range
            for token in self.tokens:
                presets = explorer.explore_dimension(token, n_levels, base_preset)
                self.preset_pool.extend(presets)
        
        # Outcome tracking
        self.outcomes: List[OutcomeRecord] = []
        self.preset_scores: Dict[str, List[float]] = defaultdict(list)
    
    def _preset_key(self, preset: Dict[str, Any]) -> str:
        """Generate hashable key for preset."""
        key_tokens = {k: v for k, v in preset.items() if k in self.tokens}
        return json.dumps(key_tokens, sort_keys=True)
    
    def get_next_condition(self) -> Dict[str, Any]:
        """Get next preset to test (exploration or exploitation).
        
        Returns:
            Preset configuration for next experiment
        """
        # Exploration: random preset
        if random.random() < self.exploration_rate or not self.outcomes:
            return random.choice(self.preset_pool)
        
        # Exploitation: Thompson sampling
        # Sample from posterior for each preset, pick best sample
        best_sample = -float('inf')
        best_preset = self.preset_pool[0]
        
        for preset in self.preset_pool:
            key = self._preset_key(preset)
            scores = self.preset_scores.get(key, [])
            
            if not scores:
                # Unsampled preset - give it high priority
                sample = float('inf')
            else:
                # Sample from posterior (normal approximation)
                mean = sum(scores) / len(scores)
                std = (sum((x - mean)**2 for x in scores) / len(scores))**0.5 + 0.1
                sample = random.gauss(mean, std)
            
            if sample > best_sample:
                best_sample = sample
                best_preset = preset
        
        return best_preset
    
    def record_outcome(
        self,
        preset: Dict[str, Any],
        outcomes: Dict[str, float],
        user_id: Optional[str] = None,
        domain: Optional[str] = None,
        personality: Optional[Dict[str, float]] = None
    ):
        """Record outcome for a preset configuration.
        
        Args:
            preset: Preset configuration used
            outcomes: Dictionary of outcome metrics (MUST include 'social_presence')
            user_id: Optional user identifier
            domain: Optional domain/context
            personality: Optional Big 5 personality traits
                        {'openness': 3.5, 'conscientiousness': 4.2, ...}
        
        Note:
            outcomes MUST include 'social_presence' as primary metric
            Other metrics (trust, satisfaction) are secondary
        """
        import time
        
        record = OutcomeRecord(
            preset_config=preset,
            outcomes=outcomes,
            user_id=user_id,
            domain=domain,
            personality=personality,
            timestamp=time.time()
        )
        self.outcomes.append(record)
        
        # Update scores using target_metric (social_presence by default)
        key = self._preset_key(preset)
        score = outcomes.get(self.target_metric, 0)
        if score == 0 and self.target_metric not in outcomes:
            # Fallback to average if target metric missing (for backward compat)
            score = sum(outcomes.values()) / len(outcomes) if outcomes else 0
        self.preset_scores[key].append(score)
    
    def get_best_preset(self, metric: Optional[str] = None) -> Dict[str, Any]:
        """Get preset with best average outcome.
        
        Args:
            metric: Specific metric to optimize (default: uses target_metric='social_presence')
            
        Returns:
            Best performing preset configuration
        """
        if not self.outcomes:
            return load_preset(self.base_preset)
        
        # Use target_metric if no metric specified
        if metric is None:
            metric = self.target_metric
        
        preset_outcomes = defaultdict(list)
        for record in self.outcomes:
            key = self._preset_key(record.preset_config)
            preset_outcomes[key].append(record.outcomes.get(metric, 0.0))
        
        # Find best average
        best_key = max(
            preset_outcomes.keys(),
            key=lambda k: sum(preset_outcomes[k]) / len(preset_outcomes[k])
        )
        
        # Reconstruct preset
        return json.loads(best_key)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get optimization statistics.
        
        Returns:
            Dictionary with optimization metrics
        """
        if not self.outcomes:
            return {"n_trials": 0}
        
        return {
            "n_trials": len(self.outcomes),
            "n_unique_presets": len(self.preset_scores),
            "best_preset": self.get_best_preset(),
            "best_score": max(
                sum(scores) / len(scores)
                for scores in self.preset_scores.values()
            ) if self.preset_scores else 0.0,
            "coverage": len(self.preset_scores) / len(self.preset_pool)
        }
    
    def save(self, path: Path):
        """Save optimization state to file."""
        data = {
            "tokens": self.tokens,
            "n_levels": self.n_levels,
            "base_preset": self.base_preset,
            "exploration_rate": self.exploration_rate,
            "outcomes": [r.to_dict() for r in self.outcomes]
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load(cls, path: Path) -> 'ThresholdOptimizer':
        """Load optimization state from file."""
        with open(path, 'r') as f:
            data = json.load(f)
        
        optimizer = cls(
            tokens=data["tokens"],
            n_levels=data["n_levels"],
            base_preset=data["base_preset"],
            exploration_rate=data["exploration_rate"]
        )
        
        # Restore outcomes
        for outcome_dict in data["outcomes"]:
            optimizer.outcomes.append(OutcomeRecord(**outcome_dict))
            key = optimizer._preset_key(outcome_dict["preset_config"])
            avg = sum(outcome_dict["outcomes"].values()) / len(outcome_dict["outcomes"])
            optimizer.preset_scores[key].append(avg)
        
        return optimizer


__all__ = [
    "ThresholdExplorer",
    "ThresholdOptimizer",
    "OutcomeRecord",
]
