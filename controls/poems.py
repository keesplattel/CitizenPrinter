#!/usr/bin/env python3
"""Gedichten over het verloren contact met de natuur, en de weg terug.

Each knob (0..KNOB_MAX) picks a level for one part of the poem:

  knob 1  wildness  where we are: city -> suburb -> edge of town -> the wild
  knob 2  season    winter -> spring -> summer -> autumn
  knob 3  hope      lost -> unsure -> hopeful -> found

The poem has two stanzas: the loss (a place couplet and a season couplet)
and the way back (reaching out, an encounter, the ending). Within a level,
couplets are picked at random, so the same knob settings give a different
poem on every print. Every couplet is a complete sentence that stands on its
own, so any combination reads correctly. The receipt is printed as an image,
so accents are fine; keep lines under ~44 characters so they fit the paper.

Try it:  python3 poems.py 10 10 10     (or --samples for a spread)
"""

import random
import sys

KNOB_MAX = 20
MAX_LINE = 44

TITLES = [
    "VELDNOTITIES",
    "BON VOOR IETS VERLORENS",
    "BEWIJS VAN AANWEZIGHEID",
    "RETOURBELEID",
    "GEVONDEN VOORWERPEN",
    "INVENTARIS",
    "DE WEG TERUG",
    "NOTITIES VAN DE RAND",
    "EEN KLEINE TERUGKEER",
]

# --- Where we are (by wildness) --------------------------------------------
PLACE = [
    # 0: deep city
    (
        [
            "Ik kende ooit de namen van vogels.\nNu ken ik de namen van apps.",
            "Mijn dagen zijn van binnen verlicht,\neen blauw weer achter glas.",
            "Ik woon elf verdiepingen boven\nalles wat met opzet groeit.",
        ],
        [
            "De koelkast zoemt de hele nacht zijn toon,\nen ik noem het gezelschap.",
            "Zelfs de bomen in mijn straat\nzijn genummerd, omheind en moe.",
            "Ik meet de seizoenen in aanbiedingen,\nin de kleur van de koffiebekers.",
        ],
    ),
    # 1: suburb
    (
        [
            "Onze tuin is een vierkantje gras\ndat we maaien voor het iets kan zeggen.",
            "Achter de huizen ligt een sloot\nwaar de kikkers nog hun uren houden.",
            "Elke dag rijd ik langs hetzelfde weiland\nen nooit heb ik erin gestaan.",
        ],
        [
            "De heggen zijn tot stilte geknipt.\nDe goten bewaren wat de hemel stuurt.",
            "'s Nachts wissen de lantaarnpalen\nelke ster, behalve de koppige.",
            "Mijn kinderen kennen de dinosaurussen\nbeter dan de mussen bij het voerhuisje.",
        ],
    ),
    # 2: edge of town
    (
        [
            "De rivier stroomt nog altijd achter\nhet parkeerterrein, onder het lawaai.",
            "De buslijn eindigt bij een bos\ndat ik alleen vanuit het raam ken.",
            "Ik loop door het park op het betegelde pad,\nhet pad dat zegt waar ik heen moet.",
        ],
        [
            "Ik hoor de rivier alleen als het stil is,\nen het is bijna nooit stil.",
            "De eiken daar zijn ouder dan de stad\nen lijken het niet erg te vinden.",
            "Ik draag mijn telefoon als een lantaarn,\nook al is het helemaal niet donker.",
        ],
    ),
    # 3: the wild
    (
        [
            "Ik kwam hier naar het verste veld\nmet niets dan een geleende kaart.",
            "Het bos begint waar het bereik ophoudt.\nZo had ik het niet gepland.",
            "Hierboven heeft de wind geen adres\nen verliest het pad zich in de heide.",
        ],
        [
            "Toch grijp ik steeds naar mijn zak,\nnaar een licht dat er niet is.",
            "Zelfs hier hoor ik de snelweg,\neen grijze rivier in de verte.",
            "Ik weet dat ik me thuis zou moeten voelen.\nIk voel me een gast die te laat kwam.",
        ],
    ),
]

