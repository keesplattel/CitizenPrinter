#!/usr/bin/env python3
"""Poems about losing touch with nature, and finding the way back.

Each knob (0..KNOB_MAX) picks a level for one part of the poem:

  knob 1  wildness  where we are: city -> suburb -> edge of town -> the wild
  knob 2  season    winter -> spring -> summer -> autumn
  knob 3  hope      lost -> unsure -> hopeful -> found

Within a level, couplets are picked at random, so the same knob settings
give a different poem on every print. Every couplet is a complete sentence,
so any combination reads correctly. Keep lines under ~42 characters (80mm
paper fits 48) and stick to plain ASCII: no curly quotes or dashes.

Try it:  python3 poems.py 10 10 10     (or --samples for a spread)
"""

import random
import sys
from datetime import datetime

KNOB_MAX = 20
WIDTH = 48

TITLES = [
    "FIELD NOTES",
    "RECEIPT FOR A LOST THING",
    "PROOF OF PRESENCE",
    "RETURN POLICY",
    "LOST AND FOUND",
    "INVENTORY",
    "THE WAY BACK",
    "NOTES FROM THE EDGE",
    "A SMALL RETURN",
]

# --- Stanza 1: where we are (by wildness) ---------------------------------
# Two slots per level; one couplet is drawn from each.
PLACE = [
    # 0: deep city
    (
        [
            "I knew the names of birds once.\nNow I know the names of apps.",
            "My days are lit from the inside,\na blue weather behind glass.",
            "I live eleven floors above\nanything that grows on purpose.",
        ],
        [
            "The fridge hums its one long note\nall night, and I call it company.",
            "Even the trees on my street\nare numbered, and fenced, and tired.",
            "I measure the seasons in sales,\nin the colour of the coffee cups.",
        ],
    ),
    # 1: suburb
    (
        [
            "Our garden is a square of lawn\nwe cut before it can say anything.",
            "There is a ditch behind the houses\nwhere the frogs still keep their hours.",
            "I drive past the same field daily\nand have never once stood in it.",
        ],
        [
            "The hedges are trimmed into silence.\nThe gutters keep what the sky sends.",
            "At night the streetlights erase\nevery star but the stubborn ones.",
            "My children know the dinosaurs\nbetter than the sparrows at the feeder.",
        ],
    ),
    # 2: edge of town
    (
        [
            "The river still runs behind\nthe car park, under the noise.",
            "The bus line ends at a wood\nI have only seen from the window.",
            "I walk the park on the paved path,\nthe one that tells me where to go.",
        ],
        [
            "I hear it only when the traffic stops,\nwhich is almost never.",
            "The oaks there are older than the town\nand do not seem to mind it.",
            "I carry my phone like a lantern\nthough it is not dark at all.",
        ],
    ),
    # 3: the wild
    (
        [
            "I came out here to the far field\nwith nothing but a borrowed map.",
            "The forest starts where the signal ends.\nI did not plan it that way.",
            "Up here the wind has no address\nand the path forgets itself in heather.",
        ],
        [
            "Still I keep reaching for my pocket,\nfor a light that is not there.",
            "Even here I hear the motorway,\na grey river in the distance.",
            "I know I should feel at home.\nI feel like a guest who came late.",
        ],
    ),
]

# --- Stanza 2: the season (by season) -------------------------------------
# Written to work in any place, from city to forest.
SEASON = [
    # 0: winter
    (
        [
            "It is winter. The frost has written\nsomething on every window.",
            "The cold comes in like an old friend\nwho never learned to knock.",
            "Snow fell overnight and covered\nthe difference between things.",
        ],
        [
            "The birds that stayed are small and loud,\nkeeping the light alive by talking.",
            "Under the ice the water moves,\npatient, with somewhere to be.",
            "The bare trees show their whole design,\nthe one that summer hides.",
        ],
    ),
    # 1: spring
    (
        [
            "It is spring. Something green\nhas broken through the asphalt.",
            "The rain arrives in short sentences\nand the soil answers every one.",
            "The blossom came out all at once,\nas if someone had called its name.",
        ],
        [
            "The blackbird starts before the dawn,\nrehearsing for nobody.",
            "Everything is beginning again\nwithout asking for permission.",
            "The mud smells like a memory\nI am not old enough to have.",
        ],
    ),
    # 2: summer
    (
        [
            "It is summer, and the long light\nlingers on the rooftops until ten.",
            "The heat sits on the pavement\nand the grass goes gold with waiting.",
            "The swifts are back, screaming\ntheir thin circles over the roofs.",
        ],
        [
            "Bees work the clover in the verges\nthat the mowers somehow missed.",
            "At dusk the air fills up with insects\nand the bats come out to read them.",
            "A thunderstorm builds in the west\nlike a thought I almost have.",
        ],
    ),
    # 3: autumn
    (
        [
            "It is autumn. The trees are letting go\nof everything they held all year.",
            "The geese go over in their letters,\nspelling out a word for leaving.",
            "Rain on the windows, rain on the leaves,\nthe whole world softening.",
        ],
        [
            "Mushrooms rise in the night\nlike they have heard a rumour.",
            "The light comes low and golden\nand leaves earlier each day.",
            "The smell of wet earth reaches me\neven here, even now.",
        ],
    ),
]

