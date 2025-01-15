"""
Schema definitions for content extraction and analysis.
"""

MARKET_RESEARCH_SCHEMA = {
    "properties": {
        "market_size": {"type": "string"},
        "growth_rate": {"type": "string"},
        "key_players": {"type": "array", "items": {"type": "string"}},
        "trends": {"type": "array", "items": {"type": "string"}},
        "challenges": {"type": "array", "items": {"type": "string"}},
        "opportunities": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["market_size", "growth_rate", "key_players", "trends"]
} 