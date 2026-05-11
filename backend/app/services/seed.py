from sqlalchemy.orm import Session

from app.models.character import CharacterAlias, CharacterForm, CharacterIdentity
from app.models.corpus import CorpusShloka
from app.services.text import normalize_name


INITIAL_CHARACTERS = [
    {
        "canonical_name": "Sri Krishna",
        "category": "avatar",
        "aliases": ["Krishna", "Kanha", "Gopala", "Govinda", "Damodara", "Madhava", "Mukunda"],
        "description": "The Supreme Lord appearing in the Yadava lineage and Vrindavan pastimes.",
        "forms": [
            {
                "form_name": "Child Krishna of Vrindavan",
                "age_stage": "child",
                "visual_profile": (
                    "Divine child with deep blue complexion, large lotus-like eyes, curly black hair, "
                    "peacock feather crown, yellow silk dhoti, pearl and flower garlands, gold ornaments, "
                    "gentle playful smile, often holding a flute or butter."
                ),
                "cultural_rules": "Must feel rooted in Vrindavan devotional art, not Western fantasy royalty.",
                "negative_prompt": "western crown, european prince outfit, modern clothing, horror, gore",
                "status": "draft",
                "is_default": True,
            }
        ],
    },
    {
        "canonical_name": "Balarama",
        "category": "avatar",
        "aliases": ["Baladeva", "Balabhadra", "Rama"],
        "description": "Krishna's elder brother, strong and protective.",
        "forms": [
            {
                "form_name": "Young Balarama of Vrindavan",
                "age_stage": "child",
                "visual_profile": (
                    "Fair-complexioned divine boy with strong rounded features, dark hair, blue or white silk garments, "
                    "simple gold ornaments, confident protective expression, often associated with plough and pastoral settings."
                ),
                "cultural_rules": "Indic cowherd prince styling, gentle and protective, never medieval European.",
                "negative_prompt": "western armor, european farm boy, modern clothing, gore",
                "status": "draft",
                "is_default": True,
            }
        ],
    },
    {
        "canonical_name": "Mother Yashoda",
        "category": "devotee",
        "aliases": ["Yashoda", "Yasoda", "Yashoda Maiya", "Maiya Yashoda"],
        "description": "Krishna's loving foster mother in Gokula and Vrindavan.",
        "forms": [
            {
                "form_name": "Mother Yashoda of Gokula",
                "age_stage": "adult",
                "visual_profile": (
                    "Warm motherly Indian woman with kind expressive eyes, graceful sari, traditional jewelry, "
                    "hair tied neatly with flowers, gentle protective posture, soft maternal expression."
                ),
                "cultural_rules": "Village Gokula styling with devotional warmth; no Western household setting.",
                "negative_prompt": "western dress, modern kitchen, european village, horror",
                "status": "draft",
                "is_default": True,
            }
        ],
    },
    {
        "canonical_name": "Nanda Maharaja",
        "category": "devotee",
        "aliases": ["Nanda", "Nanda Baba", "Nanda Maharaj"],
        "description": "The respected cowherd chief of Gokula and Krishna's foster father.",
        "forms": [
            {
                "form_name": "Nanda Maharaja of Gokula",
                "age_stage": "adult",
                "visual_profile": (
                    "Kind dignified Indian cowherd chief with warm brown complexion, moustache, dhoti, angavastra, "
                    "turban, simple gold ornaments, fatherly expression, village elder presence."
                ),
                "cultural_rules": "Indic pastoral village leader, not Western king.",
                "negative_prompt": "european king robe, western crown, modern clothing, gore",
                "status": "draft",
                "is_default": True,
            }
        ],
    },
    {
        "canonical_name": "Narada Muni",
        "category": "rishi",
        "aliases": ["Narada", "Narad", "Devarshi Narada"],
        "description": "The travelling sage and devotee who carries divine messages.",
        "forms": [
            {
                "form_name": "Travelling Sage Narada",
                "age_stage": "timeless sage",
                "visual_profile": (
                    "Radiant sage with serene face, tied matted hair, saffron robes, tilaka, prayer beads, "
                    "small hand cymbals or veena/tambura, floating or walking gracefully with joyful devotion."
                ),
                "cultural_rules": "Classical Hindu rishi iconography with musical instrument.",
                "negative_prompt": "wizard hat, western lute, medieval monk, horror",
                "status": "draft",
                "is_default": True,
            }
        ],
    },
    {
        "canonical_name": "Prahlada Maharaja",
        "category": "devotee",
        "aliases": ["Prahlada", "Prahalada", "Prahlad"],
        "description": "The child devotee famous for unwavering devotion to Lord Vishnu.",
        "forms": [
            {
                "form_name": "Child Prahlada",
                "age_stage": "child",
                "visual_profile": (
                    "Gentle young prince with calm devotional expression, traditional dhoti and ornaments, "
                    "hands often folded in prayer, luminous innocence, palace or gurukula setting."
                ),
                "cultural_rules": "Indic royal child, devotional composure, no Western prince costume.",
                "negative_prompt": "european prince, modern school uniform, horror gore",
                "status": "draft",
                "is_default": True,
            }
        ],
    },
    {
        "canonical_name": "Narasimha",
        "category": "avatar",
        "aliases": ["Lord Narasimha", "Nrsimha", "Narasimhadeva"],
        "description": "The man-lion avatar of Lord Vishnu who protects Prahlada.",
        "forms": [
            {
                "form_name": "Protective Narasimha",
                "age_stage": "divine form",
                "visual_profile": (
                    "Majestic divine man-lion form with golden mane, powerful protective posture, ornate dhoti and jewelry, "
                    "radiant aura, fierce yet controlled expression, shown as protector of Prahlada."
                ),
                "cultural_rules": "Devotional symbolic power; intense but non-graphic.",
                "negative_prompt": "gore, blood spray, horror monster, dismemberment, western beast design",
                "status": "draft",
                "is_default": True,
            }
        ],
    },
    {
        "canonical_name": "Hiranyakashipu",
        "category": "asura",
        "aliases": ["Hiranyakasipu", "Hiranyakashipu", "Hiranyakashyap"],
        "description": "The powerful asura king and father of Prahlada.",
        "forms": [
            {
                "form_name": "Asura King Hiranyakashipu",
                "age_stage": "adult",
                "visual_profile": (
                    "Imposing asura king with regal Indic armor and ornaments, intense eyes, dark royal palette, "
                    "large palace presence, proud posture, mythological but not horror-like."
                ),
                "cultural_rules": "Indic asura royalty; avoid demon caricature or Western devil imagery.",
                "negative_prompt": "horned devil, western demon, gore, horror, modern weapon",
                "status": "draft",
                "is_default": True,
            }
        ],
    },
]

