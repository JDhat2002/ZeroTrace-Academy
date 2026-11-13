"""The twenty most widely spoken languages, by total speakers.

Order follows the usual published ranking: English, Mandarin, Hindi,
Spanish, French, Arabic, Bengali, Portuguese, Russian, Urdu, Indonesian,
German, Japanese, Nigerian Pidgin, Marathi, Telugu, Turkish, Tamil,
Yue Chinese, and Vietnamese. Names are the labels stored on a course.
"""

WORLD_LANGUAGES = (
    ("en", "English"),
    ("zh", "Mandarin Chinese"),
    ("hi", "Hindi"),
    ("es", "Spanish"),
    ("fr", "French"),
    ("ar", "Arabic"),
    ("bn", "Bengali"),
    ("pt", "Portuguese"),
    ("ru", "Russian"),
    ("ur", "Urdu"),
    ("id", "Indonesian"),
    ("de", "German"),
    ("ja", "Japanese"),
    ("pcm", "Nigerian Pidgin"),
    ("mr", "Marathi"),
    ("te", "Telugu"),
    ("tr", "Turkish"),
    ("ta", "Tamil"),
    ("yue", "Yue Chinese"),
    ("vi", "Vietnamese"),
)


def language_names():
    return [name for _, name in WORLD_LANGUAGES]
