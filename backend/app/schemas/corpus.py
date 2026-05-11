from pydantic import BaseModel


class ShlokaOut(BaseModel):
    id: str
    canto: int
    chapter: int
    verse: str
    sanskrit: str
    transliteration: str
    translation: str
    summary: str
    characters: list[str]
    location: str
    themes: list[str]
    source_name: str
    source_url: str
    license: str

    model_config = {"from_attributes": True}
