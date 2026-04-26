PRESETS = [
    {
        "id": "youtube_standard",
        "name": "YouTube Standard",
        "max_words_per_line": 8,
        "max_lines_per_block": 1,
        "max_chars_per_line": 52,
        "max_words_per_cue": 10,
        "min_duration": 1.5,
        "max_duration": 5.0,
    },
    {
        "id": "shorts_reels",
        "name": "Shorts/Reels",
        "max_words_per_line": 4,
        "max_lines_per_block": 1,
        "max_chars_per_line": 30,
        "max_words_per_cue": 5,
        "min_duration": 1.1,
        "max_duration": 3.0,
    },
    {
        "id": "dense_transcript",
        "name": "Dense Transcript",
        "max_words_per_line": 8,
        "max_lines_per_block": 2,
        "max_chars_per_line": 48,
        "max_words_per_cue": 16,
        "min_duration": 1.8,
        "max_duration": 7.0,
    },
]

PRESETS_BY_ID = {p["id"]: p for p in PRESETS}
