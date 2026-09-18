"""Personality and Persona Configuration Schemas."""

from typing import Literal
from pydantic import BaseModel, Field


class PersonalitySettings(BaseModel):
    """Configurable traits and behavior parameters for the Jenna AI persona."""

    assistant_name: str = Field(
        default="Jenna",
        min_length=1,
        max_length=64,
        description="Display name for the personal AI companion",
    )
    personality_style: Literal["warm", "professional", "playful", "concise"] = Field(
        default="warm",
        description="Core personality tone and energy",
    )
    response_style: Literal["conversational", "structured", "direct"] = Field(
        default="conversational",
        description="Structural format of responses",
    )
    preferred_language: Literal["auto", "en", "hi", "hinglish"] = Field(
        default="auto",
        description="Linguistic preference ('auto' naturally matches user's language)",
    )
    preferred_locale: str = Field(
        default="en-IN",
        max_length=16,
        description="Locale convention for dates, times, and colloquialisms",
    )
    verbosity: Literal["concise", "normal", "detailed"] = Field(
        default="normal",
        description="Depth and length of answers",
    )
    formality: Literal["casual", "neutral", "formal"] = Field(
        default="casual",
        description="Level of formality in address",
    )
    humor_level: Literal["none", "subtle", "witty"] = Field(
        default="subtle",
        description="Appropriate level of wit and humor",
    )

    model_config = {"extra": "ignore"}


class PersonalitySettingsResponse(BaseModel):
    """Response wrapper for personality settings."""
    settings: PersonalitySettings
    user_id: str
