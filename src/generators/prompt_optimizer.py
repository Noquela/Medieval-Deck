"""
Prompt Optimizer for SDXL generation with 77-token CLIP limit handling.

Optimizes prompts for medieval card backgrounds with quality and style enhancement.
"""

import logging
from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import re
import json
from pathlib import Path

from ..models.card_models import CardType, Rarity

logger = logging.getLogger(__name__)


class PromptPriority(Enum):
    """Priority levels for prompt tokens."""
    CRITICAL = 1    # Must include (card type, main subject)
    HIGH = 2        # Important for quality (style, lighting)
    MEDIUM = 3      # Enhancing details (textures, atmosphere)
    LOW = 4         # Optional flourishes (extra details)


@dataclass
class TokenInfo:
    """Information about a prompt token."""
    token: str
    priority: PromptPriority
    weight: float = 1.0
    category: str = "general"


class PromptOptimizer:
    """
    Optimizes prompts for SDXL generation with CLIP token limit awareness.
    
    Features:
    - 77-token CLIP limit handling
    - Priority-based token selection
    - Medieval theme optimization
    - Quality enhancement
    - Style consistency
    """
    
    # CLIP tokenizer token limit
    MAX_TOKENS = 77
    
    def __init__(self, prompts_config_path: Optional[str] = None):
        """
        Initialize prompt optimizer.
        
        Args:
            prompts_config_path: Path to prompts configuration file
        """
        self.quality_tokens = self._get_quality_tokens()
        self.style_tokens = self._get_style_tokens()
        self.medieval_tokens = self._get_medieval_tokens()
        self.lighting_tokens = self._get_lighting_tokens()
        self.negative_tokens = self._get_negative_tokens()
        
        # Load custom prompts if available
        if prompts_config_path and Path(prompts_config_path).exists():
            self._load_prompts_config(prompts_config_path)
            
        logger.info("Prompt Optimizer initialized")
        
    def _get_quality_tokens(self) -> List[TokenInfo]:
        """Get quality enhancement tokens."""
        return [
            TokenInfo("masterpiece", PromptPriority.HIGH, 1.3, "quality"),
            TokenInfo("best quality", PromptPriority.HIGH, 1.2, "quality"),
            TokenInfo("high quality", PromptPriority.HIGH, 1.1, "quality"),
            TokenInfo("ultra detailed", PromptPriority.MEDIUM, 1.1, "quality"),
            TokenInfo("sharp focus", PromptPriority.MEDIUM, 1.0, "quality"),
            TokenInfo("professional", PromptPriority.MEDIUM, 1.0, "quality"),
            TokenInfo("8k resolution", PromptPriority.LOW, 1.0, "quality"),
            TokenInfo("highly detailed", PromptPriority.LOW, 1.0, "quality"),
        ]
        
    def _get_style_tokens(self) -> List[TokenInfo]:
        """Get style-specific tokens."""
        return [
            TokenInfo("medieval fantasy", PromptPriority.CRITICAL, 1.4, "style"),
            TokenInfo("dark fantasy", PromptPriority.HIGH, 1.3, "style"),
            TokenInfo("gothic", PromptPriority.HIGH, 1.2, "style"),
            TokenInfo("renaissance art", PromptPriority.MEDIUM, 1.1, "style"),
            TokenInfo("oil painting", PromptPriority.MEDIUM, 1.0, "style"),
            TokenInfo("concept art", PromptPriority.MEDIUM, 1.0, "style"),
            TokenInfo("fantasy art", PromptPriority.LOW, 1.0, "style"),
        ]
        
    def _get_medieval_tokens(self) -> Dict[CardType, List[TokenInfo]]:
        """Get medieval-themed tokens by card type."""
        return {
            CardType.CREATURE: [
                TokenInfo("ancient beast", PromptPriority.CRITICAL, 1.3, "creature"),
                TokenInfo("mythical creature", PromptPriority.HIGH, 1.2, "creature"),
                TokenInfo("dragon", PromptPriority.HIGH, 1.2, "creature"),
                TokenInfo("knight", PromptPriority.HIGH, 1.1, "creature"),
                TokenInfo("warrior", PromptPriority.MEDIUM, 1.0, "creature"),
                TokenInfo("monster", PromptPriority.MEDIUM, 1.0, "creature"),
            ],
            CardType.SPELL: [
                TokenInfo("magical energy", PromptPriority.CRITICAL, 1.3, "spell"),
                TokenInfo("arcane magic", PromptPriority.HIGH, 1.2, "spell"),
                TokenInfo("spell circle", PromptPriority.HIGH, 1.1, "spell"),
                TokenInfo("mystical runes", PromptPriority.MEDIUM, 1.1, "spell"),
                TokenInfo("enchantment", PromptPriority.MEDIUM, 1.0, "spell"),
                TokenInfo("sorcery", PromptPriority.LOW, 1.0, "spell"),
            ],
            CardType.ARTIFACT: [
                TokenInfo("ancient relic", PromptPriority.CRITICAL, 1.3, "artifact"),
                TokenInfo("magical item", PromptPriority.HIGH, 1.2, "artifact"),
                TokenInfo("ornate weapon", PromptPriority.HIGH, 1.1, "artifact"),
                TokenInfo("golden chalice", PromptPriority.MEDIUM, 1.1, "artifact"),
                TokenInfo("jeweled crown", PromptPriority.MEDIUM, 1.0, "artifact"),
                TokenInfo("sacred relic", PromptPriority.LOW, 1.0, "artifact"),
            ],
            CardType.LAND: [
                TokenInfo("medieval castle", PromptPriority.CRITICAL, 1.3, "land"),
                TokenInfo("ancient kingdom", PromptPriority.HIGH, 1.2, "land"),
                TokenInfo("dark forest", PromptPriority.HIGH, 1.1, "land"),
                TokenInfo("stone fortress", PromptPriority.MEDIUM, 1.1, "land"),
                TokenInfo("mountain pass", PromptPriority.MEDIUM, 1.0, "land"),
                TokenInfo("village", PromptPriority.LOW, 1.0, "land"),
            ]
        }
        
    def _get_lighting_tokens(self) -> List[TokenInfo]:
        """Get lighting and atmosphere tokens."""
        return [
            TokenInfo("dramatic lighting", PromptPriority.HIGH, 1.2, "lighting"),
            TokenInfo("atmospheric", PromptPriority.HIGH, 1.1, "lighting"),
            TokenInfo("moody lighting", PromptPriority.MEDIUM, 1.1, "lighting"),
            TokenInfo("golden hour", PromptPriority.MEDIUM, 1.0, "lighting"),
            TokenInfo("candlelight", PromptPriority.MEDIUM, 1.0, "lighting"),
            TokenInfo("moonlight", PromptPriority.LOW, 1.0, "lighting"),
            TokenInfo("torch light", PromptPriority.LOW, 1.0, "lighting"),
        ]
        
    def _get_negative_tokens(self) -> List[str]:
        """Get negative prompt tokens."""
        return [
            "blurry", "low quality", "pixelated", "cartoon", "anime",
            "text", "watermark", "signature", "logo", "bad anatomy",
            "deformed", "distorted", "ugly", "poorly drawn",
            "modern", "contemporary", "futuristic", "sci-fi",
            "plastic", "toy", "3d render", "cgi"
        ]
        
    def _load_prompts_config(self, config_path: str) -> None:
        """Load custom prompts from configuration file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # Update tokens from config
            if "quality_tokens" in config:
                self.quality_tokens.extend([
                    TokenInfo(token, PromptPriority.MEDIUM, 1.0, "quality")
                    for token in config["quality_tokens"]
                ])
                
            if "negative_tokens" in config:
                self.negative_tokens.extend(config["negative_tokens"])
                
            logger.info(f"Loaded custom prompts from {config_path}")
            
        except Exception as e:
            logger.warning(f"Failed to load prompts config: {e}")
            
    def _tokenize_estimate(self, text: str) -> int:
        """
        Estimate token count for CLIP tokenizer.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Simple estimation based on word count and punctuation
        # Real CLIP tokenizer would be more accurate but requires transformers
        words = re.findall(r'\b\w+\b', text)
        punctuation = re.findall(r'[^\w\s]', text)
        
        # CLIP tends to split some words into subwords
        estimated_tokens = len(words) + len(punctuation)
        
        # Add buffer for subword tokenization
        return int(estimated_tokens * 1.2)
        
    def _select_tokens_by_priority(
        self,
        token_candidates: List[TokenInfo],
        max_tokens: int,
        used_tokens: int
    ) -> List[TokenInfo]:
        """
        Select tokens based on priority and remaining token budget.
        
        Args:
            token_candidates: List of candidate tokens
            max_tokens: Maximum tokens allowed
            used_tokens: Tokens already used
            
        Returns:
            Selected tokens that fit within budget
        """
        available_tokens = max_tokens - used_tokens
        selected = []
        
        # Sort by priority (lower enum value = higher priority)
        candidates_by_priority = sorted(
            token_candidates,
            key=lambda x: (x.priority.value, -x.weight)
        )
        
        current_tokens = 0
        for token_info in candidates_by_priority:
            token_count = self._tokenize_estimate(token_info.token)
            
            if current_tokens + token_count <= available_tokens:
                selected.append(token_info)
                current_tokens += token_count
            else:
                break
                
        return selected
        
    def _build_weighted_prompt(self, tokens: List[TokenInfo]) -> str:
        """
        Build prompt string with attention weights.
        
        Args:
            tokens: List of tokens with weights
            
        Returns:
            Formatted prompt string with weights
        """
        prompt_parts = []
        
        for token_info in tokens:
            if token_info.weight != 1.0:
                # Format with attention weight
                if token_info.weight > 1.0:
                    weight_str = f"{token_info.weight:.1f}"
                    prompt_parts.append(f"({token_info.token}:{weight_str})")
                else:
                    weight_str = f"{token_info.weight:.1f}"
                    prompt_parts.append(f"[{token_info.token}:{weight_str}]")
            else:
                prompt_parts.append(token_info.token)
                
        return ", ".join(prompt_parts)
        
    def optimize_prompt(
        self,
        base_prompt: str,
        card_type: CardType,
        rarity: Rarity,
        custom_tokens: Optional[List[str]] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Optimize prompt for SDXL generation with token limit awareness.
        
        Args:
            base_prompt: Base prompt text
            card_type: Type of card for context
            rarity: Card rarity for enhancement level
            custom_tokens: Additional custom tokens
            max_tokens: Maximum token limit (default: 77)
            
        Returns:
            Optimized prompt string
        """
        max_tokens = max_tokens or self.MAX_TOKENS
        
        # Start with base prompt tokens
        base_tokens = base_prompt.split(", ") if base_prompt else []
        base_token_count = sum(self._tokenize_estimate(token) for token in base_tokens)
        
        # Collect candidate tokens
        candidates = []
        
        # Add style tokens (always high priority)
        candidates.extend(self.style_tokens)
        
        # Add card type specific tokens
        if card_type in self.medieval_tokens:
            candidates.extend(self.medieval_tokens[card_type])
            
        # Add quality tokens based on rarity
        quality_count = {
            Rarity.COMMON: 1,
            Rarity.UNCOMMON: 2,
            Rarity.RARE: 3,
            Rarity.LEGENDARY: 4
        }.get(rarity, 1)
        
        candidates.extend(self.quality_tokens[:quality_count])
        
        # Add lighting tokens
        candidates.extend(self.lighting_tokens[:2])  # Limit lighting tokens
        
        # Add custom tokens if provided
        if custom_tokens:
            for token in custom_tokens:
                candidates.append(
                    TokenInfo(token, PromptPriority.MEDIUM, 1.0, "custom")
                )
                
        # Remove duplicates and filter already used
        used_tokens_set = set(token.lower() for token in base_tokens)
        unique_candidates = []
        
        for candidate in candidates:
            if candidate.token.lower() not in used_tokens_set:
                unique_candidates.append(candidate)
                used_tokens_set.add(candidate.token.lower())
                
        # Select tokens within budget
        selected_tokens = self._select_tokens_by_priority(
            unique_candidates,
            max_tokens,
            base_token_count
        )
        
        # Build final prompt
        final_tokens = base_tokens + [token.token for token in selected_tokens]
        optimized_prompt = ", ".join(final_tokens)
        
        # Verify token count
        final_token_count = self._tokenize_estimate(optimized_prompt)
        
        if final_token_count > max_tokens:
            logger.warning(
                f"Optimized prompt may exceed token limit: "
                f"{final_token_count}/{max_tokens} tokens"
            )
            
        logger.debug(
            f"Prompt optimization: {len(base_tokens)} -> {len(final_tokens)} tokens "
            f"({final_token_count}/{max_tokens})"
        )
        
        return optimized_prompt
        
    def get_negative_prompt(
        self,
        card_type: Optional[CardType] = None,
        additional_negatives: Optional[List[str]] = None
    ) -> str:
        """
        Get optimized negative prompt.
        
        Args:
            card_type: Card type for specific negatives
            additional_negatives: Additional negative tokens
            
        Returns:
            Negative prompt string
        """
        negatives = self.negative_tokens.copy()
        
        # Add card type specific negatives
        type_negatives = {
            CardType.CREATURE: ["robotic", "mechanical", "digital"],
            CardType.SPELL: ["physical", "solid", "mundane"],
            CardType.ARTIFACT: ["organic", "living", "natural"],
            CardType.LAND: ["indoor", "interior", "enclosed"]
        }
        
        if card_type in type_negatives:
            negatives.extend(type_negatives[card_type])
            
        if additional_negatives:
            negatives.extend(additional_negatives)
            
        return ", ".join(negatives)
        
    def analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Analyze prompt for token count and composition.
        
        Args:
            prompt: Prompt to analyze
            
        Returns:
            Analysis results
        """
        tokens = prompt.split(", ")
        token_count = self._tokenize_estimate(prompt)
        
        # Categorize tokens
        categories = {"quality": 0, "style": 0, "content": 0, "other": 0}
        
        quality_terms = [token.token.lower() for token in self.quality_tokens]
        style_terms = [token.token.lower() for token in self.style_tokens]
        
        for token in tokens:
            token_lower = token.lower()
            if any(quality_term in token_lower for quality_term in quality_terms):
                categories["quality"] += 1
            elif any(style_term in token_lower for style_term in style_terms):
                categories["style"] += 1
            elif token_lower in ["creature", "spell", "artifact", "land"]:
                categories["content"] += 1
            else:
                categories["other"] += 1
                
        return {
            "token_count": token_count,
            "estimated_tokens": token_count,
            "max_tokens": self.MAX_TOKENS,
            "tokens_remaining": self.MAX_TOKENS - token_count,
            "token_breakdown": categories,
            "total_terms": len(tokens),
            "efficiency": len(tokens) / max(token_count, 1)
        }
