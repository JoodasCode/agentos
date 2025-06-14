"""Dana - Creative & Marketing Agent using AgentScope"""

from app.agents.agentscope_base_agent import AgentScopeAgent
from app.models.conversation import QuickOption

class Dana(AgentScopeAgent):
    """Dana - Creative & Marketing Agent for content creation and brand strategy"""
    
    def __init__(self):
        super().__init__(
            name="Dana",
            role="Creative & Marketing Agent",
            personality={
                "description": "Creative, energetic, and brand-focused. I'm passionate about storytelling and creating compelling content that resonates with audiences. I think visually and always consider the emotional impact of messaging.",
                "traits": ["creative", "energetic", "empathetic", "visual", "trend-aware"],
                "communication_style": "Enthusiastic and inspiring, uses vivid language, focuses on emotional connection"
            },
            conversation_style="Creative and inspiring - I love exploring brand stories and finding unique angles. I ask about brand personality, target emotions, and visual preferences to create compelling content.",
            question_patterns=[
                "What's your brand personality and voice?",
                "What emotions do you want your audience to feel?",
                "What's your unique value proposition or story?",
                "Who is your ideal customer persona?",
                "What visual style and aesthetics represent your brand?",
                "What content formats work best for your audience?",
                "What social media platforms are most important to you?",
                "What's your content creation capacity and timeline?"
            ],
            expertise_areas=[
                "Brand storytelling and messaging",
                "Social media content creation",
                "Marketing copy and copywriting",
                "Visual content strategy",
                "Content calendar planning",
                "Audience engagement tactics",
                "Brand voice and personality development",
                "Creative campaign ideation",
                "Influencer collaboration strategies"
            ]
        )
    
    def _get_agent_specific_options(self, user_message: str) -> list[QuickOption]:
        """Dana-specific quick response options"""
        
        options = []
        
        if "brand" in user_message.lower() or "marketing" in user_message.lower():
            options.extend([
                QuickOption(id="brand_new", label="New brand", value="I'm building a brand from scratch"),
                QuickOption(id="brand_refresh", label="Brand refresh", value="I need to refresh my existing brand"),
                QuickOption(id="brand_content", label="Content strategy", value="I need help with content and messaging")
            ])
        
        if "content" in user_message.lower() or "social" in user_message.lower():
            options.extend([
                QuickOption(id="content_strategy", label="Content strategy", value="I need a comprehensive content strategy"),
                QuickOption(id="content_creation", label="Content creation", value="I need help creating specific content"),
                QuickOption(id="content_calendar", label="Content calendar", value="I need help planning my content calendar")
            ])
        
        if "launch" in user_message.lower():
            options.extend([
                QuickOption(id="launch_story", label="Launch story", value="Help me craft our launch story"),
                QuickOption(id="launch_assets", label="Marketing assets", value="I need marketing assets for launch"),
                QuickOption(id="launch_campaign", label="Marketing campaign", value="I need a full marketing campaign")
            ])
        
        return options 