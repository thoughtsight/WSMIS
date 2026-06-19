"""
AI Service for Dashboard Narratives and Actions
Provides optional AI-generated content with deterministic rule-based fallbacks.
Uses a provider pattern to support multiple AI backends (Gemini, Anthropic, etc.).
"""

import json
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    def generate_narrative(self, payload: Dict[str, Any]) -> str:
        """Generate a narrative from the given payload."""
        pass
    
    @abstractmethod
    def generate_actions(self, payload: Dict[str, Any]) -> str:
        """Generate action recommendations from the given payload."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available (package installed + API key configured)."""
        pass


class RuleBasedProvider(AIProvider):
    """Deterministic rule-based provider used as fallback when AI is unavailable."""
    
    def is_available(self) -> bool:
        """Rule-based provider is always available."""
        return True
    
    def generate_narrative(self, payload: Dict[str, Any]) -> str:
        """
        Generate a deterministic rule-based narrative.
        Uses simple logic based on the provided metrics.
        """
        mode = payload.get("mode", "YoY")
        cp_total = payload.get("cp_total_inr", "₹0")
        growth_pct = payload.get("growth_pct", 0)
        best_loc = payload.get("best_loc", "—")
        best_growth = payload.get("best_growth_pct", 0)
        worst_loc = payload.get("worst_loc", "—")
        worst_growth = payload.get("worst_growth_pct", 0)
        best_driver = payload.get("best_driver", "volume")
        worst_driver = payload.get("worst_driver", "volume")
        n_growing = payload.get("n_growing", 0)
        n_total = payload.get("n_total", 0)
        neg_count = payload.get("neg_count", 0)
        top_svc_driver = payload.get("top_svc_driver", "—")
        abs_growth = payload.get("abs_growth_inr", "₹0")

        # Build narrative based on growth and health
        if growth_pct >= 0:
            sentence1 = f"Labour revenue of {cp_total} grew by {growth_pct:.1f}% {mode}, led by {best_loc} at {best_growth:.1f}% growth."
        else:
            sentence1 = f"Labour revenue of {cp_total} declined by {abs(growth_pct):.1f}% {mode}, with {best_loc} as the top performer at {best_growth:.1f}%."

        # Second sentence based on worst performer and health
        if worst_growth < 0:
            action = "review" if neg_count > 0 else "monitor"
            sentence2 = f"Primary driver is {best_driver}, while {worst_loc} declined {abs(worst_growth):.1f}% driven by {worst_driver}. {n_growing}/{n_total} locations growing. {action.capitalize()} {worst_loc} operations."
        else:
            sentence2 = f"Primary driver is {best_driver}, with all locations performing positively. {n_growing}/{n_total} locations growing. Sustain current momentum."

        return f"{sentence1} {sentence2}"
    
    def generate_actions(self, payload: Dict[str, Any]) -> str:
        """
        Generate deterministic rule-based action recommendations.
        """
        worst_loc = payload.get("worst_loc", "—")
        worst_growth = payload.get("worst_growth_pct", 0)
        worst_driver = payload.get("worst_driver", "volume")
        best_loc = payload.get("best_loc", "—")
        best_growth = payload.get("best_growth_pct", 0)
        neg_count = payload.get("neg_count", 0)
        neg_locations = payload.get("neg_locations", [])
        top_svc_driver = payload.get("top_svc_driver", "—")
        rpc_growth = payload.get("rpc_growth", 0)
        declining_locs = payload.get("declining_locs", [])

        # Build opportunities
        opps = []
        if declining_locs:
            for loc_data in declining_locs[:3]:
                loc = loc_data.get("location", "—")
                gap = loc_data.get("gap_inr", "₹0")
                opps.append(f"O1: Recover {gap} revenue potential at {loc} by improving service mix and efficiency.")
        else:
            opps.append("O1: Expand PMP and BR attach rates across all locations to increase revenue per jobcard.")
            opps.append("O2: Cross-sell high-margin services from top-performing locations to underperforming ones.")
            opps.append("O3: Implement customer retention programs to drive repeat business and steady revenue.")

        # Build actions
        acts = []
        if worst_growth < 0:
            acts.append(f"A1: Review {worst_loc} operations and {worst_driver} performance to address {abs(worst_growth):.1f}% decline.")
        if neg_count > 0:
            neg_locs_str = ", ".join(neg_locations[:2]) if neg_locations else "affected locations"
            acts.append(f"A2: Audit negative labour advisors at {neg_locs_str} and review discount policies immediately.")
        if rpc_growth < 0:
            acts.append(f"A3: Push {top_svc_driver} attach rates to improve revenue per jobcard which declined {abs(rpc_growth):.1f}%.")
        else:
            acts.append(f"A3: Scale {best_loc}'s best practices across network to replicate {best_growth:.1f}% growth success.")

        # Ensure we have exactly 3 of each
        while len(opps) < 3:
            opps.append(f"O{len(opps)+1}: Optimize operational efficiency to reduce costs and improve margins.")
        while len(acts) < 3:
            acts.append(f"A{len(acts)+1}: Conduct regular performance reviews and provide targeted training to advisors.")

        return "\n".join(opps[:3] + acts[:3])