# --- The season (by season) ------------------------------------------------
# Written to work in any place, from city to forest.
SEASON = [
    # 0: winter
    (
        [
            "Het is winter. De vorst heeft iets\ngeschreven op elk raam.",
            "De kou komt binnen als een oude vriend\ndie nooit heeft leren kloppen.",
            "Vannacht viel er sneeuw, en die bedekte\nhet verschil tussen de dingen.",
        ],
        [
            "De vogels die bleven zijn klein en luid;\nze praten het licht in leven.",
            "Onder het ijs beweegt het water,\ngeduldig, op weg naar ergens.",
            "De kale bomen tonen hun hele ontwerp,\nhet ontwerp dat de zomer verbergt.",
        ],
    ),
    # 1: spring
    (
        [
            "Het is lente. Er is iets groens\ndoor het asfalt gebroken.",
            "De regen komt in korte zinnen\nen de aarde beantwoordt ze allemaal.",
            "De bloesem kwam ineens tevoorschijn,\nalsof iemand haar naam had geroepen.",
        ],
        [
            "De merel begint al voor de dageraad.\nHij repeteert voor niemand.",
            "Alles begint opnieuw\nzonder om toestemming te vragen.",
            "De modder ruikt naar een herinnering\ndie ik te jong ben om te hebben.",
        ],
    ),
    # 2: summer
    (
        [
            "Het is zomer, en het lange licht\nblijft tot tien uur op de daken hangen.",
            "De hitte ligt op de stoep\nen het gras wordt goud van het wachten.",
            "De gierzwaluwen zijn terug en krijsen\nhun dunne cirkels boven de daken.",
        ],
        [
            "Bijen bewerken de klaver in de berm\ndie de maaimachine heeft gespaard.",
            "Bij schemer vult de lucht zich met insecten\nen de vleermuizen komen ze lezen.",
            "In het westen bouwt een onweer zich op,\nals een gedachte die ik bijna heb.",
        ],
    ),
    # 3: autumn
    (
        [
            "Het is herfst. De bomen laten los\nwat ze het hele jaar vasthielden.",
            "De ganzen trekken over in hun letters\nen spellen een woord voor vertrekken.",
            "Regen op de ramen, regen op de bladeren,\nde hele wereld wordt zachter.",
        ],
        [
            "Paddenstoelen rijzen op in de nacht,\nalsof ze een gerucht hebben gehoord.",
            "Het licht valt laag en goudkleurig\nen vertrekt elke dag wat eerder.",
            "De geur van natte aarde bereikt me,\nzelfs hier, zelfs nu.",
        ],
    ),
]

# --- Reaching out (by wildness) --------------------------------------------
REACH = [
    # 0: deep city
    [
        "Vandaag legde ik mijn hand plat\ntegen de bast van de enige straatboom.",
        "Ik zette het raam wijd open\nen liet het weer de kamer in.",
        "Ik liet mijn telefoon op tafel liggen\nen liep tot de winkels ophielden.",
    ],
    # 1: suburb
    [
        "Vandaag deed ik mijn schoenen uit\nin het natte gras bij het station.",
        "Ik knielde in de tuin\nen duwde mijn handen in de aarde.",
        "Ik volgde de sloot langs de hekken\ntot waar het riet begint.",
    ],
    # 2: edge of town
    [
        "Vandaag stapte ik van het pad af\nen gaf mijn schoenen aan de modder.",
        "Ik zat onder de oudste eik\ntot mijn adem trager werd, net als de zijne.",
        "Ik volgde het geluid van de rivier\ntot ik de rivier vond.",
    ],
    # 3: the wild
    [
        "Vandaag ging ik liggen in de heide\nen liet de lucht verdergaan zonder mij.",
        "Ik dronk uit de beek met mijn handen,\nzoals ik dat ooit gedaan moet hebben.",
        "Ik zette de kaart uit\nen liep op de vorm van de heuvels.",
    ],
]

