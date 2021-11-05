from datetime import datetime
from enum import Enum
from typing import Any, Optional, TypeVar
from warnings import warn

from aenum import MultiValueEnum
from pydantic import BaseModel, Extra, Field, HttpUrl, validator

T = TypeVar('T')


def to_camel(string: str) -> str:
    first, *rest = string.split("_")
    return first + ''.join(word.capitalize() for word in rest)


class Difficulty(str, Enum):
    EASY = 'Easy'
    MEDIUM = 'Medium'
    TOUGH = 'Tough'
    VERY_TOUGH = 'VeryTough'


class SpecialArtistType(str, Enum):
    NONE = 'None'
    AUTHOR_IS_ARTIST = 'AuthorIsArtist'
    PUBLIC_LICENSE = 'PublicLicense'


class CanBePlayedOn(str, Enum):
    ONE_PLAYER_ONLY = 'OnePlayerOnly'
    TWO_PLAYER_ONLY = 'TwoPlayerOnly'
    BOTH_MODES = 'BothModes'


class FirstBeatBehavior(str, MultiValueEnum):
    RUN_NORMALLY = 'RunNormally'
    RUN_EVENTS_ON_PREBAR = 'RunEventsOnPrebar', 'RunEventsOnPreBar'


class MultiplayerAppearance(str, Enum):
    HORIZONTAL_STRIPS = 'HorizontalStrips'
    NOTHING = 'Nothing'


class PartialSettings(BaseModel):
    song: str
    artist: str
    author: str
    description: str
    difficulty: Difficulty = Difficulty.MEDIUM  # CLS seems to default to Medium when difficutly is missing
    seizure_warning: Optional[bool] = None  # maybe use strict bool here  Should this be optional? default to false?
    tags: list[str]

    class Config:
        extra = Extra.forbid

    @validator('difficulty', pre=True)
    def set_difficulty(cls, difficulty_input: Any) -> Difficulty:
        if isinstance(difficulty_input, Difficulty):
            return difficulty_input

        if difficulty_input in {e.value for e in Difficulty}:
            return Difficulty(difficulty_input)

        if difficulty_input in {e.name for e in Difficulty}:
            return Difficulty[difficulty_input]

        # CLS defaults to Easy when the difficulty is invalid
        warn(f'Invalid difficulty "{difficulty_input}", defaulting to {Difficulty.EASY}.')
        return Difficulty.EASY

    @validator('tags')
    def remove_empty_strings(cls, tags: list[str]) -> list[str]:
        return [tag for tag in tags if tag]


class SiteMetadata(PartialSettings):
    download_url: HttpUrl
    preview_img: Optional[HttpUrl]
    last_updated: datetime
    max_bpm: Optional[float]
    min_bpm: Optional[float]
    single_player: bool  # TODO: Decide how to reconcile this with LevelSettings
    two_player: bool
    verified: Optional[bool] = None

    class Config:
        extra = Extra.forbid

    @validator('preview_img', pre=True)
    def fix_empty_urls(cls, url: Any) -> Any:
        return url if url else None


class LevelSettings(PartialSettings):
    version: int
    syringe_icon: str
    special_artist_type: Optional[SpecialArtistType]  # make sure artist type None doesn't get turned into normal None
    song_name_hue: float
    separate_2p_level_filename: str = Field(alias="separate2PLevelFilename")  # TODO: variable naming?
    rank_max_mistakes: list[int] = Field(..., max_items=4, min_items=4)
    rank_description: list[str] = Field(..., max_items=6, min_items=6)
    preview_song: str
    preview_song_start_time: float
    preview_song_duration: float
    preview_image: str  # TODO: Make this the same as sitemetatdata with alias? do I want to do that
    multiplayer_appearance: MultiplayerAppearance
    first_beat_behavior: FirstBeatBehavior
    can_be_played_on: CanBePlayedOn
    # Should these use optional? should lack of field be treated the same as ""?
    level_volume: Optional[float] = None
    artist_permission: Optional[str] = None
    artist_links: Optional[str] = None
    mods: Optional[str] = None
    custom_class: Optional[str] = None

    class Config:
        alias_generator = to_camel

    @validator('tags', pre=True)
    def split_tags(cls, tags_string: str) -> list[str]:
        return [tag.strip() for tag in tags_string.split(',')]


class Level(BaseModel):
    settings: LevelSettings
    rows: list[dict[str, Any]]
    events: list[dict[str, Any]]
    conditionals: Optional[list[dict[str, Any]]] = None
