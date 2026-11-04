
# accounts/views.py

import secrets

from django.db import connection, transaction, IntegrityError
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.http import HttpResponseRedirect
from .forms import UserRegistrationForm


class SignUpView(CreateView):
    form_class = UserRegistrationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"

    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Create the Django auth_user record
                self.object = form.save()

                # Generate an unused 8-digit career account ID
                account_id = self.generate_account_id()

                # Create the linked career account
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO account (
                            acc_id,
                            auth_user_id,
                            acc_fname,
                            acc_lname,
                            acc_email,
                            acc_role,
                            acc_status
                        )
                        VALUES (
                            %s, %s, %s, %s, %s,
                            'student', 'active'
                        )
                    """, [
                        account_id,
                        self.object.pk,
                        self.object.first_name,
                        self.object.last_name,
                        self.object.email
                    ])

        except (IntegrityError, ValueError):
            form.add_error(
                None,
                "Unable to create your account. Please try again."
            )
            return self.form_invalid(form)

        return HttpResponseRedirect(self.get_success_url())

    @staticmethod
    def generate_account_id():
        """
        Generate an unused 8-digit ID.
        Excludes reserved system account IDs.
        """
        reserved = {
            "00000000",
            "11111111",
            "99999999"
        }

        for _ in range(20):
            account_id = f"{secrets.randbelow(100000000):08d}"

            if account_id in reserved:
                continue

            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM account WHERE acc_id = %s",
                    [account_id]
                )

                if cursor.fetchone() is None:
                    return account_id

        raise ValueError("Could not generate an account ID.")
