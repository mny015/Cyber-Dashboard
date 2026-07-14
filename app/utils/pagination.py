"""Bounded pagination parsing shared by list controllers."""

from dataclasses import dataclass

from flask import request


@dataclass(frozen=True, slots=True)
class PaginationRequest:
    page: int
    per_page: int

    @property
    def offset(self):
        return (self.page - 1) * self.per_page


def normalize_pagination(page=1, per_page=25, *, default_per_page=25, max_per_page=100):
    return PaginationRequest(
        page=_bounded_integer(page, default=1, minimum=1),
        per_page=_bounded_integer(
            per_page,
            default=default_per_page,
            minimum=1,
            maximum=max_per_page,
        ),
    )


def pagination_from_request(*, default_per_page=25, max_per_page=100):
    return normalize_pagination(
        request.args.get("page", 1),
        request.args.get("per_page", default_per_page),
        default_per_page=default_per_page,
        max_per_page=max_per_page,
    )


def _bounded_integer(value, *, default, minimum, maximum=None):
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        normalized = default
    normalized = max(normalized, minimum)
    if maximum is not None:
        normalized = min(normalized, maximum)
    return normalized
