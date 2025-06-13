from app.agents.base_agent import ConversationalAgent
from app.core.logging import get_logger

logger = get_logger(__name__)

class Riley(ConversationalAgent):
    """Data Analysis Agent - Thoughtful contributor with metrics focus"""
    
    def __init__(self):
        super().__init__(
            name="Riley",
            personality={
                "description": "Data analyst focused on metrics we can automatically track and report",
                "expertise": "Automated analytics and performance monitoring",
                "traits": ["data-driven", "systematic", "alert-focused", "insight-oriented"],
                "communication_style": "Asks for data context, shares relevant insights, suggests metrics to track"
            },
            conversation_style="Focuses on trackable metrics and automated reporting",
            question_patterns=[
                "Which metrics matter most? (signups, revenue, traffic, social engagement, Product Hunt rank)",
                "How often do you want reports? (real-time, hourly, daily, weekly)",
                "What alert thresholds should we set up automatically?",
                "Do you want automated competitor benchmarking?",
                "Should we set up automated conversion funnel tracking?",
                "What baseline data do you have for automated comparison?",
                "Do you want automated anomaly detection alerts?",
                "Should we create automated performance dashboards?",
                "What automated insights do you want generated?",
                "Do you need automated ROI calculations?",
                "What metrics matter most to you?",
                "Do you have baseline data to compare against?",
                "What's your current user/traffic numbers?",
                "Any specific KPIs you're targeting?",
                "When do you want to measure results?",
                "Do you have analytics set up?",
                "What data do you currently track?",
                "Any previous campaign data to reference?",
                "What would success look like numerically?",
                "When should we check in on progress?",
                "Any seasonal trends we should consider?",
                "What's your conversion funnel like?"
            ]
        )
        
        logger.info("Riley (Data Analysis Agent) initialized")
    
    def should_contribute(self, conversation_context: dict) -> bool:
        """Determine if Riley should contribute to this conversation"""
        keywords = ["metrics", "data", "analytics", "track", "measure", "numbers", "performance", "results", "success", "kpi"]
        message = conversation_context.get("last_message", "").lower()
        return any(keyword in message for keyword in keywords)
    
    def get_analytics_insight(self, context: dict) -> str:
        """Generate analytics-focused input based on conversation context"""
        return """From a data perspective, I can help you track what matters most!

I can automatically monitor these metrics:
📈 Signups (with conversion tracking)
💰 Revenue (real-time or daily reports)
🌐 Traffic (source attribution and behavior)
❤️ Social Engagement (across all platforms)
🏆 Product Hunt Ranking (live updates)

What would success look like numerically for you? This helps me set up the right tracking and alerts."""
    
    def analyze_success_metrics(self, user_input: str) -> dict:
        """Analyze user input to identify mentioned metrics and goals"""
        metrics_found = {
            "signups": False,
            "revenue": False,
            "traffic": False,
            "engagement": False,
            "ranking": False,
            "conversion": False,
            "numeric_goals": []
        }
        
        input_lower = user_input.lower()
        
        # Check for specific metrics
        if any(word in input_lower for word in ["signup", "user", "registration", "account"]):
            metrics_found["signups"] = True
        if any(word in input_lower for word in ["revenue", "money", "sales", "income", "mrr", "arr"]):
            metrics_found["revenue"] = True
        if any(word in input_lower for word in ["traffic", "visitor", "pageview", "session"]):
            metrics_found["traffic"] = True
        if any(word in input_lower for word in ["engagement", "like", "share", "comment", "interaction"]):
            metrics_found["engagement"] = True
        if any(word in input_lower for word in ["rank", "position", "top", "featured"]):
            metrics_found["ranking"] = True
        if any(word in input_lower for word in ["conversion", "convert", "funnel"]):
            metrics_found["conversion"] = True
        
        # Extract numeric goals (simple regex)
        import re
        numbers = re.findall(r'\d+', user_input)
        metrics_found["numeric_goals"] = numbers
        
        return metrics_found
    
    def suggest_tracking_setup(self, metrics: dict) -> str:
        """Suggest tracking setup based on identified metrics"""
        suggestions = []
        
        if metrics["signups"]:
            suggestions.append("• Signup tracking with source attribution")
        if metrics["revenue"]:
            suggestions.append("• Revenue monitoring with real-time alerts")
        if metrics["traffic"]:
            suggestions.append("• Traffic analytics with conversion funnel")
        if metrics["engagement"]:
            suggestions.append("• Social engagement tracking across platforms")
        if metrics["ranking"]:
            suggestions.append("• Product Hunt ranking monitoring")
        
        if not suggestions:
            suggestions = [
                "• Basic engagement tracking (recommended starting point)",
                "• Signup conversion monitoring",
                "• Traffic source analysis"
            ]
        
        return "I recommend setting up:\n" + "\n".join(suggestions) 