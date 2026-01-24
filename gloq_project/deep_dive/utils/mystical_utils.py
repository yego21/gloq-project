def get_page_range(current_page, total_pages, delta=2):
    """
    Helper function to generate smart page range for pagination.
    Shows first page, last page, current page and delta pages around it.
    """
    if total_pages <= 7:
        return list(range(1, total_pages + 1))

    pages = set()
    pages.add(1)  # Always show first page
    pages.add(total_pages)  # Always show last page

    # Add current page and delta pages around it
    for i in range(max(1, current_page - delta), min(total_pages + 1, current_page + delta + 1)):
        pages.add(i)

    # Convert to sorted list
    pages_list = sorted(pages)

    # Add ellipsis where there are gaps
    result = []
    prev = 0
    for page in pages_list:
        if prev and page - prev > 1:
            result.append('...')
        result.append(page)
        prev = page

    return result

def generate_planet_interpretation(
    planet_name,
    sign,
    house,
    degree,
    is_retrograde,
    aspects
):
    """
    Generates a comprehensive astrological interpretation for a planetary placement.
    Designed for extensibility: natal, transit, synastry, or report generation.
    """

    # =========================
    # CORE ASTROLOGICAL DATABASE
    # =========================

    PLANET_DATA = {
        'Sun': {
            'core': "The Sun represents identity, vitality, ego, and life purpose.",
            'function': "how you shine, create meaning, and express your essential self",
            'keywords': ['Identity', 'Vitality', 'Purpose', 'Willpower', 'Ego']
        },
        'Moon': {
            'core': "The Moon governs emotions, instincts, and subconscious patterns.",
            'function': "how you feel, nurture, and seek emotional security",
            'keywords': ['Emotions', 'Instincts', 'Needs', 'Security', 'Memory']
        },
        'Mercury': {
            'core': "Mercury rules thinking, communication, and perception.",
            'function': "how you process information and express ideas",
            'keywords': ['Communication', 'Logic', 'Learning', 'Speech', 'Mind']
        },
        'Venus': {
            'core': "Venus governs love, values, attraction, and harmony.",
            'function': "how you relate, love, and find pleasure",
            'keywords': ['Love', 'Values', 'Beauty', 'Relationships', 'Pleasure']
        },
        'Mars': {
            'core': "Mars governs action, drive, desire, and assertion.",
            'function': "how you pursue goals and assert your will",
            'keywords': ['Action', 'Drive', 'Passion', 'Courage', 'Assertion']
        },
        'Jupiter': {
            'core': "Jupiter represents growth, wisdom, and expansion.",
            'function': "how you seek meaning, opportunity, and faith",
            'keywords': ['Growth', 'Wisdom', 'Luck', 'Beliefs', 'Expansion']
        },
        'Saturn': {
            'core': "Saturn rules discipline, structure, and karmic lessons.",
            'function': "how you build stability through responsibility",
            'keywords': ['Structure', 'Discipline', 'Responsibility', 'Boundaries', 'Maturity']
        },
        'Uranus': {
            'core': "Uranus represents innovation, rebellion, and awakening.",
            'function': "how you seek freedom and express uniqueness",
            'keywords': ['Innovation', 'Change', 'Freedom', 'Rebellion', 'Awakening']
        },
        'Neptune': {
            'core': "Neptune governs spirituality, dreams, and transcendence.",
            'function': "how you dissolve boundaries and seek higher truth",
            'keywords': ['Spirituality', 'Dreams', 'Illusion', 'Compassion', 'Mysticism']
        },
        'Pluto': {
            'core': "Pluto rules transformation, power, and regeneration.",
            'function': "how you confront shadow and undergo deep change",
            'keywords': ['Transformation', 'Power', 'Intensity', 'Rebirth', 'Depth']
        },
        'Chiron': {
            'core': "Chiron represents the wounded healer archetype.",
            'function': "where healing, teaching, and integration occur",
            'keywords': ['Healing', 'Wound', 'Wisdom', 'Integration', 'Teaching']
        },
        'North Node': {
            'core': "The North Node indicates evolutionary growth and soul direction.",
            'function': "where your soul is learning to grow",
            'keywords': ['Destiny', 'Growth', 'Purpose', 'Evolution', 'Future']
        },
        'South Node': {
            'core': "The South Node reflects past patterns and karmic comfort zones.",
            'function': "where habits must be released or balanced",
            'keywords': ['Past', 'Karma', 'Habits', 'Release', 'Familiarity']
        },
        'Lilith': {
            'core': "Lilith represents raw instinct, shadow, and primal autonomy.",
            'function': "how untamed power and suppressed truth emerge",
            'keywords': ['Shadow', 'Power', 'Sexuality', 'Autonomy', 'Rebellion']
        }
    }

    SIGN_DATA = {
        sign: {
            'expression': f"{sign} colors this planet with its distinctive qualities.",
            'mode': "how the planetary energy is expressed through temperament and style"
        }
    }

    HOUSE_DATA = {
        1: "identity, self-image, and personal expression",
        2: "values, resources, and self-worth",
        3: "communication, learning, and mindset",
        4: "home, roots, and emotional foundation",
        5: "creativity, joy, and self-expression",
        6: "work, health, and daily routines",
        7: "partnerships, marriage, and cooperation",
        8: "transformation, intimacy, and shared resources",
        9: "beliefs, philosophy, and higher learning",
        10: "career, reputation, and public life",
        11: "friendships, networks, and aspirations",
        12: "subconscious, spirituality, and solitude"
    }

    RETROGRADE_MEANING = (
        "The retrograde motion internalizes this planet’s energy, "
        "indicating reflection, revision, and karmic processing."
    )

    # =========================
    # INTERPRETATION ASSEMBLY
    # =========================

    planet = PLANET_DATA.get(planet_name, {
        'core': f"{planet_name} represents a unique energetic influence.",
        'function': "how this planetary force operates",
        'keywords': ['Energy', 'Influence']
    })

    interpretation_parts = []

    # Core meaning
    interpretation_parts.append(
        f"{planet['core']} It describes {planet['function']}."
    )

    # Sign expression
    interpretation_parts.append(
        f"In {sign}, this energy is expressed through the qualities and style of {sign}."
    )

    # House placement
    if house:
        house_theme = HOUSE_DATA.get(house, "life experience")
        interpretation_parts.append(
            f"Placed in the {house}th house, this planet manifests in matters of {house_theme}."
        )

    # Degree emphasis (open-ended hook)
    if degree is not None:
        interpretation_parts.append(
            f"At {degree}°, this placement carries a specific emphasis that can refine timing, intensity, or mastery."
        )

    # Retrograde influence
    if is_retrograde:
        interpretation_parts.append(f"℞ {RETROGRADE_MEANING}")

    # Aspect synthesis
    aspect_count = len(aspects) if aspects else 0
    if aspect_count > 0:
        interpretation_parts.append(
            f"This planet forms {aspect_count} significant aspect(s), "
            "interweaving its expression with other planetary forces in the chart."
        )

    personal_interpretation = " ".join(interpretation_parts)

    # =========================
    # FINAL OUTPUT
    # =========================

    return {
        'planet': planet_name,
        'sign': sign,
        'house': house,
        'degree': degree,
        'is_retrograde': is_retrograde,
        'aspect_count': aspect_count,
        'keywords': planet['keywords'],
        'core_meaning': planet['core'],
        'personal_interpretation': personal_interpretation
    }


