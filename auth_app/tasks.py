from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_html_email(subject, template, context, recipient, fallback_text):
    """Sends an email with an HTML body and a plain text fallback."""
    html_content = render_to_string(template, context)
    message = EmailMultiAlternatives(
        subject=subject,
        body=fallback_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
    )
    message.attach_alternative(html_content, "text/html")
    message.send(fail_silently=False)


def send_activation_email(user_email, activation_link):
    """Sends the account activation email to a newly registered user."""
    send_html_email(
        subject="Confirm your email",
        template="emails/activation_email.html",
        context={"user_email": user_email, "activation_link": activation_link},
        recipient=user_email,
        fallback_text=f"Please activate your account: {activation_link}",
    )


def send_password_reset_email(user_email, reset_link):
    """Sends the password reset email to a user."""
    send_html_email(
        subject="Reset your Password",
        template="emails/password_reset_email.html",
        context={"reset_link": reset_link},
        recipient=user_email,
        fallback_text=f"Reset your password: {reset_link}",
    )