# --- The ending (by hope) --------------------------------------------------
# Slot 1 is an encounter, slot 2 is the closing couplet.
ENDING = [
    # 0: lost
    (
        [
            "Een kraai bekeek me vanaf de draad\nen besloot dat ik niets was.",
            "Vlakbij riep een vogel, één keer,\nen ik kan je niet zeggen welke.",
            "Er bewoog iets in het gras\nen het was weg voor ik me omdraaide.",
        ],
        [
            "Ik ging naar huis en deed het licht aan.\nHet scherm was blij me te zien.",
            "Ik weet de woorden niet meer.\nIk weet niet of er woorden waren.",
            "Wat het ook was, het was niet voor mij.\nIk liep terug naar het lawaai.",
        ],
    ),
    # 1: unsure
    (
        [
            "Toen zei een merel, zo dichtbij\ndat ik hem kon aanraken, iets eenvoudigs.",
            "Een vos stak het pad over\nen haastte zich niet, en bleef niet.",
            "De wind ging door de bladeren\nmet een geluid als ingehouden adem.",
        ],
        [
            "Ik verstond het woord niet.\nIk denk dat ik morgen terugkom.",
            "Ik ken de taal nog niet,\nmaar ik weet dat ze gesproken wordt.",
            "Er was niets opgelost.\nMaar er was iets van het slot.",
        ],
    ),
    # 2: hopeful
    (
        [
            "Toen zong een winterkoning,\nniet groter dan een gedachte.",
            "Een ree hief haar kop op\nen hield een tijdje mijn blik vast.",
            "Het licht viel door de takken\nen ging liggen op mijn handen.",
        ],
        [
            "Ik verstond het woord niet.\nIk ben het opnieuw aan het leren.",
            "Ik zei niets terug,\nen dat was het juiste antwoord.",
            "Even wist ik hoe het heette,\nen dat het mij altijd al kende.",
        ],
    ),
    # 3: found
    (
        [
            "Toen werd de hele heg wakker van vogels,\nen elke vogel sprak.",
            "Een reiger steeg op uit het water,\nlangzaam als een deur die opengaat.",
            "Het begon te regenen, en ik liet het toe,\nen het voelde als gekend worden.",
        ],
        [
            "Ik ben hier geen bezoeker.\nDat ben ik nooit geweest.",
            "Ik nam de lange weg naar huis,\nen thuis was groter dan voorheen.",
            "De wereld sprak al die tijd.\nIk was alleen gestopt met luisteren.",
        ],
    ),
]


def level(value: int, levels: int) -> int:
    """Map a knob value 0..KNOB_MAX onto 0..levels-1."""
    value = max(0, min(KNOB_MAX, value))
    return min(value * levels // (KNOB_MAX + 1), levels - 1)


def poem(values: list[int], rng: random.Random | None = None) -> tuple[str, list[list[str]]]:
    """Write a poem for knob values [wildness, season, hope].

    Returns the title and the stanzas, each a list of lines.
    """
    rng = rng or random.Random()
    wildness, season, hope = values
    w = level(wildness, len(PLACE))
    s = level(season, len(SEASON))
    h = level(hope, len(ENDING))

    stanzas = [
        [rng.choice(PLACE[w][0] + PLACE[w][1]), rng.choice(SEASON[s][0] + SEASON[s][1])],
        [rng.choice(REACH[w]), rng.choice(ENDING[h][0]), rng.choice(ENDING[h][1])],
    ]
    title = rng.choice(TITLES)
    return title, ["\n".join(stanza).split("\n") for stanza in stanzas]


def compose(values: list[int], rng: random.Random | None = None) -> str:
    title, stanzas = poem(values, rng)
    body = "\n\n".join("\n".join(stanza) for stanza in stanzas)
    return f"{title}\n\n{body}"


def _check_banks() -> None:
    """Every couplet has two lines, each short enough for the paper."""
    banks = [*REACH]
    for group in (PLACE, SEASON, ENDING):
        for slots in group:
            banks.extend(slots)
    for bank in banks:
        for couplet in bank:
            lines = couplet.split("\n")
            assert len(lines) == 2, f"not a couplet: {couplet!r}"
            for line in lines:
                assert len(line) <= MAX_LINE, f"too long: {line!r}"


if __name__ == "__main__":
    _check_banks()
    if sys.argv[1:] == ["--samples"]:
        for values in ([0, 0, 0], [7, 7, 7], [14, 14, 14], [20, 20, 20]):
            print(compose(values), end="\n\n\n")
    else:
        knobs = [int(v) for v in sys.argv[1:4]] or [10, 10, 10]
        print(compose(knobs))