INITIAL_SHLOKAS = [
    {
        "canto": 1,
        "chapter": 1,
        "verse": "1",
        "sanskrit": "",
        "transliteration": "",
        "translation": "",
        "summary": (
            "Invocation and philosophical opening of the Bhagavatham: meditate on the Supreme Truth, "
            "the source, sustainer, and knower of all creation."
        ),
        "characters": ["Sri Krishna"],
        "location": "Cosmic devotional opening",
        "themes": ["creation", "supreme truth", "devotion", "inquiry"],
        "source_name": "Bhagavatham repository seed",
        "source_url": "https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/html/sa_bhAgavatapurANa.htm",
        "license": "Source metadata only; full Sanskrit/translation ingestion pending license review",
    },
    {
        "canto": 3,
        "chapter": 25,
        "verse": "21-44",
        "sanskrit": "",
        "transliteration": "",
        "translation": "",
        "summary": (
            "Kapila teaches Devahuti about devotion, the nature of consciousness, and the path that "
            "turns the heart toward liberation."
        ),
        "characters": ["Kapila", "Devahuti"],
        "location": "Sage Kapila's hermitage",
        "themes": ["teaching", "devotion", "liberation", "mother and son"],
        "source_name": "Bhagavatham repository seed",
        "source_url": "https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/html/sa_bhAgavatapurANa.htm",
        "license": "Source metadata only; full Sanskrit/translation ingestion pending license review",
    },
    {
        "canto": 7,
        "chapter": 5,
        "verse": "23-24",
        "sanskrit": "",
        "transliteration": "",
        "translation": "",
        "summary": (
            "Prahlada describes the nine forms of devotion, presenting bhakti as hearing, chanting, "
            "remembering, serving, worshiping, praying, serving as a servant, friendship, and surrender."
        ),
        "characters": ["Prahlada Maharaja", "Hiranyakashipu"],
        "location": "Hiranyakashipu's palace school",
        "themes": ["devotion", "teaching", "courage", "bhakti"],
        "source_name": "Bhagavatham repository seed",
        "source_url": "https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/html/sa_bhAgavatapurANa.htm",
        "license": "Source metadata only; full Sanskrit/translation ingestion pending license review",
    },
    {
        "canto": 7,
        "chapter": 8,
        "verse": "17-34",
        "sanskrit": "",
        "transliteration": "",
        "translation": "",
        "summary": (
            "Narasimha appears to protect Prahlada and defeat Hiranyakashipu. The episode should be "
            "rendered as a devotional, symbolic divine victory without graphic violence."
        ),
        "characters": ["Prahlada Maharaja", "Narasimha", "Hiranyakashipu"],
        "location": "Hiranyakashipu's palace hall",
        "themes": ["protection", "divine victory", "devotion", "asura conflict"],
        "source_name": "Bhagavatham repository seed",
        "source_url": "https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/html/sa_bhAgavatapurANa.htm",
        "license": "Source metadata only; full Sanskrit/translation ingestion pending license review",
    },
    {
        "canto": 10,
        "chapter": 6,
        "verse": "1-44",
        "sanskrit": "",
        "transliteration": "",
        "translation": "",
        "summary": (
            "Putana comes to harm baby Krishna, but Krishna protects himself and grants her liberation. "
            "The scene plan should preserve the mythological event without horror or graphic imagery."
        ),
        "characters": ["Sri Krishna", "Mother Yashoda", "Nanda Maharaja", "Putana"],
        "location": "Gokula",
        "themes": ["baby Krishna", "protection", "liberation", "divine grace"],
        "source_name": "Bhagavatham repository seed",
        "source_url": "https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/html/sa_bhAgavatapurANa.htm",
        "license": "Source metadata only; full Sanskrit/translation ingestion pending license review",
    },
    {
        "canto": 10,
        "chapter": 11,
        "verse": "35-59",
        "sanskrit": "",
        "transliteration": "",
        "translation": "",
        "summary": (
            "Krishna and Balarama enter Vrindavan with the cowherd community, establishing the pastoral "
            "setting of forests, cows, Yamuna riverbanks, and devotional childhood pastimes."
        ),
        "characters": ["Sri Krishna", "Balarama", "Mother Yashoda", "Nanda Maharaja"],
        "location": "Vrindavan",
        "themes": ["Vrindavan", "cowherd life", "family", "pastoral devotion"],
        "source_name": "Bhagavatham repository seed",
        "source_url": "https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/html/sa_bhAgavatapurANa.htm",
        "license": "Source metadata only; full Sanskrit/translation ingestion pending license review",
    },
    {
        "canto": 10,
        "chapter": 25,
        "verse": "1-33",
        "sanskrit": "",
        "transliteration": "",
        "translation": "",
        "summary": (
            "Krishna lifts Govardhana Hill to protect the people and cows of Vrindavan from Indra's storm, "
            "showing divine shelter and the beauty of simple devotion."
        ),
        "characters": ["Sri Krishna", "Balarama", "Mother Yashoda", "Nanda Maharaja", "Indra"],
        "location": "Govardhana and Vrindavan",
        "themes": ["protection", "storm", "Govardhana", "devotion", "divine shelter"],
        "source_name": "Bhagavatham repository seed",
        "source_url": "https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/html/sa_bhAgavatapurANa.htm",
        "license": "Source metadata only; full Sanskrit/translation ingestion pending license review",
    },
]


def seed_initial_data(db: Session) -> None:
    seed_characters(db)
    seed_corpus(db)


def seed_characters(db: Session) -> None:
    if db.query(CharacterIdentity).count() > 0:
        return
    for item in INITIAL_CHARACTERS:
        character = CharacterIdentity(
            canonical_name=item["canonical_name"],
            category=item["category"],
            description=item["description"],
            status="seeded",
        )
        db.add(character)
        db.flush()

        aliases = [item["canonical_name"], *item["aliases"]]
        for alias in dict.fromkeys(aliases):
            db.add(
                CharacterAlias(
                    character_id=character.id,
                    alias=alias,
                    alias_normalized=normalize_name(alias),
                    confidence=100,
                )
            )

        for form in item["forms"]:
            db.add(CharacterForm(character_id=character.id, **form))

    db.commit()


def seed_corpus(db: Session) -> None:
    if db.query(CorpusShloka).count() > 0:
        return
    for item in INITIAL_SHLOKAS:
        db.add(CorpusShloka(**item))
    db.commit()
