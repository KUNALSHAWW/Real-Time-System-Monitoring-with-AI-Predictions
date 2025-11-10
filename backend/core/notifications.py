"""
Notification Service for Multi-Channel Alerts
Supports Email, Slack, PagerDuty, and In-App notifications
"""

import smtplib
import requests
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, EmailStr
from enum import Enum

# ============================================================================
# NOTIFICATION MODELS
# ============================================================================

class NotificationChannel(str, Enum):
    """Available notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    IN_APP = "in_app"
    SMS = "sms"

class NotificationSeverity(str, Enum):
    """Notification severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class Notification(BaseModel):
    """Notification model"""
    title: str
    message: str
    severity: NotificationSeverity = NotificationSeverity.INFO
    channels: List[NotificationChannel]
    recipients: Optional[List[str]] = []
    metadata: Optional[Dict] = {}

# ============================================================================
# EMAIL SERVICE
# ============================================================================

class EmailService:
    """SMTP Email notification service"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        suggested_fixes: Optional[List[str]] = None
    ) -> bool:
        """
        Send email notification
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)
            suggested_fixes: List of suggested fixes for anomalies
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.username
            msg['To'] = to_email
            msg['Date'] = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
            
            # Add suggested fixes to body if provided
            if suggested_fixes:
                body += "\n\n🔧 Suggested Fixes:\n"
                for i, fix in enumerate(suggested_fixes, 1):
                    body += f"{i}. {fix}\n"
            
            # Attach plain text
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach HTML if provided
            if html_body:
                if suggested_fixes:
                    html_body += "<h3>🔧 Suggested Fixes:</h3><ol>"
                    for fix in suggested_fixes:
                        html_body += f"<li>{fix}</li>"
                    html_body += "</ol>"
                
                msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Email send error: {e}")
            return False

# ============================================================================
# SLACK SERVICE
# ============================================================================

