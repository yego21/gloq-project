# journal/api.py (create this new file)

"""
Django Ninja API Router for Cosmic Oracle features.

Structure:
- NinjaAPI instance handles all routing
- Authentication required for personal data (natal charts)
- Public endpoints for general cosmic data (moon phase, transits)
"""

from ninja import NinjaAPI, Router
from ninja.security import django_auth
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from typing import List

from userprofile.models import BirthProfile
from ..schemas import (
    # Input schemas
    BirthProfileCreateSchema,
    BirthProfileUpdateSchema,

    # Output schemas
    BirthProfileOutSchema,
    MoonPhaseSchema,
    PlanetarySummarySchema,
    NatalChartSchema,
    NatalChartResponseSchema,
    ErrorSchema,
)

from ..services.mystical.astronomical_svc import (
    get_moon_phase,
    get_planetary_summary,
    # We'll add get_natal_chart later
)
from ..services.mystical.natal_chart_svc import NatalChartService

# ============================================================
# INITIALIZE API
# ============================================================

api = NinjaAPI(
    title="Cosmic Oracle API",
    version="1.0.0",
    description="Astronomical calculations and mystical insights",
    docs_url="/docs",  # Swagger UI at this URL
)

# Create separate routers for organization
cosmic_router = Router(tags=["Cosmic Data"])  # Public endpoints
profile_router = Router(tags=["Birth Profile"])  # Authenticated endpoints


# ============================================================
# PUBLIC ENDPOINTS (No authentication required)
# ============================================================

@cosmic_router.get("/moon-phase", response=MoonPhaseSchema)
def get_current_moon_phase(request):
    """
    Get current moon phase with mystical interpretation.

    Returns:
        - Current phase name and emoji
        - Illumination percentage
        - Mystical meaning
        - Days until next phase

    No authentication required - this is public cosmic data.
    """
    moon_data = get_moon_phase()
    return moon_data


@cosmic_router.get("/planetary-summary", response=PlanetarySummarySchema)
def get_current_planetary_positions(request, timezone: str = "UTC"):
    """
    Get current planetary positions and cosmic weather.

    Args:
        timezone: IANA timezone string (default: UTC)

    Returns:
        - Current sign positions for major planets
        - Dominant element
        - Cosmic weather summary

    No authentication required.
    """
    planetary_data = get_planetary_summary(timezone)
    return planetary_data


# ============================================================
# AUTHENTICATED ENDPOINTS (Require login)
# ============================================================

@profile_router.post(
    "/birth-profile",
    response={201: BirthProfileOutSchema, 400: ErrorSchema},
    auth=django_auth  # This line requires authentication
)
def create_birth_profile(request, payload: BirthProfileCreateSchema):
    """
    Create a birth profile for the authenticated user.

    Authentication: Required (user must be logged in)

    Args:
        payload: Birth profile data (validated by Pydantic)

    Returns:
        201: Created birth profile
        400: Validation error or profile already exists

    Note: Each user can only have ONE birth profile.
    """
    # Check if user already has a birth profile
    if hasattr(request.user, 'birth_profile'):
        return 400, {
            "detail": "Birth profile already exists. Use PUT to update.",
            "code": "PROFILE_EXISTS"
        }

    # Create the birth profile
    # payload.dict() converts Pydantic schema to regular dict
    birth_profile = BirthProfile.objects.create(
        user=request.user,
        **payload.dict()
    )

    # Return the created profile (201 = Created)
    return 201, birth_profile


@profile_router.get(
    "/birth-profile",
    response={200: BirthProfileOutSchema, 404: ErrorSchema},
    auth=django_auth
)
def get_my_birth_profile(request):
    """
    Get the authenticated user's birth profile.

    Authentication: Required

    Returns:
        200: User's birth profile
        404: No birth profile exists for this user
    """
    try:
        # OneToOne relationship: request.user.birth_profile
        birth_profile = request.user.birth_profile
        return 200, birth_profile
    except BirthProfile.DoesNotExist:
        return 404, {
            "detail": "Birth profile not found. Create one first.",
            "code": "PROFILE_NOT_FOUND"
        }


@profile_router.put(
    "/birth-profile",
    response={200: BirthProfileOutSchema, 404: ErrorSchema},
    auth=django_auth
)
def update_birth_profile(request, payload: BirthProfileUpdateSchema):
    """
    Update the authenticated user's birth profile.

    Authentication: Required

    Args:
        payload: Fields to update (all optional)

    Returns:
        200: Updated birth profile
        404: No birth profile exists

    Note: Updating invalidates cached chart data.
    """
    try:
        birth_profile = request.user.birth_profile
    except BirthProfile.DoesNotExist:
        return 404, {
            "detail": "Birth profile not found. Create one first.",
            "code": "PROFILE_NOT_FOUND"
        }

    # Update only fields that were provided
    # payload.dict(exclude_unset=True) ignores None values
    update_data = payload.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(birth_profile, field, value)

    # Invalidate cache since birth data changed
    birth_profile.invalidate_cache()

    # Save triggers the model's save() method (sets has_birth_time flag)
    birth_profile.save()

    return 200, birth_profile


@profile_router.delete(
    "/birth-profile",
    response={204: None, 404: ErrorSchema},
    auth=django_auth
)
def delete_birth_profile(request):
    """
    Delete the authenticated user's birth profile.

    Authentication: Required

    Returns:
        204: Successfully deleted (no content)
        404: No birth profile exists

    Warning: This permanently deletes the birth profile and cached chart.
    """
    try:
        birth_profile = request.user.birth_profile
        birth_profile.delete()
        return 204, None  # 204 = No Content (success, nothing to return)
    except BirthProfile.DoesNotExist:
        return 404, {
            "detail": "Birth profile not found.",
            "code": "PROFILE_NOT_FOUND"
        }


@profile_router.get(
    "/natal-chart",
    response={200: NatalChartResponseSchema, 404: ErrorSchema},
    auth=django_auth
)
def get_my_natal_chart(request, force_recalculate: bool = False):
    """Calculate and return the user's natal chart."""
    try:
        birth_profile = request.user.birth_profile
    except BirthProfile.DoesNotExist:
        return 404, {
            "detail": "Birth profile required. Create one first.",
            "code": "PROFILE_NOT_FOUND"
        }

    # Check cache
    if birth_profile.cached_chart_data and not force_recalculate:
        natal_chart = birth_profile.cached_chart_data
    else:
        # Calculate using the class directly
        service = NatalChartService(birth_profile)
        natal_chart = service.generate_natal_chart()

        # Cache the result
        birth_profile.cached_chart_data = natal_chart
        birth_profile.save(update_fields=['cached_chart_data'])

    return 200, {
        "birth_profile": birth_profile,
        "natal_chart": natal_chart
    }


# ============================================================
# REGISTER ROUTERS
# ============================================================

# Add all routers to main API
api.add_router("/cosmic/", cosmic_router)
api.add_router("/profile/", profile_router)


# ============================================================
# HEALTH CHECK
# ============================================================

@api.get("/health")
def health_check(request):
    """
    Simple health check endpoint.
    Used to verify API is running.
    """
    return {"status": "ok", "message": "Cosmic Oracle API is running"}