def generate_aspect_interpretation(planet1, planet2, aspect_type, orb):
    """
    Generates a comprehensive interpretation for a specific aspect between two planets.
    Returns detailed, personalized meaning based on the planetary combination.
    """

    # =========================
    # PLANET ARCHETYPES
    # =========================

    PLANET_ARCHETYPES = {
        'Sun': {'essence': 'core identity', 'verb': 'shine', 'energy': 'vital force'},
        'Moon': {'essence': 'emotional nature', 'verb': 'feel', 'energy': 'instinctual response'},
        'Mercury': {'essence': 'mental patterns', 'verb': 'think and communicate', 'energy': 'intellectual processing'},
        'Venus': {'essence': 'values and attractions', 'verb': 'love and appreciate', 'energy': 'relational harmony'},
        'Mars': {'essence': 'drive and desire', 'verb': 'act and assert', 'energy': 'motivational force'},
        'Jupiter': {'essence': 'expansion and beliefs', 'verb': 'grow and explore', 'energy': 'optimistic faith'},
        'Saturn': {'essence': 'structure and limits', 'verb': 'commit and discipline',
                   'energy': 'crystallizing maturity'},
        'Uranus': {'essence': 'innovation and freedom', 'verb': 'awaken and liberate',
                   'energy': 'revolutionary change'},
        'Neptune': {'essence': 'spirituality and dreams', 'verb': 'dissolve and transcend',
                    'energy': 'mystical connection'},
        'Pluto': {'essence': 'transformation and power', 'verb': 'transform and regenerate',
                  'energy': 'intense rebirth'},
        'Chiron': {'essence': 'wound and healing', 'verb': 'heal and teach', 'energy': 'wounded wisdom'},
        'North Node': {'essence': 'evolutionary direction', 'verb': 'evolve toward', 'energy': 'karmic growth'},
        'South Node': {'essence': 'past patterns', 'verb': 'release from', 'energy': 'karmic familiarity'},
        'Lilith': {'essence': 'shadow power', 'verb': 'reclaim autonomy', 'energy': 'primal authenticity'},
    }

    # =========================
    # ASPECT-SPECIFIC DYNAMICS
    # =========================

    ASPECT_DYNAMICS = {
        'Conjunction': {
            'relationship': 'merges',
            'dynamic': 'These energies blend into a unified force, amplifying each other',
            'experience': 'You experience these planets as inseparable—they work as one',
            'integration': 'The key is learning to express both energies simultaneously without one overpowering the other',
        },
        'Opposition': {
            'relationship': 'polarizes',
            'dynamic': 'These energies pull in opposite directions, creating conscious awareness',
            'experience': 'You may feel torn between these two needs, often seeing one reflected in others',
            'integration': 'The key is finding the middle ground and integrating both perspectives',
        },
        'Trine': {
            'relationship': 'harmonizes with',
            'dynamic': 'These energies flow together naturally and effortlessly',
            'experience': 'This combination feels innate—talents here come easily to you',
            'integration': 'The key is actively developing these natural gifts rather than taking them for granted',
        },
        'Square': {
            'relationship': 'challenges',
            'dynamic': 'These energies create internal friction that demands action',
            'experience': 'You feel motivated tension between these areas, pushing you to grow',
            'integration': 'The key is using this dynamic tension as fuel for achievement and mastery',
        },
        'Sextile': {
            'relationship': 'cooperates with',
            'dynamic': 'These energies support each other when you take initiative',
            'experience': 'Opportunities arise naturally, but require your conscious engagement',
            'integration': 'The key is actively pursuing the supportive connections this aspect offers',
        },
        'Quincunx': {
            'relationship': 'awkwardly connects with',
            'dynamic': 'These energies don\'t naturally understand each other, requiring constant adjustment',
            'experience': 'You feel a persistent sense of unease, as if these needs speak different languages',
            'integration': 'The key is developing creative flexibility and accepting the need for ongoing adaptation',
        },
    }

    # =========================
    # PLANETARY COMBINATIONS
    # =========================

    def get_combination_meaning(p1, p2, aspect):
        """Generate specific interpretation for planet pair"""

        # Normalize planet order for lookup
        combo_key = tuple(sorted([p1, p2]))

        COMBINATIONS = {
            ('Sun', 'Moon'): {
                'essence': 'conscious identity with emotional needs',
                'Conjunction': 'Your sense of self and emotional nature are unified—what you want aligns with what you need.',
                'Opposition': 'You balance between your personal goals (Sun) and emotional security (Moon), often seeing one in relationships.',
                'Trine': 'Your ego and emotions work harmoniously together—you naturally express feelings in healthy ways.',
                'Square': 'Internal tension between what you want to be and what you need emotionally drives self-development.',
                'Sextile': 'Opportunities to integrate your identity with emotional intelligence through conscious effort.',
            },
            ('Sun', 'Mercury'): {
                'essence': 'identity with mental expression',
                'Conjunction': 'Your sense of self and thinking are merged—you think about yourself and express your identity mentally.',
                'Opposition': 'Objectivity about your identity; you can step back and think about yourself clearly.',
                'Trine': 'Natural ability to articulate who you are and communicate your authentic self.',
                'Square': 'Tension between ego and logic drives you to refine self-expression and communication.',
                'Sextile': 'Opportunities to develop communication skills that authentically represent your identity.',
            },
            ('Sun', 'Venus'): {
                'essence': 'identity with values and love',
                'Conjunction': 'Who you are and what you love are inseparable—your identity IS your values and relationships.',
                'Opposition': 'You seek yourself through relationships, learning self-worth through others.',
                'Trine': 'Natural charm and ease in expressing yourself lovingly; creativity flows effortlessly.',
                'Square': 'Creative tension between ego and relationships drives artistic development and self-worth work.',
                'Sextile': 'Opportunities to develop talents in art, relationships, or self-expression through practice.',
            },
            ('Sun', 'Mars'): {
                'essence': 'identity with action and desire',
                'Conjunction': 'Your will and action are one—you naturally assert yourself with confidence.',
                'Opposition': 'You learn assertiveness through others; partners may reflect your warrior energy.',
                'Trine': 'Natural courage and ability to pursue goals confidently without internal conflict.',
                'Square': 'Dynamic tension between ego and action creates ambitious drive and competitive spirit.',
                'Sextile': 'Opportunities to develop confidence and assertiveness through taking action.',
            },
            ('Sun', 'Jupiter'): {
                'essence': 'identity with expansion and faith',
                'Conjunction': 'Your identity expands naturally—you radiate optimism and philosophical confidence.',
                'Opposition': 'You grow through relationships and see your potential reflected in others.',
                'Trine': 'Natural luck and optimism; doors open easily and faith in yourself is strong.',
                'Square': 'Over-expansion drives growth; learning to balance confidence with realistic self-assessment.',
                'Sextile': 'Opportunities for growth and learning when you actively pursue knowledge and experience.',
            },
            ('Sun', 'Saturn'): {
                'essence': 'identity with structure and limits',
                'Conjunction': 'Your identity is shaped by discipline, responsibility, and earned authority.',
                'Opposition': 'You learn self-mastery through relationships and external structures.',
                'Trine': 'Natural ability to build lasting achievements through patient, disciplined effort.',
                'Square': 'Father issues or authority struggles drive you to develop authentic inner authority.',
                'Sextile': 'Opportunities to develop maturity and discipline through consistent effort.',
            },
            ('Sun', 'Uranus'): {
                'essence': 'identity with innovation and freedom',
                'Conjunction': 'Your identity IS uniqueness—you naturally rebel against convention and awaken others.',
                'Opposition': 'Freedom needs clash with ego; partners may be unpredictable or awakening.',
                'Trine': 'Natural ability to innovate and express your unique genius without internal conflict.',
                'Square': 'Revolutionary tension pushes you toward breakthrough self-expression despite disruption.',
                'Sextile': 'Opportunities to develop your unique gifts through experimentation and risk-taking.',
            },
            ('Sun', 'Neptune'): {
                'essence': 'identity with spirituality and dreams',
                'Conjunction': 'Your ego dissolves into universal consciousness—artist, mystic, or both.',
                'Opposition': 'You seek transcendence through relationships; boundaries with others blur easily.',
                'Trine': 'Natural creative and spiritual gifts flow effortlessly into self-expression.',
                'Square': 'Identity confusion or illusion pushes you toward spiritual clarity and creative expression.',
                'Sextile': 'Opportunities to develop spiritual or creative identity through dedicated practice.',
            },
            ('Sun', 'Pluto'): {
                'essence': 'identity with transformation and power',
                'Conjunction': 'Your identity undergoes constant death and rebirth—you wield transformative power.',
                'Opposition': 'You meet your shadow through relationships; others catalyze your transformation.',
                'Trine': 'Natural ability to transform yourself and wield personal power authentically.',
                'Square': 'Power struggles and ego death drive profound self-transformation.',
                'Sextile': 'Opportunities to develop personal power and transformative capacity through intensity.',
            },
            ('Moon', 'Mercury'): {
                'essence': 'emotions with mental expression',
                'Conjunction': 'Feelings and thoughts merge—you talk about emotions easily but may over-rationalize them.',
                'Opposition': 'You balance feeling with thinking; may intellectualize emotions or feel your thoughts.',
                'Trine': 'Natural emotional intelligence—you articulate feelings clearly and think empathetically.',
                'Square': 'Tension between head and heart drives development of emotional communication skills.',
                'Sextile': 'Opportunities to develop emotional literacy through journaling, therapy, or communication.',
            },
            ('Moon', 'Venus'): {
                'essence': 'emotions with values and love',
                'Conjunction': 'Your emotional needs and what you love are unified—you need love to feel secure.',
                'Opposition': 'You balance personal comfort with relationship harmony; may attract nurturing partners.',
                'Trine': 'Natural emotional warmth and ease in relationships; you nurture through love.',
                'Square': 'Tension between security needs and relationship desires drives emotional maturity.',
                'Sextile': 'Opportunities to cultivate emotional harmony and loving relationships through care.',
            },
            ('Moon', 'Mars'): {
                'essence': 'emotions with action and desire',
                'Conjunction': 'Your emotions and actions are one—you act on feelings immediately and passionately.',
                'Opposition': 'You balance emotional safety with assertion; may attract passionate or aggressive partners.',
                'Trine': 'Natural ability to act on emotions healthily; courage comes from emotional security.',
                'Square': 'Emotional volatility or anger drives you to develop healthy emotional expression.',
                'Sextile': 'Opportunities to develop emotional courage and healthy assertion through practice.',
            },
            ('Moon', 'Jupiter'): {
                'essence': 'emotions with expansion and faith',
                'Conjunction': 'Emotional abundance and optimism—you need freedom and growth to feel secure.',
                'Opposition': 'You balance emotional needs with adventure; relationships expand your comfort zone.',
                'Trine': 'Natural emotional generosity and optimism; you nurture through expansion and faith.',
                'Square': 'Over-emotional expression or restlessness drives growth in emotional wisdom.',
                'Sextile': 'Opportunities to expand emotional capacity through philosophy, travel, or teaching.',
            },
            ('Moon', 'Saturn'): {
                'essence': 'emotions with structure and limits',
                'Conjunction': 'Emotional restraint or maturity—you need structure and achievement to feel secure.',
                'Opposition': 'You balance emotional needs with responsibility; may attract serious or older partners.',
                'Trine': 'Natural emotional stability and maturity; you build lasting emotional security.',
                'Square': 'Mother issues or emotional blocks drive development of mature emotional self-sufficiency.',
                'Sextile': 'Opportunities to develop emotional discipline and lasting security through commitment.',
            },
            ('Mercury', 'Venus'): {
                'essence': 'thinking with values and beauty',
                'Conjunction': 'Your mind loves beauty—you think about relationships, art, and harmony.',
                'Opposition': 'You balance logic with aesthetics; may see ideas through relationship lens.',
                'Trine': 'Natural charm in communication; you speak with grace and think creatively.',
                'Square': 'Tension between logic and aesthetics drives refined taste and diplomatic skill.',
                'Sextile': 'Opportunities to develop artistic communication or relationship intelligence.',
            },
            ('Mercury', 'Mars'): {
                'essence': 'thinking with action and assertion',
                'Conjunction': 'Sharp, quick mind—you think fast, speak assertively, and defend your ideas.',
                'Opposition': 'You balance thinking with action; may debate or see thoughts through others.',
                'Trine': 'Natural mental quickness and confident communication; strategic thinking flows.',
                'Square': 'Mental impatience or argumentativeness drives sharp wit and competitive thinking.',
                'Sextile': 'Opportunities to develop assertive communication and quick decision-making.',
            },
            ('Venus', 'Mars'): {
                'essence': 'attraction with action',
                'Conjunction': 'Desire and attraction merge—you pursue what you love passionately and directly.',
                'Opposition': 'You balance attraction with assertion; dynamic romantic tension and polarity.',
                'Trine': 'Natural ability to pursue desires and create harmonious passion in relationships.',
                'Square': 'Creative tension between desire and action drives passionate relationships and art.',
                'Sextile': 'Opportunities to balance masculine and feminine energies through conscious effort.',
            },
            ('Mercury', 'Jupiter'): {
                'essence': 'thinking with expansion and wisdom',
                'Conjunction': 'Expansive mind—you think big, philosophically, and optimistically.',
                'Opposition': 'You balance details with big picture; may see concepts through relationships.',
                'Trine': 'Natural teaching ability and philosophical wisdom; learning comes easily.',
                'Square': 'Over-thinking or exaggeration drives refinement of philosophical communication.',
                'Sextile': 'Opportunities to develop wisdom and teaching skills through study and travel.',
            },
            ('Mercury', 'Saturn'): {
                'essence': 'thinking with structure and discipline',
                'Conjunction': 'Serious, structured mind—you think methodically, deeply, and responsibly.',
                'Opposition': 'You balance thinking with structure; may see logic through authority figures.',
                'Trine': 'Natural mental discipline and ability to master complex subjects through patience.',
                'Square': 'Mental blocks or learning difficulties drive development of mental mastery.',
                'Sextile': 'Opportunities to develop disciplined thinking and communication through practice.',
            },
            ('Venus', 'Jupiter'): {
                'essence': 'love with expansion and abundance',
                'Conjunction': 'Abundant love and generosity—you love expansively and attract abundance.',
                'Opposition': 'You balance intimacy with freedom in relationships; may attract expansive partners.',
                'Trine': 'Natural charm, luck in love, and ability to attract what you value effortlessly.',
                'Square': 'Over-indulgence or excess in pleasure drives development of wise enjoyment.',
                'Sextile': 'Opportunities to expand love and attract abundance through generous giving.',
            },
            ('Venus', 'Saturn'): {
                'essence': 'love with commitment and limits',
                'Conjunction': 'Serious love and committed values—you love responsibly and value lasting bonds.',
                'Opposition': 'You balance pleasure with responsibility; may attract mature or serious partners.',
                'Trine': 'Natural ability to build lasting relationships and value quality over quantity.',
                'Square': 'Love lessons or rejection drives development of mature, committed love.',
                'Sextile': 'Opportunities to develop lasting values and committed relationships through patience.',
            },
            ('Mars', 'Jupiter'): {
                'essence': 'action with expansion and faith',
                'Conjunction': 'Abundant energy and confidence—you act boldly with faith in success.',
                'Opposition': 'You balance assertion with expansion; may act through relationships or beliefs.',
                'Trine': 'Natural ability to take confident action and pursue goals with optimism.',
                'Square': 'Over-confidence or recklessness drives development of wise, measured action.',
                'Sextile': 'Opportunities to expand your capacity for courageous action through risk-taking.',
            },
            ('Mars', 'Saturn'): {
                'essence': 'action with discipline and limits',
                'Conjunction': 'Controlled power—you act with discipline, patience, and strategic restraint.',
                'Opposition': 'You balance assertion with restraint; may face authority in taking action.',
                'Trine': 'Natural ability to channel energy productively through disciplined effort.',
                'Square': 'Frustration or blocked energy drives development of patient, strategic action.',
                'Sextile': 'Opportunities to develop disciplined action and endurance through commitment.',
            },
            ('Jupiter', 'Saturn'): {
                'essence': 'expansion with structure',
                'Conjunction': 'The Great Conjunction—you balance growth with responsibility in 20-year cycles.',
                'Opposition': 'You balance optimism with realism; learning to expand within limits.',
                'Trine': 'Natural ability to build sustainable growth through wise planning.',
                'Square': 'Tension between expansion and contraction drives mature development.',
                'Sextile': 'Opportunities to balance faith with discipline through conscious effort.',
            },
        }

        # Get specific combination or return generic
        combo_data = COMBINATIONS.get(combo_key, {})
        aspect_text = combo_data.get(aspect,
                                     f"These planets form a {aspect.lower()}, creating a unique dynamic in your chart.")
        essence = combo_data.get('essence', 'unique planetary interaction')

        return {
            'essence': essence,
            'interpretation': aspect_text
        }

    # =========================
    # GENERATE INTERPRETATION
    # =========================

    p1_data = PLANET_ARCHETYPES.get(planet1, {'essence': 'planetary force', 'verb': 'express', 'energy': 'influence'})
    p2_data = PLANET_ARCHETYPES.get(planet2, {'essence': 'planetary force', 'verb': 'express', 'energy': 'influence'})
    aspect_dynamic = ASPECT_DYNAMICS.get(aspect_type, {
        'relationship': 'connects with',
        'dynamic': 'These energies interact in unique ways',
        'experience': 'You experience this planetary connection uniquely',
        'integration': 'The key is learning to work with both energies',
    })

    combo = get_combination_meaning(planet1, planet2, aspect_type)

    # Build comprehensive interpretation
    interpretation_parts = []

    # Opening: What connects
    interpretation_parts.append(
        f"Your {p1_data['essence']} ({planet1}) {aspect_dynamic['relationship']} "
        f"your {p2_data['essence']} ({planet2})."
    )

    # Specific meaning for this combination
    interpretation_parts.append(combo['interpretation'])

    # How you experience it
    interpretation_parts.append(aspect_dynamic['experience'])

    # Integration guidance
    interpretation_parts.append(aspect_dynamic['integration'])

    full_interpretation = " ".join(interpretation_parts)

    return {
        'planets': f"{planet1}-{planet2}",
        'aspect_type': aspect_type,
        'orb': orb,
        'essence': combo['essence'],
        'relationship_dynamic': aspect_dynamic['relationship'],
        'full_interpretation': full_interpretation,
        'integration_key': aspect_dynamic['integration'],
    }


def index_coincidences(journal_entry):
    from journal.models import JournalCosmicCoincidence

    # 1. Dig into the 'planets' list of your cached_chart_data
    natal_data = journal_entry.user.birth_profile.cached_chart_data
    natal_planets_list = natal_data.get('planets', [])

    # 2. Convert that list into a simple lookup dictionary: {'Sun': 'Capricorn', ...}
    # This makes the "Match" constant time O(1)
    natal_lookup = {p['name']: p['sign'] for p in natal_planets_list}

    # 3. Get current snapshot positions (this matches your snapshot structure)
    if not journal_entry.planetary_snapshot:
        return

    current_positions = journal_entry.planetary_snapshot.planetary_data.get('planetary_positions', [])

    matches = []
    for p in current_positions:
        name = p['name']
        current_sign = p['sign']

        # 4. Compare current planet sign vs natal planet sign
        if natal_lookup.get(name) == current_sign:
            matches.append(JournalCosmicCoincidence(
                user=journal_entry.user,
                entry=journal_entry,
                planet_key=name
            ))

    if matches:
        # ignore_conflicts=True prevents crashes if you rerun this
        JournalCosmicCoincidence.objects.bulk_create(matches, ignore_conflicts=True)