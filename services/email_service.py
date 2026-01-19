"""
Email service for sending password reset emails and other notifications.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings
import secrets
from datetime import datetime, timedelta
from typing import Optional

# Store reset tokens temporarily (in production, use Redis or database)
reset_tokens = {}

def generate_reset_token(user_id: int, email: str) -> str:
    """Generate a password reset token"""
    token = secrets.token_urlsafe(32)
    reset_tokens[token] = {
        "user_id": user_id,
        "email": email,
        "expires": datetime.utcnow() + timedelta(hours=1)
    }
    return token

def verify_reset_token(token: str) -> Optional[dict]:
    """Verify a reset token and return user data if valid"""
    if token not in reset_tokens:
        return None
    
    data = reset_tokens[token]
    if datetime.utcnow() > data["expires"]:
        del reset_tokens[token]
        return None
    
    return data

def invalidate_reset_token(token: str):
    """Remove a used reset token"""
    if token in reset_tokens:
        del reset_tokens[token]

def send_password_reset_email(to_email: str, reset_link: str) -> bool:
    """Send password reset email via SMTP"""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print("⚠️ SMTP not configured. Would have sent reset email to:", to_email)
        print("   Reset link:", reset_link)
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '🔐 TrueCheck - Recuperação de Senha'
        msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USER}>"
        msg['To'] = to_email
        
        # HTML email body
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #3b82f6; color: white !important; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 TrueCheck</h1>
                    <p>Recuperação de Senha</p>
                </div>
                <div class="content">
                    <p>Olá,</p>
                    <p>Recebemos um pedido para redefinir a sua senha. Clique no botão abaixo para continuar:</p>
                    <p style="text-align: center;">
                        <a href="{reset_link}" class="button">Redefinir Senha</a>
                    </p>
                    <p><strong>Este link expira em 1 hora.</strong></p>
                    <p>Se não solicitou esta alteração, ignore este email. A sua senha permanecerá inalterada.</p>
                    <div class="footer">
                        <p>TrueCheck - Plataforma de Verificação de Factos</p>
                        <p>Este é um email automático, por favor não responda.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text fallback
        text = f"""
        TrueCheck - Recuperação de Senha
        
        Olá,
        
        Recebemos um pedido para redefinir a sua senha.
        
        Clique no link abaixo para continuar:
        {reset_link}
        
        Este link expira em 1 hora.
        
        Se não solicitou esta alteração, ignore este email.
        
        --
        TrueCheck - Plataforma de Verificação de Factos
        """
        
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Connect to SMTP server and send
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Password reset email sent to: {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False
