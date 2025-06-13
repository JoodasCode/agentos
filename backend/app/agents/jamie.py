from app.agents.base_agent import ConversationalAgent
from app.core.logging import get_logger

logger = get_logger(__name__)

class Jamie(ConversationalAgent):
    """Operations Agent - Practical organizer with scheduling focus"""
    
    def __init__(self):
        super().__init__(
            name="Jamie",
            personality={
                "description": "Operations coordinator who sets up automated workflows and scheduling",
                "expertise": "Trigger.dev job scheduling and workflow automation",
                "traits": ["systematic", "automation-focused", "reliable", "workflow-oriented"],
                "communication_style": "Focuses on feasibility, timelines, and resource requirements"
            },
            conversation_style="Focuses on automated scheduling and workflow setup",
            question_patterns=[
                "When should automated reminders fire? (1 day before, 1 hour before, at launch, 1 day after)",
                "What's your preferred notification method for automated alerts?",
                "Should we set up automated backup schedules?",
                "What automated escalation rules do you want?",
                "Do you need automated status updates sent to your team?",
                "Should we create automated rollback procedures?",
                "What automated health checks do you want running?",
                "Do you want automated progress reports?",
                "Should we set up automated dependency monitoring?",
                "What automated approval workflows do you need?",
                "When do you need this completed?",
                "What's your availability like?",
                "Any vacation/busy periods coming up?",
                "Who else needs to be involved?",
                "When should we send reminders?",
                "How often do you want progress updates?",
                "What time zone are you in?",
                "Best way to reach you for urgent items?",
                "Any approval processes we need to factor in?",
                "When should we schedule check-ins?",
                "What's your preferred communication method?",
                "Any dependencies on other projects?",
                "When should we start each phase?",
                "How much lead time do you need for reviews?"
            ]
        )
        
        logger.info("Jamie (Operations Agent) initialized")
    
    def should_contribute(self, conversation_context: dict) -> bool:
        """Determine if Jamie should contribute to this conversation"""
        keywords = ["schedule", "timeline", "workflow", "process", "automation", "reminder", "notification", "availability", "deadline"]
        message = conversation_context.get("last_message", "").lower()
        return any(keyword in message for keyword in keywords)
    
    def get_operational_input(self, context: dict) -> str:
        """Generate operations-focused input based on conversation context"""
        return """From an operations standpoint, I'll make sure everything runs smoothly!

I can set up automated workflows for:
⏰ Reminders (1 day before, 1 hour before, at launch, 1 day after)
📊 Progress reports (daily, weekly, or milestone-based)
🔔 Alert notifications (email, Slack, or SMS)
🔄 Backup and rollback procedures
🚨 Health monitoring and escalation rules

What's your availability like? And when do you prefer to receive updates? This helps me schedule everything perfectly."""
    
    def analyze_scheduling_needs(self, user_input: str) -> dict:
        """Analyze user input to identify scheduling and workflow needs"""
        needs = {
            "timeline_mentioned": False,
            "availability_mentioned": False,
            "communication_prefs": False,
            "team_involvement": False,
            "approval_process": False,
            "urgency_level": "medium"
        }
        
        input_lower = user_input.lower()
        
        # Check for timeline indicators
        timeline_words = ["asap", "urgent", "deadline", "by", "before", "after", "schedule"]
        needs["timeline_mentioned"] = any(word in input_lower for word in timeline_words)
        
        # Check for availability mentions
        availability_words = ["available", "busy", "free", "time", "hours", "weekend", "vacation"]
        needs["availability_mentioned"] = any(word in input_lower for word in availability_words)
        
        # Check for communication preferences
        comm_words = ["email", "slack", "text", "call", "notification", "update", "report"]
        needs["communication_prefs"] = any(word in input_lower for word in comm_words)
        
        # Check for team involvement
        team_words = ["team", "colleague", "manager", "approval", "review", "stakeholder"]
        needs["team_involvement"] = any(word in input_lower for word in team_words)
        
        # Check for approval processes
        approval_words = ["approve", "review", "sign-off", "permission", "authorization"]
        needs["approval_process"] = any(word in input_lower for word in approval_words)
        
        # Determine urgency
        if any(word in input_lower for word in ["asap", "urgent", "immediately", "rush"]):
            needs["urgency_level"] = "high"
        elif any(word in input_lower for word in ["flexible", "whenever", "no rush"]):
            needs["urgency_level"] = "low"
        
        return needs
    
    def suggest_workflow_setup(self, needs: dict) -> str:
        """Suggest workflow setup based on identified needs"""
        suggestions = []
        
        if needs["timeline_mentioned"]:
            suggestions.append("• Automated deadline tracking with milestone alerts")
        if needs["availability_mentioned"]:
            suggestions.append("• Smart scheduling around your availability")
        if needs["communication_prefs"]:
            suggestions.append("• Customized notification preferences")
        if needs["team_involvement"]:
            suggestions.append("• Team collaboration workflows with role assignments")
        if needs["approval_process"]:
            suggestions.append("• Automated approval chains with escalation")
        
        # Add urgency-based suggestions
        if needs["urgency_level"] == "high":
            suggestions.append("• Real-time monitoring with immediate alerts")
        elif needs["urgency_level"] == "low":
            suggestions.append("• Weekly progress summaries with flexible deadlines")
        else:
            suggestions.append("• Daily check-ins with standard escalation")
        
        if not suggestions:
            suggestions = [
                "• Basic project timeline with key milestones",
                "• Standard reminder schedule (1 day before key dates)",
                "• Weekly progress reports"
            ]
        
        return "I'll set up:\n" + "\n".join(suggestions)
    
    def create_timeline_estimate(self, project_scope: str) -> dict:
        """Create a rough timeline estimate based on project scope"""
        # Simple heuristic-based estimation
        scope_lower = project_scope.lower()
        
        base_timeline = {
            "planning": "2-3 days",
            "content_creation": "3-5 days", 
            "setup_automation": "1-2 days",
            "testing": "1-2 days",
            "launch": "1 day",
            "follow_up": "3-7 days"
        }
        
        # Adjust based on scope indicators
        if any(word in scope_lower for word in ["simple", "basic", "quick"]):
            multiplier = 0.7
        elif any(word in scope_lower for word in ["complex", "comprehensive", "full"]):
            multiplier = 1.5
        else:
            multiplier = 1.0
        
        # Apply multiplier (simplified)
        if multiplier != 1.0:
            for phase in base_timeline:
                if "day" in base_timeline[phase]:
                    # Extract number and adjust
                    import re
                    numbers = re.findall(r'\d+', base_timeline[phase])
                    if numbers:
                        min_days = int(int(numbers[0]) * multiplier)
                        max_days = int(int(numbers[-1]) * multiplier) if len(numbers) > 1 else min_days
                        base_timeline[phase] = f"{min_days}-{max_days} days" if min_days != max_days else f"{min_days} days"
        
        return base_timeline 