class AnthropicProvider(AIProvider):
    """Anthropic Claude provider for AI-generated narratives and actions."""
    
    def __init__(self):
        self._available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if anthropic package is installed and API key is configured."""
        try:
            import anthropic
            return bool(os.environ.get("ANTHROPIC_API_KEY"))
        except ImportError:
            return False
    
    def is_available(self) -> bool:
        """Check if this provider is available."""
        return self._available
    
    def generate_narrative(self, payload: Dict[str, Any]) -> str:
        """Generate narrative using Anthropic Claude."""
        import anthropic
        client = anthropic.Anthropic()
        payload_json = json.dumps(payload, sort_keys=True)
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=120,
            system=(
                "You are a senior automotive dealership financial analyst writing for a Dealer Principal. "
                "Return exactly 2 sentences. No markdown. No bullet points. No preamble. "
                "Sentence 1: State what happened — include the exact ₹ total revenue, exact growth %, "
                "and name the top-performing location and its growth %. "
                "Sentence 2: State the primary service type driver, name the worst-performing location "
                "and its decline %, and give one specific action verb (e.g. review, escalate, audit, push). "
                "Use Indian number formatting (Cr for crores, L for lakhs)."
            ),
            messages=[{"role": "user", "content": payload_json}]
        )
        return msg.content[0].text
    
    def generate_actions(self, payload: Dict[str, Any]) -> str:
        """Generate action recommendations using Anthropic Claude."""
        import anthropic
        client = anthropic.Anthropic()
        payload_json = json.dumps(payload, sort_keys=True)
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            system=(
                "You are an automotive service operations consultant writing for a Dealer Principal. "
                "Return exactly 6 lines: lines 1-3 are Opportunities, lines 4-6 are Actions. "
                "Format: O1: ... O2: ... O3: ... A1: ... A2: ... A3: ... "
                "Each line is one sentence. "
                "Opportunities must quantify the revenue potential in ₹ (use Indian formatting). "
                "Actions must name the specific location or service type and include a specific action verb. "
                "No markdown, no bullet points, no preamble."
            ),
            messages=[{"role": "user", "content": payload_json}]
        )
        return msg.content[0].text


class GeminiProvider(AIProvider):
    """Google Gemini provider for AI-generated narratives and actions."""
    
    def __init__(self):
        self._available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if google-generativeai package is installed and API key is configured."""
        try:
            import google.generativeai as genai
            return bool(os.environ.get("GEMINI_API_KEY"))
        except ImportError:
            return False
    
    def is_available(self) -> bool:
        """Check if this provider is available."""
        return self._available
    
    def generate_narrative(self, payload: Dict[str, Any]) -> str:
        """Generate narrative using Google Gemini."""
        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-1.5-flash')
        payload_json = json.dumps(payload, sort_keys=True)
        prompt = (
            "You are a senior automotive dealership financial analyst writing for a Dealer Principal. "
            "Return exactly 2 sentences. No markdown. No bullet points. No preamble. "
            "Sentence 1: State what happened — include the exact ₹ total revenue, exact growth %, "
            "and name the top-performing location and its growth %. "
            "Sentence 2: State the primary service type driver, name the worst-performing location "
            "and its decline %, and give one specific action verb (e.g. review, escalate, audit, push). "
            "Use Indian number formatting (Cr for crores, L for lakhs).\n\n"
            f"Data: {payload_json}"
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    
    def generate_actions(self, payload: Dict[str, Any]) -> str:
        """Generate action recommendations using Google Gemini."""
        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-1.5-flash')
        payload_json = json.dumps(payload, sort_keys=True)
        prompt = (
            "You are an automotive service operations consultant writing for a Dealer Principal. "
            "Return exactly 6 lines: lines 1-3 are Opportunities, lines 4-6 are Actions. "
            "Format: O1: ... O2: ... O3: ... A1: ... A2: ... A3: ... "
            "Each line is one sentence. "
            "Opportunities must quantify the revenue potential in ₹ (use Indian formatting). "
            "Actions must name the specific location or service type and include a specific action verb. "
            "No markdown, no bullet points, no preamble.\n\n"
            f"Data: {payload_json}"
        )
        response = model.generate_content(prompt)
        return response.text.strip()


def _get_provider() -> AIProvider:
    """
    Get the appropriate AI provider based on availability.
    Priority: Gemini > Anthropic > RuleBased (fallback).
    """
    # Try Gemini first
    gemini = GeminiProvider()
    if gemini.is_available():
        return gemini
    
    # Try Anthropic second
    anthropic = AnthropicProvider()
    if anthropic.is_available():
        return anthropic
    
    # Fall back to rule-based
    return RuleBasedProvider()


# Initialize provider singleton
_provider: Optional[AIProvider] = None


def get_narrative(payload: Dict[str, Any]) -> str:
    """
    Get AI-generated or rule-based narrative for dashboard.
    
    Args:
        payload: Dictionary containing metrics for narrative generation
                 - mode: "YoY" or "MoM"
                 - cp_total_inr: Current period total revenue formatted
                 - growth_pct: Growth percentage
                 - best_loc: Best performing location
                 - best_growth_pct: Best location growth percentage
                 - best_driver: Service type driving best location
                 - worst_loc: Worst performing location
                 - worst_growth_pct: Worst location growth percentage
                 - worst_driver: Service type driving worst location
                 - n_growing: Number of growing locations
                 - n_total: Total number of locations
                 - neg_count: Number of negative labour alerts
                 - top_svc_driver: Top service type driver
                 - abs_growth_inr: Absolute growth formatted
    
    Returns:
        Narrative string (2 sentences)
    """
    global _provider
    if _provider is None:
        _provider = _get_provider()
    
    try:
        return _provider.generate_narrative(payload)
    except Exception:
        # Fallback to rule-based on any error
        rule_provider = RuleBasedProvider()
        return rule_provider.generate_narrative(payload)


def get_actions(payload: Dict[str, Any]) -> str:
    """
    Get AI-generated or rule-based action recommendations for dashboard.
    
    Args:
        payload: Dictionary containing metrics for action generation
                 - mode: "YoY" or "MoM"
                 - worst_loc: Worst performing location
                 - worst_growth_pct: Worst location growth percentage
                 - worst_driver: Service type driving worst location
                 - best_loc: Best performing location
                 - best_growth_pct: Best location growth percentage
                 - neg_count: Number of negative labour alerts
                 - neg_locations: List of locations with negative labour
                 - top_svc_driver: Top service type driver
                 - rpc_growth: Revenue per jobcard growth
                 - declining_locs: List of declining locations with gap data
    
    Returns:
        Actions string (6 lines: O1, O2, O3, A1, A2, A3)
    """
    global _provider
    if _provider is None:
        _provider = _get_provider()
    
    try:
        return _provider.generate_actions(payload)
    except Exception:
        # Fallback to rule-based on any error
        rule_provider = RuleBasedProvider()
        return rule_provider.generate_actions(payload)
