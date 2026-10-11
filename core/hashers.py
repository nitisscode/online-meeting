from django.contrib.auth.hashers import PBKDF2PasswordHasher


class ProjectPBKDF2PasswordHasher(PBKDF2PasswordHasher):
    iterations = 39000


def configure_password_hasher(iterations: int) -> None:
    ProjectPBKDF2PasswordHasher.iterations = iterations
