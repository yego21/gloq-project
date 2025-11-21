# journal/schemas.py (create this new file)

"""
Pydantic schemas for Django Ninja API.

Why Pydantic?
- Automatic validation: Wrong data types get rejected before hitting your view
- Type hints: Your IDE knows what fields exist and their types
- Auto documentation: Swagger UI generates from these schemas
- Serialization: Converts Django models to JSON automatically
"""



from ninja import Schema
from datetime import datetime, date, time
from typing import Optional, List
from decimal import Decimal


# ============================================================
# INPUT SCHEMAS (Data coming FROM frontend TO backend)
# ============================================================

class BirthProfileCreateSchema(Schema):
    """
    Schema for creating a new birth profile.
    All required fields must be provided by the user.
    """
    birth_date: date  # Required: YYYY-MM-DD format
    birth_time: Optional[time] = None  # Optional: HH:MM:SS format
    birth_latitude: Decimal  # Required: -90 to 90
    birth_longitude: Decimal  # Required: -180 to 180
    birth_timezone: str = "UTC"  # Default to UTC if not provided
    birth_city: Optional[str] = None  # Optional display field
    birth_country: Optional[str] = None  # Optional display field

    # Custom validation example
    class Config:
        schema_extra = {
            "example": {
                "birth_date": "1990-05-15",
                "birth_time": "14:30:00",
                "birth_latitude": 10.315700,
                "birth_longitude": 123.885400,
                "birth_timezone": "Asia/Manila",
                "birth_city": "Cebu City",
                "birth_country": "Philippines"
            }
        }


class BirthProfileUpdateSchema(Schema):
    """
    Schema for updating an existing birth profile.
    All fields are optional - only provided fields will be updated.
    """
    birth_date: Optional[date] = None
    birth_time: Optional[time] = None
    birth_latitude: Optional[Decimal] = None
    birth_longitude: Optional[Decimal] = None
    birth_timezone: Optional[str] = None
    birth_city: Optional[str] = None
    birth_country: Optional[str] = None


# ============================================================
# OUTPUT SCHEMAS (Data going FROM backend TO frontend)
# ============================================================

class BirthProfileOutSchema(Schema):
    """
    Schema for returning birth profile data.
    Includes computed fields like has_birth_time and chart_completeness.
    """
    id: int
    birth_date: date
    birth_time: Optional[time]
    birth_latitude: Decimal
    birth_longitude: Decimal
    birth_timezone: str
    birth_city: Optional[str]
    birth_country: Optional[str]
    has_birth_time: bool
    chart_completeness: int  # Percentage 0-100
    created_at: datetime
    updated_at: datetime

    # We don't include cached_chart_data here - that goes in separate schema

    @staticmethod
    def from_orm(birth_profile):
        """
        Convert Django model instance to this schema.
        Django Ninja calls this automatically.
        """
        return {
            'id': birth_profile.id,
            'birth_date': birth_profile.birth_date,
            'birth_time': birth_profile.birth_time,
            'birth_latitude': birth_profile.birth_latitude,
            'birth_longitude': birth_profile.birth_longitude,
            'birth_timezone': birth_profile.birth_timezone,
            'birth_city': birth_profile.birth_city,
            'birth_country': birth_profile.birth_country,
            'has_birth_time': birth_profile.has_birth_time,
            'chart_completeness': birth_profile.chart_completeness,
            'created_at': birth_profile.created_at,
            'updated_at': birth_profile.updated_at,
        }


# ============================================================
# CHART DATA SCHEMAS
# ============================================================

class PlanetPositionSchema(Schema):
    """
    Single planet's position in the natal chart.
    Matches the structure from your astronomical_svc.py
    """
    name: str  # "Sun", "Moon", "Mercury", etc.
    symbol: str  # Emoji or unicode symbol
    sign: str  # "Aries", "Taurus", etc.
    degree: int  # 0-29 degrees within sign
    longitude: float  # 0-360 absolute position
    element: str  # "Fire", "Earth", "Air", "Water"


class HouseSchema(Schema):
    """
    Single house cusp position.
    Only included if birth time is known.
    """
    house_number: int  # 1-12
    sign: str  # Sign on the cusp
    degree: int  # Degree within sign
    longitude: float  # Absolute position


class AspectSchema(Schema):
    """
    Planetary aspect (relationship between two planets).
    Example: Sun conjunct Moon, Mars square Venus
    """
    planet1: str  # "Sun"
    planet2: str  # "Moon"
    aspect_type: str  # "Conjunction", "Opposition", "Trine", "Square", "Sextile"
    angle: float  # Exact angle between planets
    orb: float  # How close to exact (smaller = stronger)


class NatalChartSchema(Schema):
    """
    Complete natal chart calculation result.
    This is what gets cached in BirthProfile.cached_chart_data
    """
    planets: List[PlanetPositionSchema]
    houses: Optional[List[HouseSchema]]  # Null if no birth time
    aspects: List[AspectSchema]

    # Ascendant and Midheaven (if birth time known)
    ascendant: Optional[dict] = None  # {"sign": "Scorpio", "degree": 15}
    midheaven: Optional[dict] = None  # {"sign": "Leo", "degree": 22}

    # Summary data
    dominant_element: str  # Most common element
    dominant_modality: Optional[str] = None  # "Cardinal", "Fixed", "Mutable"

    # Metadata
    calculated_at: datetime
    has_houses: bool  # Quick flag for frontend


class NatalChartResponseSchema(Schema):
    """
    Full response when requesting a natal chart.
    Includes both the birth profile and the chart calculation.
    """
    birth_profile: BirthProfileOutSchema
    natal_chart: NatalChartSchema


# ============================================================
# CURRENT TRANSIT SCHEMAS (Your existing real-time data)
# ============================================================

class MoonPhaseSchema(Schema):
    """
    Current moon phase data.
    Matches your existing get_moon_phase() output.
    """
    phase: str
    emoji: str
    description: str
    illumination: str
    illumination_decimal: float
    mystical_meaning: str
    next_phase_days: int
    phase_angle: Optional[float] = None
    visual_phase: Optional[dict] = None


class PlanetarySummarySchema(Schema):
    """
    Current planetary positions for today.
    Matches your existing get_planetary_summary() output.
    """
    sun_sign: str
    moon_sign: str
    mercury_sign: Optional[str] = None
    venus_sign: Optional[str] = None
    mars_sign: Optional[str] = None
    planetary_positions: List[PlanetPositionSchema]
    dominant_element: str
    cosmic_weather: str


# ============================================================
# ERROR SCHEMAS
# ============================================================

class ErrorSchema(Schema):
    """
    Standardized error response.
    All endpoints return this structure on errors.
    """
    detail: str  # Human-readable error message
    code: Optional[str] = None  # Machine-readable error code

    class Config:
        schema_extra = {
            "example": {
                "detail": "Birth profile not found for this user",
                "code": "PROFILE_NOT_FOUND"
            }
        }


class ValidationErrorSchema(Schema):
    """
    Validation error with field-specific details.
    """
    detail: str
    errors: dict  # Field name -> error message

    class Config:
        schema_extra = {
            "example": {
                "detail": "Validation failed",
                "errors": {
                    "birth_date": "Birth date cannot be in the future",
                    "birth_latitude": "Must be between -90 and 90"
                }
            }
        }