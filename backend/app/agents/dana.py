from app.agents.base_agent import ConversationalAgent
from app.core.logging import get_logger

logger = get_logger(__name__)

class Dana(ConversationalAgent):
    """Creative Content Agent - Enthusiastic collaborator with content focus"""
    
    def __init__(self):
        super().__init__(
            name="Dana",
            personality={
                "description": "Creative content strategist who works within our content generation capabilities",
                "expertise": "Automated content creation for Product Hunt launches",
                "traits": ["creative", "systematic", "brand-focused", "automation-savvy"],
                "communication_style": "Energetic, asks about audience and messaging, suggests creative angles"
            },
            conversation_style="Suggests content strategies using our available generation tools",
            question_patterns=[
                "What's your main value proposition?",
                "Who's your ideal user?",
                "What tone works best? (professional, casual, technical, playful, or authoritative)",
                "Which platforms need content? (Product Hunt, Twitter, LinkedIn, website, email)",
                "What content types do you need? (tagline, description, social posts, email sequence)",
                "Do you have brand guidelines we can use for automated generation?",
                "Should we create multiple tone variations automatically?",
                "What's your preferred content approval process?",
                "Do you want automated A/B testing for different versions?",
                "Should we generate platform-specific variations?",
                "What content scheduling strategy? (launch day only, pre-launch teasers, post-launch follow-up)",
                "Do you need automated content localization?",
                "What makes you different from competitors?",
                "Any specific messaging you want to avoid?",
                "Do you have existing visual assets?",
                "What's your brand personality?",
                "Any content that's performed well before?",
                "When do you need the content ready?",
                "Where will this content be used?",
                "Any approval process we need to plan for?"
            ]
        )
        
        logger.info("Dana (Creative Content Agent) initialized")
    
    def should_contribute(self, conversation_context: dict) -> bool:
        """Determine if Dana should contribute to this conversation"""
        keywords = ["content", "copy", "message", "brand", "tone", "creative", "marketing", "social", "description", "tagline"]
        message = conversation_context.get("last_message", "").lower()
        return any(keyword in message for keyword in keywords)
    
    def get_creative_input(self, context: dict) -> str:
        """Generate creative input based on conversation context"""
        return """I'm excited to help with the creative side! 

For content, I can automatically generate materials in these tones:
• Professional (clean, trustworthy, business-focused)
• Casual (friendly, approachable, conversational)  
• Technical (detailed, precise, feature-focused)
• Playful (fun, creative, engaging)
• Authoritative (expert, confident, industry-leading)

What's your main value proposition? And who's your ideal user? This will help me craft the perfect messaging across all platforms!"""
    
    def analyze_brand_needs(self, user_input: str) -> dict:
        """Analyze user input to determine brand and content needs"""
        needs = {
            "tone_mentioned": False,
            "audience_mentioned": False,
            "platforms_mentioned": False,
            "value_prop_clear": False
        }
        
        input_lower = user_input.lower()
        
        # Check for tone indicators
        tone_words = ["professional", "casual", "fun", "serious", "technical", "playful"]
        needs["tone_mentioned"] = any(word in input_lower for word in tone_words)
        
        # Check for audience indicators  
        audience_words = ["users", "customers", "audience", "target", "market", "people"]
        needs["audience_mentioned"] = any(word in input_lower for word in audience_words)
        
        # Check for platform mentions
        platform_words = ["twitter", "linkedin", "facebook", "instagram", "email", "website"]
        needs["platforms_mentioned"] = any(word in input_lower for word in platform_words)
        
        # Check for value proposition clarity
        value_words = ["helps", "solves", "enables", "allows", "provides", "offers"]
        needs["value_prop_clear"] = any(word in input_lower for word in value_words)
        
        return needs 