
# accounts/views.py

import secrets

from django.db import connection, transaction, IntegrityError
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import UserRegistrationForm


class SignUpView(CreateView):
    form_class = UserRegistrationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"

    MAX_ID_ATTEMPTS = 20

    @staticmethod
    def generate_account_id():
        """
        Generate a random eight-digit career account ID.
        """
        reserved_ids = {
            "00000000",
            "11111111",
            "99999999",
        }

        while True:
            account_id = f"{secrets.randbelow(100000000):08d}"

            if account_id not in reserved_ids:
                return account_id

    @staticmethod
    def is_account_id_collision(error):
        """
        Only retry duplicate-primary-key errors.

        Other database errors must not be treated
        as account ID collisions.
        """
        original = error.__cause__ or error
        args = getattr(original, "args", ())

        return (
            len(args) >= 2
            and args[0] == 1062
            and "PRIMARY" in str(args[1]).upper()
        )

    def create_career_account(self, user):
        """
        Insert an account linked to Django auth_user.

        Each attempt uses a savepoint so a duplicate
        account ID does not invalidate the outer
        registration transaction.
        """
        for _ in range(self.MAX_ID_ATTEMPTS):
            account_id = self.generate_account_id()

            try:
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
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
                            """,
                            [
                                account_id,
                                user.pk,
                                user.first_name,
                                user.last_name,
                                user.email,
                            ],
                        )

                return account_id

            except IntegrityError as error:
                if self.is_account_id_collision(error):
                    continue

                raise

        raise ValueError(
            "Unable to generate a unique career account ID."
        )

    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Create Django authentication user.
                self.object = form.save()

                # Create linked CaLLP career account.
                self.create_career_account(self.object)

        except (IntegrityError, ValueError):
            form.add_error(
                None,
                "Unable to create your account. "
                "Please check your information and try again."
            )

            return self.form_invalid(form)

        return HttpResponseRedirect(self.get_success_url())
