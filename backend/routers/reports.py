"""
Reports router - Email reporting functionality
Sends HTML email reports with system status and AI analysis
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from core.logger import get_logger
from core.config import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import psutil
import os

logger = get_logger("reports")
router = APIRouter()

# Email configuration from environment variables
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))


class ReportRequest(BaseModel):
    """Email report request"""
    recipient_email: EmailStr
    subject: Optional[str] = "System Monitoring Report"
    include_ai_analysis: bool = True
    custom_message: Optional[str] = None


class ReportResponse(BaseModel):
    """Email report response"""
    success: bool
    message: str
    recipient: str
    timestamp: datetime


def get_current_metrics_dict() -> dict:
    """Get current system metrics as dictionary"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        return {
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory.percent, 2),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "disk_percent": round(disk.percent, 2),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "network_sent_mb": round(network.bytes_sent / (1024**2), 2),
            "network_recv_mb": round(network.bytes_recv / (1024**2), 2),
            "process_count": len(psutil.pids())
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return {}


def get_status_color(value: float, warning: float = 70, critical: float = 90) -> str:
    """Get status color based on value"""
    if value >= critical:
        return "#e74c3c"  # Red
    elif value >= warning:
        return "#f39c12"  # Orange
    else:
        return "#27ae60"  # Green


def get_status_emoji(value: float, warning: float = 70, critical: float = 90) -> str:
    """Get status emoji based on value"""
    if value >= critical:
        return "🔴"
    elif value >= warning:
        return "🟡"
    else:
        return "🟢"


async def get_ai_analysis(metrics: dict) -> str:
    """Get AI analysis if available"""
    try:
        from groq import Groq
        
        if not settings.GROQ_API_KEY:
            return "<p>AI analysis unavailable - GROQ API key not configured.</p>"
        
        client = Groq(api_key=settings.GROQ_API_KEY)
        
        prompt = f"""Provide a brief 3-sentence system health summary based on these metrics:
- CPU: {metrics.get('cpu_percent', 'N/A')}%
- Memory: {metrics.get('memory_percent', 'N/A')}%
- Disk: {metrics.get('disk_percent', 'N/A')}%

Focus on: overall health, any concerns, and one recommendation."""

        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a concise system monitoring expert. Be brief and actionable."},
                {"role": "user", "content": prompt}
            ],
            model=settings.GROQ_MODEL or "llama-3.1-70b-versatile",
            temperature=0.5,
            max_tokens=150
        )
        
        return f"<p>{response.choices[0].message.content}</p>"
    
    except Exception as e:
        logger.error(f"Error getting AI analysis: {e}")
        return f"<p>AI analysis unavailable: {str(e)}</p>"


def generate_html_report(metrics: dict, ai_analysis: str = "", custom_message: str = "") -> str:
    """Generate HTML email report"""
    
    cpu_color = get_status_color(metrics.get('cpu_percent', 0))
    memory_color = get_status_color(metrics.get('memory_percent', 0))
    disk_color = get_status_color(metrics.get('disk_percent', 0))
    
    cpu_emoji = get_status_emoji(metrics.get('cpu_percent', 0))
    memory_emoji = get_status_emoji(metrics.get('memory_percent', 0))
    disk_emoji = get_status_emoji(metrics.get('disk_percent', 0))
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #3498db;
            padding-bottom: 20px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            color: #2c3e50;
            margin: 0;
        }}
        .metric-card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid;
        }}
        .metric-title {{
            font-weight: bold;
            font-size: 14px;
            color: #666;
            margin-bottom: 5px;
        }}
        .metric-value {{
            font-size: 28px;
            font-weight: bold;
        }}
        .metric-detail {{
            font-size: 12px;
            color: #888;
        }}
        .ai-section {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
        }}
        .ai-section h3 {{
            margin-top: 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #888;
            font-size: 12px;
        }}
        .status-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 System Monitoring Report</h1>
            <p style="color: #666; margin: 10px 0 0 0;">Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        </div>
        
        {f'<div style="background: #e8f4fd; padding: 15px; border-radius: 8px; margin-bottom: 20px;"><strong>📝 Note:</strong> {custom_message}</div>' if custom_message else ''}
        
        <h2>📈 Current System Status</h2>
        
        <div class="metric-card" style="border-color: {cpu_color};">
            <div class="metric-title">{cpu_emoji} CPU USAGE</div>
            <div class="metric-value" style="color: {cpu_color};">{metrics.get('cpu_percent', 'N/A')}%</div>
        </div>
        
        <div class="metric-card" style="border-color: {memory_color};">
            <div class="metric-title">{memory_emoji} MEMORY USAGE</div>
            <div class="metric-value" style="color: {memory_color};">{metrics.get('memory_percent', 'N/A')}%</div>
            <div class="metric-detail">{metrics.get('memory_used_gb', 0)} GB / {metrics.get('memory_total_gb', 0)} GB</div>
        </div>
        
        <div class="metric-card" style="border-color: {disk_color};">
            <div class="metric-title">{disk_emoji} DISK USAGE</div>
            <div class="metric-value" style="color: {disk_color};">{metrics.get('disk_percent', 'N/A')}%</div>
            <div class="metric-detail">{metrics.get('disk_used_gb', 0)} GB / {metrics.get('disk_total_gb', 0)} GB</div>
        </div>
        
        <div class="metric-card" style="border-color: #3498db;">
            <div class="metric-title">🌐 NETWORK I/O</div>
            <div class="metric-detail">
                ↑ Sent: {metrics.get('network_sent_mb', 0)} MB | ↓ Received: {metrics.get('network_recv_mb', 0)} MB
            </div>
        </div>
        
        <div class="metric-card" style="border-color: #9b59b6;">
            <div class="metric-title">⚙️ ACTIVE PROCESSES</div>
            <div class="metric-value" style="color: #9b59b6;">{metrics.get('process_count', 'N/A')}</div>
        </div>
        
        {f'''
        <div class="ai-section">
            <h3>🤖 AI Analysis</h3>
            {ai_analysis}
        </div>
        ''' if ai_analysis else ''}
        
        <div class="footer">
            <p>This report was automatically generated by System Monitoring Dashboard</p>
            <p>Deployed on Hugging Face Spaces</p>
        </div>
    </div>
