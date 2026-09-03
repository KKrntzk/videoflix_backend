from django.contrib.auth.tokens import PasswordResetTokenGenerator


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """Generates activation tokens that expire once the account is active."""

    def _make_hash_value(self, user, timestamp):
        """Includes is_active so the token expires after activation."""
        return f"{user.pk}{timestamp}{user.is_active}"


account_activation_token = AccountActivationTokenGenerator()
