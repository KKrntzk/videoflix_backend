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
