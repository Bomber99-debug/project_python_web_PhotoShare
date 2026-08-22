"""User roles used by authorization rules."""

from enum import Enum


class Role( str, Enum ):
	USER = "user"
	MODERATOR = "moderator"
	ADMIN = "admin"
