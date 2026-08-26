from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_activation_email(user_email, activation_link):
    """Sends the account activation email to a newly registered user."""
    context = {"user_email": user_email, "activation_link": activation_link}
    html_content = render_to_string("emails/activation_email.html", context)
    message = EmailMultiAlternatives(
        subject="Confirm your email",
        body=f"Please activate your account: {activation_link}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user_email],
    )
    message.attach_alternative(html_content, "text/html")
    message.send()


def send_password_reset_email(user_email, reset_link):
    """Sends the password reset email to a user."""
    context = {"reset_link": reset_link}
    html_content = render_to_string("emails/password_reset_email.html", context)
    message = EmailMultiAlternatives(
        subject="Reset your Password",
        body=f"Reset your password: {reset_link}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user_email],
    )
    message.attach_alternative(html_content, "text/html")
    message.send(fail_silently=False)