</body>
</html>
"""
    return html


@router.post("/send-report", response_model=ReportResponse)
async def send_report(request: ReportRequest):
    """
    Send HTML email report with current system status and AI analysis
    
    Required environment variables:
    - EMAIL_USER: Sender email address
    - EMAIL_PASS: Email app password
    - SMTP_SERVER: SMTP server (default: smtp.gmail.com)
    - SMTP_PORT: SMTP port (default: 587)
    """
    logger.info(f"Sending report to {request.recipient_email}")
    
    # Validate email configuration
    if not EMAIL_USER or not EMAIL_PASS:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "EMAIL_NOT_CONFIGURED",
                "message": "Email credentials not configured. Set EMAIL_USER and EMAIL_PASS environment variables.",
                "solution": "Add EMAIL_USER and EMAIL_PASS to your Hugging Face Space secrets"
            }
        )
    
    try:
        # Get current metrics
        metrics = get_current_metrics_dict()
        
        if not metrics:
            raise HTTPException(status_code=500, detail="Failed to collect system metrics")
        
        # Get AI analysis if requested
        ai_analysis = ""
        if request.include_ai_analysis:
            ai_analysis = await get_ai_analysis(metrics)
        
        # Generate HTML report
        html_content = generate_html_report(
            metrics=metrics,
            ai_analysis=ai_analysis,
            custom_message=request.custom_message or ""
        )
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = request.subject
        msg['From'] = EMAIL_USER
        msg['To'] = request.recipient_email
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, request.recipient_email, msg.as_string())
        
        logger.info(f"Report sent successfully to {request.recipient_email}")
        
        return ReportResponse(
            success=True,
            message="Report sent successfully!",
            recipient=request.recipient_email,
            timestamp=datetime.utcnow()
        )
    
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed")
        raise HTTPException(
            status_code=401,
            detail={
                "error": "SMTP_AUTH_FAILED",
                "message": "Email authentication failed. Check your EMAIL_USER and EMAIL_PASS.",
                "solution": "For Gmail, use an App Password (not your regular password)"
            }
        )
    
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "SMTP_ERROR",
                "message": f"Failed to send email: {str(e)}"
            }
        )
    
    except Exception as e:
        logger.error(f"Error sending report: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "REPORT_FAILED",
                "message": f"Failed to send report: {str(e)}"
            }
        )


@router.get("/email-config")
async def check_email_config():
    """Check email configuration status"""
    return {
        "email_configured": bool(EMAIL_USER and EMAIL_PASS),
        "smtp_server": SMTP_SERVER,
        "smtp_port": SMTP_PORT,
        "sender_email": EMAIL_USER[:3] + "***" if EMAIL_USER else None,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/test-email")
async def test_email_connection():
    """Test SMTP connection without sending an email"""
    if not EMAIL_USER or not EMAIL_PASS:
        raise HTTPException(
            status_code=503,
            detail="Email credentials not configured"
        )
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
        
        return {
            "success": True,
            "message": "SMTP connection successful!",
            "smtp_server": SMTP_SERVER
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"SMTP connection failed: {str(e)}"
        )