# --- Stanza 3: reaching out (action by wildness, then a shared turn) -------
REACH = [
    # 0: deep city
    [
        "Today I put my hand flat\non the bark of the one street tree.",
        "I opened the window wide\nand let the weather into the room.",
        "I left my phone on the table\nand walked until the shops ran out.",
    ],
    # 1: suburb
    [
        "Today I took my shoes off\nin the wet grass by the station.",
        "I knelt down in the garden\nand pushed my hands into the dirt.",
        "I followed the ditch past the fences\nto where the reeds begin.",
    ],
    # 2: edge of town
    [
        "Today I stepped off the paved path\nand let the mud have my shoes.",
        "I sat under the oldest oak\nuntil my breathing slowed to match it.",
        "I followed the sound of the river\nuntil I found the river.",
    ],
    # 3: the wild
    [
        "Today I lay down in the heather\nand let the sky go on without me.",
        "I drank from the stream with my hands\nthe way I must have once.",
        "I turned off the map\nand walked by the shape of the hills.",
    ],
]

TURN = [
    "I waited like a question\nthe ground forgot to answer.",
    "For a long time nothing happened.\nThat was the first lesson.",
    "My body remembered something\nmy mind had filed away.",
    "I felt foolish, and then less foolish,\nand then nothing but the air.",
    "It is harder than it sounds,\nto be somewhere completely.",
    "I did not know what I was listening for.\nI listened anyway.",
]

# --- Stanza 4: the ending (by hope) ---------------------------------------
# Slot 1 is an encounter, slot 2 is the closing couplet.
ENDING = [
    # 0: lost
    (
        [
            "A crow watched me from the wire\nand decided I was nothing.",
            "A bird called once, close by,\nand I could not tell you which.",
            "Something moved in the grass\nand was gone before I turned.",
        ],
        [
            "I went home and turned on the lights.\nThe screen was glad to see me.",
            "I don't remember the words.\nI'm not sure there were any.",
            "Whatever it was, it was not for me.\nI walked back to the noise.",
        ],
    ),
    # 1: unsure
    (
        [
            "Then a blackbird, close enough\nto touch, said something plain.",
            "A fox crossed the path ahead\nand did not hurry, and did not stay.",
            "The wind came through the leaves\nwith a sound like a held breath.",
        ],
        [
            "I didn't catch the word.\nI think I'll come back tomorrow.",
            "I don't know the language yet,\nbut I know it's being spoken.",
            "Nothing was fixed.\nBut something was unlocked.",
        ],
    ),
    # 2: hopeful
    (
        [
            "Then a wren, no bigger than a thought,\nsang from the bramble at my side.",
            "A deer lifted its head\nand held my gaze for a while.",
            "The light came through the branches\nand lay down on my hands.",
        ],
        [
            "I didn't catch the word.\nI'm learning it again.",
            "I said nothing back,\nwhich was the right reply.",
            "I knew, for a moment, its name,\nand that it had always known mine.",
        ],
    ),
    # 3: found
    (
        [
            "Then the whole hedge woke with birds,\nand every one was speaking.",
            "A heron rose up from the water\nslow as a door opening.",
            "The rain began, and I let it,\nand it felt like being known.",
        ],
        [
            "I am not a visitor here.\nI never was.",
            "I took the long way home,\nand home was larger than before.",
            "The world was speaking all along.\nI had only stopped listening.",
        ],
    ),
]

WILDNESS_NAMES = ["city", "suburb", "edge", "wild"]
SEASON_NAMES = ["winter", "spring", "summer", "autumn"]
HOPE_NAMES = ["lost", "unsure", "hopeful", "found"]


def level(value: int, levels: int) -> int:
    """Map a knob value 0..KNOB_MAX onto 0..levels-1."""
    value = max(0, min(KNOB_MAX, value))
    return min(value * levels // (KNOB_MAX + 1), levels - 1)


def compose(values: list[int], rng: random.Random | None = None) -> str:
    """Write a poem for knob values [wildness, season, hope]."""
    rng = rng or random.Random()
    wildness, season, hope = values
    w = level(wildness, len(PLACE))
    s = level(season, len(SEASON))
    h = level(hope, len(ENDING))

    stanzas = [
        [rng.choice(PLACE[w][0]), rng.choice(PLACE[w][1])],
        [rng.choice(SEASON[s][0]), rng.choice(SEASON[s][1])],
        [rng.choice(REACH[w]), rng.choice(TURN)],
        [rng.choice(ENDING[h][0]), rng.choice(ENDING[h][1])],
    ]
    title = rng.choice(TITLES)
    body = "\n\n".join("\n".join(stanza) for stanza in stanzas)
    return f"{title}\n\n{body}"


def footer(values: list[int]) -> str:
    wildness, season, hope = values
    settings = (
        f"{WILDNESS_NAMES[level(wildness, 4)]} {wildness}"
        f" / {SEASON_NAMES[level(season, 4)]} {season}"
        f" / {HOPE_NAMES[level(hope, 4)]} {hope}"
    )
    return "\n".join(["-" * WIDTH, settings, datetime.now().strftime("%Y-%m-%d %H:%M")])


def receipt(values: list[int], rng: random.Random | None = None) -> str:
    return f"{compose(values, rng)}\n\n{footer(values)}"


def _check_banks() -> None:
    """Every line fits the paper and is plain ASCII."""
    banks = [TITLES, TURN, *REACH]
    for group in (PLACE, SEASON, ENDING):
        for slots in group:
            banks.extend(slots)
    for bank in banks:
        for couplet in bank:
            for line in couplet.split("\n"):
                assert len(line) <= WIDTH, f"too long: {line!r}"
                assert line.isascii(), f"not ASCII: {line!r}"


if __name__ == "__main__":
    _check_banks()
    if sys.argv[1:] == ["--samples"]:
        for values in ([0, 0, 0], [7, 7, 7], [14, 14, 14], [20, 20, 20]):
            print(receipt(values), end="\n\n\n")
    else:
        knobs = [int(v) for v in sys.argv[1:4]] or [10, 10, 10]
        print(receipt(knobs))
