from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

from app.services.base_integration import BaseIntegration, IntegrationStatus
from app.models.api_keys import SupportedService
from app.core.logging import get_logger

logger = get_logger(__name__)

class GoogleCalendarIntegration(BaseIntegration):
    """Google Calendar API integration for event management, scheduling, and calendar automation"""
    
    def __init__(self):
        super().__init__(SupportedService.GOOGLE_CALENDAR)
    
    @property
    def base_url(self) -> str:
        return "https://www.googleapis.com/calendar/v3"
    
    @property
    def required_scopes(self) -> List[str]:
        return [
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/calendar.events",
            "https://www.googleapis.com/auth/calendar.readonly"
        ]
    
    async def _prepare_auth_headers(self, api_key: str) -> Dict[str, str]:
        """Prepare Google Calendar API headers"""
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def _test_api_connection(self, api_key: str) -> Dict[str, Any]:
        """Test Google Calendar API connection by getting calendar list"""
        try:
            result = await self.make_api_request(
                method="GET",
                endpoint="users/me/calendarList",
                api_key=api_key,
                params={"maxResults": 1}
            )
            
            if result.get("success"):
                calendar_data = result.get("data", {})
                if "items" in calendar_data:
                    return {
                        "connected": True,
                        "status": "success",
                        "message": "Successfully connected to Google Calendar"
                    }
                else:
                    return {
                        "connected": False,
                        "status": "error",
                        "message": "No calendar access or invalid response"
                    }
            else:
                return {
                    "connected": False,
                    "status": "error",
                    "message": result.get("message", "Failed to connect to Google Calendar")
                }
                
        except Exception as e:
            logger.error(f"Google Calendar connection test failed: {str(e)}")
            return {
                "connected": False,
                "status": "error", 
                "message": str(e)
            }
    
    # Core Google Calendar Operations
    
    async def get_calendars(self, session_id: str) -> Dict[str, Any]:
        """Get all calendars accessible to the user"""
        api_key = await self.get_api_key(session_id)
        if not api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            result = await self.make_api_request(
                method="GET",
                endpoint="users/me/calendarList",
                api_key=api_key
            )
            
            if result.get("success"):
                calendar_data = result.get("data", {})
                calendars = []
                
                for cal in calendar_data.get("items", []):
                    calendars.append({
                        "id": cal.get("id"),
                        "summary": cal.get("summary", "Untitled"),
                        "description": cal.get("description", ""),
                        "primary": cal.get("primary", False),
                        "access_role": cal.get("accessRole", "reader"),
                        "color_id": cal.get("colorId", "1"),
                        "time_zone": cal.get("timeZone", "UTC")
                    })
                
                return {
                    "success": True,
                    "calendars": calendars,
                    "count": len(calendars)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error getting Google calendars: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_events(
        self, 
        session_id: str, 
        calendar_id: str = "primary",
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 50
    ) -> Dict[str, Any]:
        """Get events from a calendar"""
        api_key = await self.get_api_key(session_id)
        if not api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            params = {
                "maxResults": max_results,
                "singleEvents": True,
                "orderBy": "startTime"
            }
            
            if time_min:
                params["timeMin"] = time_min.isoformat() + "Z"
            else:
                params["timeMin"] = datetime.utcnow().isoformat() + "Z"
            
            if time_max:
                params["timeMax"] = time_max.isoformat() + "Z"
            
            result = await self.make_api_request(
                method="GET",
                endpoint=f"calendars/{calendar_id}/events",
                api_key=api_key,
                params=params
            )
            
            if result.get("success"):
                events_data = result.get("data", {})
                events = []
                
                for event in events_data.get("items", []):
                    # Parse start and end times
                    start = event.get("start", {})
                    end = event.get("end", {})
                    
                    events.append({
                        "id": event.get("id"),
                        "summary": event.get("summary", "No Title"),
                        "description": event.get("description", ""),
                        "location": event.get("location", ""),
                        "start": {
                            "dateTime": start.get("dateTime"),
                            "date": start.get("date"),
                            "timeZone": start.get("timeZone")
                        },
                        "end": {
                            "dateTime": end.get("dateTime"),
                            "date": end.get("date"),
                            "timeZone": end.get("timeZone")
                        },
                        "attendees": [
                            {
                                "email": attendee.get("email"),
                                "displayName": attendee.get("displayName", ""),
                                "responseStatus": attendee.get("responseStatus", "needsAction")
                            }
                            for attendee in event.get("attendees", [])
                        ],
                        "created": event.get("created"),
                        "updated": event.get("updated"),
                        "html_link": event.get("htmlLink")
                    })
                
                return {
                    "success": True,
                    "events": events,
                    "count": len(events)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error getting Google Calendar events: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def create_event(
        self, 
        session_id: str, 
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        calendar_id: str = "primary"
    ) -> Dict[str, Any]:
        """Create a new calendar event"""
        api_key = await self.get_api_key(session_id)
        if not api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            event_data = {
                "summary": title,
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": "UTC"
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": "UTC"
                }
            }
            
            if description:
                event_data["description"] = description
            
            if location:
                event_data["location"] = location
            
            if attendees:
                event_data["attendees"] = [{"email": email} for email in attendees]
            
            result = await self.make_api_request(
                method="POST",
                endpoint=f"calendars/{calendar_id}/events",
                api_key=api_key,
                data=event_data
            )
            
            if result.get("success"):
                event = result.get("data", {})
                return {
                    "success": True,
                    "event": {
                        "id": event.get("id"),
                        "summary": event.get("summary"),
                        "html_link": event.get("htmlLink"),
                        "created": event.get("created")
                    }
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error creating Google Calendar event: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def update_event(
        self, 
        session_id: str, 
        event_id: str,
        calendar_id: str = "primary",
        title: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        time_zone: str = "UTC"
    ) -> Dict[str, Any]:
        """Update an existing calendar event"""
        api_key = await self.get_api_key(session_id)
        if not api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            # First get the existing event
            existing_result = await self.make_api_request(
                method="GET",
                endpoint=f"calendars/{calendar_id}/events/{event_id}",
                api_key=api_key
            )
            
            if not existing_result.get("success"):
                return existing_result
            
            existing_event = existing_result.get("data", {})
            
            # Update only provided fields
            if title:
                existing_event["summary"] = title
            
            if start_time:
                existing_event["start"] = {
                    "dateTime": start_time.isoformat(),
                    "timeZone": time_zone
                }
            
            if end_time:
                existing_event["end"] = {
                    "dateTime": end_time.isoformat(),
                    "timeZone": time_zone
                }
            
            if description is not None:
                existing_event["description"] = description
            
            if location is not None:
                existing_event["location"] = location
            
            if attendees is not None:
                existing_event["attendees"] = [{"email": email} for email in attendees]
            
            result = await self.make_api_request(
                method="PUT",
                endpoint=f"calendars/{calendar_id}/events/{event_id}",
                api_key=api_key,
                data=existing_event
            )
            
            if result.get("success"):
                event = result.get("data", {})
                return {
                    "success": True,
                    "event": {
                        "id": event.get("id"),
                        "summary": event.get("summary"),
                        "start": event.get("start"),
                        "end": event.get("end"),
                        "html_link": event.get("htmlLink"),
                        "updated": event.get("updated")
                    }
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error updating Google Calendar event: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def delete_event(
        self, 
        session_id: str, 
        event_id: str,
        calendar_id: str = "primary"
    ) -> Dict[str, Any]:
        """Delete a calendar event"""
        api_key = await self.get_api_key(session_id)
        if not api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            result = await self.make_api_request(
                method="DELETE",
                endpoint=f"calendars/{calendar_id}/events/{event_id}",
                api_key=api_key
            )
            
            if result.get("success") or result.get("status_code") == 204:
                return {
                    "success": True,
                    "message": "Event deleted successfully"
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error deleting Google Calendar event: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def find_free_time(
        self, 
        session_id: str, 
        duration_minutes: int,
        start_date: datetime,
        end_date: datetime,
        calendar_ids: Optional[List[str]] = None,
        working_hours_start: int = 9,  # 9 AM
        working_hours_end: int = 17    # 5 PM
    ) -> Dict[str, Any]:
        """Find free time slots for scheduling"""
        api_key = await self.get_api_key(session_id)
        if not api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            if not calendar_ids:
                calendar_ids = ["primary"]
            
            # Get busy times for all calendars
            busy_times = []
            
            for calendar_id in calendar_ids:
                events_result = await self.get_events(
                    session_id=session_id,
                    calendar_id=calendar_id,
                    time_min=start_date,
                    time_max=end_date
                )
                
                if events_result.get("success"):
                    for event in events_result.get("events", []):
                        start = event.get("start", {})
                        end = event.get("end", {})
                        
                        if start.get("dateTime") and end.get("dateTime"):
                            busy_times.append({
                                "start": datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00")),
                                "end": datetime.fromisoformat(end["dateTime"].replace("Z", "+00:00"))
                            })
            
            # Find free slots
            free_slots = []
            current_time = start_date
            
            while current_time < end_date:
                # Check if within working hours
                if working_hours_start <= current_time.hour < working_hours_end:
                    slot_end = current_time + timedelta(minutes=duration_minutes)
                    
                    # Check if slot conflicts with any busy time
                    is_free = True
                    for busy in busy_times:
                        if (current_time < busy["end"] and slot_end > busy["start"]):
                            is_free = False
                            break
                    
                    if is_free and slot_end.hour <= working_hours_end:
                        free_slots.append({
                            "start": current_time.isoformat(),
                            "end": slot_end.isoformat(),
                            "duration_minutes": duration_minutes
                        })
                
                # Move to next 30-minute slot
                current_time += timedelta(minutes=30)
            
            return {
                "success": True,
                "free_slots": free_slots[:20],  # Limit to 20 slots
                "count": len(free_slots),
                "duration_minutes": duration_minutes
            }
            
        except Exception as e:
            logger.error(f"Error finding free time: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # Trigger.dev Workflow Integration
    
    async def _create_service_workflow(
        self, 
        workflow_payload: Dict[str, Any], 
        api_key: str
    ) -> Dict[str, Any]:
        """Create Google Calendar-specific Trigger.dev workflows"""
        
        workflow_name = workflow_payload.get("name")
        config = workflow_payload.get("config", {})
        
        # Define available Google Calendar workflows
        calendar_workflows = {
            "meeting_scheduler": {
                "description": "Automatically schedule meetings and send invites",
                "triggers": ["meeting_requested", "manual", "time_based"],
                "actions": ["create_event", "find_free_time", "send_invites"]
            },
            "deadline_tracker": {
                "description": "Track project deadlines and create calendar reminders",
                "triggers": ["deadline_set", "reminder_time"],
                "actions": ["create_event", "update_event", "send_notification"]
            }
        }
        
        workflow_type = config.get("workflow_type", "meeting_scheduler")
        
        if workflow_type not in calendar_workflows:
            return {
                "success": False,
                "error": "invalid_workflow_type",
                "available_workflows": list(calendar_workflows.keys())
            }
        
        # Create workflow configuration
        workflow_config = {
            "name": workflow_name,
            "service": "google_calendar",
            "type": workflow_type,
            "config": calendar_workflows[workflow_type],
            "user_config": config,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "workflow": workflow_config,
            "message": f"Google Calendar workflow '{workflow_name}' created successfully"
        }
    
    # Helper Methods
    
    def parse_datetime_string(self, datetime_str: str, time_zone: str = "UTC") -> datetime:
        """Parse datetime string with timezone support"""
        try:
            if "T" in datetime_str:
                # ISO format
                return datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
            else:
                # Date only
                return datetime.strptime(datetime_str, "%Y-%m-%d")
        except Exception as e:
            logger.error(f"Error parsing datetime: {str(e)}")
            return datetime.utcnow()
    
    def format_event_for_display(self, event: Dict[str, Any]) -> str:
        """Format event data for human-readable display"""
        title = event.get("summary", "No Title")
        start = event.get("start", {})
        location = event.get("location", "")
        
        start_time = "Unknown time"
        if start.get("dateTime"):
            dt = self.parse_datetime_string(start["dateTime"])
            start_time = dt.strftime("%Y-%m-%d %H:%M")
        elif start.get("date"):
            start_time = start["date"]
        
        result = f"📅 {title}\n⏰ {start_time}"
        if location:
            result += f"\n📍 {location}"
        
        return result

# Global instance
google_calendar_integration = GoogleCalendarIntegration() 