class SlackService:
    """Slack webhook notification service"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send_notification(
        self,
        message: str,
        severity: NotificationSeverity = NotificationSeverity.INFO
    ) -> bool:
        """
        Send notification to Slack channel
        
        Args:
            message: Message text
            severity: Severity level for color coding
        """
        try:
            # Color coding by severity
            colors = {
                NotificationSeverity.INFO: "#36a64f",      # Green
                NotificationSeverity.WARNING: "#ff9900",   # Orange
                NotificationSeverity.ERROR: "#ff0000",     # Red
                NotificationSeverity.CRITICAL: "#8b0000"   # Dark Red
            }
            
            # Emoji by severity
            emojis = {
                NotificationSeverity.INFO: ":information_source:",
                NotificationSeverity.WARNING: ":warning:",
                NotificationSeverity.ERROR: ":x:",
                NotificationSeverity.CRITICAL: ":rotating_light:"
            }
            
            payload = {
                "username": "System Monitor Bot",
                "icon_emoji": ":chart_with_upwards_trend:",
                "attachments": [
                    {
                        "color": colors.get(severity, "#808080"),
                        "text": f"{emojis.get(severity, ':bell:')} {message}",
                        "footer": "System Monitoring Dashboard",
                        "ts": int(datetime.utcnow().timestamp())
                    }
                ]
            }
            
            response = requests.post(self.webhook_url, json=payload)
            return response.status_code == 200
            
        except Exception as e:
            print(f"Slack notification error: {e}")
            return False

# ============================================================================
# PAGERDUTY SERVICE
# ============================================================================

class PagerDutyService:
    """PagerDuty incident management service"""
    
    def __init__(self, api_key: str, service_key: str):
        self.api_key = api_key
        self.service_key = service_key
        self.events_url = "https://events.pagerduty.com/v2/enqueue"
    
    async def trigger_incident(
        self,
        summary: str,
        severity: NotificationSeverity = NotificationSeverity.INFO,
        source: str = "system-monitor",
        custom_details: Optional[Dict] = None
    ) -> bool:
        """
        Trigger PagerDuty incident
        
        Args:
            summary: Incident summary
            severity: Severity level
            source: Source identifier
            custom_details: Additional details
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Token token={self.api_key}"
            }
            
            # Map severity to PagerDuty levels
            pd_severity_map = {
                NotificationSeverity.INFO: "info",
                NotificationSeverity.WARNING: "warning",
                NotificationSeverity.ERROR: "error",
                NotificationSeverity.CRITICAL: "critical"
            }
            
            payload = {
                "routing_key": self.service_key,
                "event_action": "trigger",
                "payload": {
                    "summary": summary,
                    "severity": pd_severity_map.get(severity, "info"),
                    "source": source,
                    "timestamp": datetime.utcnow().isoformat(),
                    "custom_details": custom_details or {}
                }
            }
            
            response = requests.post(self.events_url, json=payload, headers=headers)
            return response.status_code == 202
            
        except Exception as e:
            print(f"PagerDuty incident error: {e}")
            return False
    
    async def resolve_incident(self, dedup_key: str) -> bool:
        """Resolve PagerDuty incident"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Token token={self.api_key}"
            }
            
            payload = {
                "routing_key": self.service_key,
                "event_action": "resolve",
                "dedup_key": dedup_key
            }
            
            response = requests.post(self.events_url, json=payload, headers=headers)
            return response.status_code == 202
            
        except Exception as e:
            print(f"PagerDuty resolve error: {e}")
            return False

# ============================================================================
# NOTIFICATION MANAGER
# ============================================================================

class NotificationManager:
    """Central notification manager for all channels"""
    
    def __init__(
        self,
        email_service: Optional[EmailService] = None,
        slack_service: Optional[SlackService] = None,
        pagerduty_service: Optional[PagerDutyService] = None
    ):
        self.email_service = email_service
        self.slack_service = slack_service
        self.pagerduty_service = pagerduty_service
    
    async def send_notification(self, notification: Notification) -> Dict[str, bool]:
        """
        Send notification through specified channels
        
        Returns:
            Dict mapping channel names to success status
        """
        results = {}
        
        # Send to each requested channel
        for channel in notification.channels:
            if channel == NotificationChannel.EMAIL and self.email_service:
                for recipient in notification.recipients:
                    success = await self.email_service.send_email(
                        to_email=recipient,
                        subject=notification.title,
                        body=notification.message,
                        html_body=self._create_html_body(notification),
                        suggested_fixes=notification.metadata.get('suggested_fixes', [])
                    )
                    results[f"{channel}:{recipient}"] = success
            
            elif channel == NotificationChannel.SLACK and self.slack_service:
                success = await self.slack_service.send_notification(
                    message=f"*{notification.title}*\n{notification.message}",
                    severity=notification.severity
                )
                results[channel] = success
            
            elif channel == NotificationChannel.PAGERDUTY and self.pagerduty_service:
                success = await self.pagerduty_service.trigger_incident(
                    summary=notification.title,
                    severity=notification.severity,
                    custom_details=notification.metadata
                )
                results[channel] = success
        
        return results
    
    def _create_html_body(self, notification: Notification) -> str:
        """Create HTML email body"""
        severity_colors = {
            NotificationSeverity.INFO: "#2196F3",
            NotificationSeverity.WARNING: "#FF9800",
            NotificationSeverity.ERROR: "#F44336",
            NotificationSeverity.CRITICAL: "#B71C1C"
        }
        
        color = severity_colors.get(notification.severity, "#757575")
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="background-color: {color}; color: white; padding: 20px;">
                    <h2 style="margin: 0;">{notification.title}</h2>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">System Monitoring Alert</p>
                </div>
                
                <div style="padding: 20px;">
                    <p style="font-size: 16px; line-height: 1.6; color: #333;">
                        {notification.message}
                    </p>
                    
                    {self._format_metadata_html(notification.metadata)}
                </div>
                
                <div style="padding: 20px; background-color: #f5f5f5; border-top: 1px solid #ddd;">
                    <p style="margin: 0; font-size: 12px; color: #757575;">
                        Severity: <strong>{notification.severity.value.upper()}</strong> | 
                        Timestamp: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _format_metadata_html(self, metadata: Dict) -> str:
        """Format metadata as HTML table"""
        if not metadata:
            return ""
        
        html = '<table style="width: 100%; border-collapse: collapse; margin-top: 15px;">'
        
        for key, value in metadata.items():
            if key != 'suggested_fixes':  # Handled separately
                html += f"""
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 8px; font-weight: bold; color: #666;">{key}:</td>
                    <td style="padding: 8px;">{value}</td>
                </tr>
                """
        
        html += '</table>'
        
        return html

# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_notification_manager(
    smtp_server: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_username: Optional[str] = None,
    smtp_password: Optional[str] = None,
    slack_webhook: Optional[str] = None,
    pagerduty_api_key: Optional[str] = None,
    pagerduty_service_key: Optional[str] = None
) -> NotificationManager:
    """
    Factory function to create NotificationManager with configured services
    """
    email_service = None
    if smtp_server and smtp_username and smtp_password:
        email_service = EmailService(
            smtp_server=smtp_server,
            smtp_port=smtp_port or 587,
            username=smtp_username,
            password=smtp_password
        )
    
    slack_service = None
    if slack_webhook:
        slack_service = SlackService(webhook_url=slack_webhook)
    
    pagerduty_service = None
    if pagerduty_api_key and pagerduty_service_key:
        pagerduty_service = PagerDutyService(
            api_key=pagerduty_api_key,
            service_key=pagerduty_service_key
        )
    
    return NotificationManager(
        email_service=email_service,
        slack_service=slack_service,
        pagerduty_service=pagerduty_service
    )
