"""
WCAG 2.2 MCP Server — SC ID Mapping
Maps slug → SC ID (e.g. "non-text-content" → "1.1.1")
"""

# Complete SC ID mapping for WCAG 2.2
# Format: slug → (sc_id, title, level, principle_num, guideline_num)
SC_MAP = {
    # Principle 1: Perceivable
    # Guideline 1.1: Text Alternatives
    "non-text-content":           ("1.1.1", "Non-text Content", "A", "1", "1.1"),
    # Guideline 1.2: Time-based Media
    "audio-only-and-video-only-prerecorded":  ("1.2.1", "Audio-only and Video-only (Prerecorded)", "A", "1", "1.2"),
    "captions-prerecorded":       ("1.2.2", "Captions (Prerecorded)", "A", "1", "1.2"),
    "audio-description-or-media-alternative-prerecorded": ("1.2.3", "Audio Description or Media Alternative (Prerecorded)", "A", "1", "1.2"),
    "captions-live":              ("1.2.4", "Captions (Live)", "AA", "1", "1.2"),
    "audio-description-prerecorded": ("1.2.5", "Audio Description (Prerecorded)", "AA", "1", "1.2"),
    "sign-language-prerecorded":  ("1.2.6", "Sign Language (Prerecorded)", "AAA", "1", "1.2"),
    "extended-audio-description-prerecorded": ("1.2.7", "Extended Audio Description (Prerecorded)", "AAA", "1", "1.2"),
    "media-alternative-prerecorded": ("1.2.8", "Media Alternative (Prerecorded)", "AAA", "1", "1.2"),
    "audio-only-live":            ("1.2.9", "Audio-only (Live)", "AAA", "1", "1.2"),
    # Guideline 1.3: Adaptable
    "info-and-relationships":     ("1.3.1", "Info and Relationships", "A", "1", "1.3"),
    "meaningful-sequence":        ("1.3.2", "Meaningful Sequence", "A", "1", "1.3"),
    "sensory-characteristics":    ("1.3.3", "Sensory Characteristics", "A", "1", "1.3"),
    "orientation":                ("1.3.4", "Orientation", "AA", "1", "1.3"),
    "identify-input-purpose":     ("1.3.5", "Identify Input Purpose", "AA", "1", "1.3"),
    "identify-purpose":           ("1.3.6", "Identify Purpose", "AAA", "1", "1.3"),
    # Guideline 1.4: Distinguishable
    "use-of-color":               ("1.4.1", "Use of Color", "A", "1", "1.4"),
    "audio-control":              ("1.4.2", "Audio Control", "A", "1", "1.4"),
    "contrast-minimum":           ("1.4.3", "Contrast (Minimum)", "AA", "1", "1.4"),
    "resize-text":                ("1.4.4", "Resize Text", "AA", "1", "1.4"),
    "images-of-text":             ("1.4.5", "Images of Text", "AA", "1", "1.4"),
    "contrast-enhanced":          ("1.4.6", "Contrast (Enhanced)", "AAA", "1", "1.4"),
    "low-or-no-background-audio": ("1.4.7", "Low or No Background Audio", "AAA", "1", "1.4"),
    "visual-presentation":        ("1.4.8", "Visual Presentation", "AAA", "1", "1.4"),
    "images-of-text-no-exception": ("1.4.9", "Images of Text (No Exception)", "AAA", "1", "1.4"),
    "reflow":                     ("1.4.10", "Reflow", "AA", "1", "1.4"),
    "non-text-contrast":          ("1.4.11", "Non-text Contrast", "AA", "1", "1.4"),
    "text-spacing":               ("1.4.12", "Text Spacing", "AA", "1", "1.4"),
    "content-on-hover-or-focus":  ("1.4.13", "Content on Hover or Focus", "AA", "1", "1.4"),

    # Principle 2: Operable
    # Guideline 2.1: Keyboard Accessible
    "keyboard":                   ("2.1.1", "Keyboard", "A", "2", "2.1"),
    "no-keyboard-trap":           ("2.1.2", "No Keyboard Trap", "A", "2", "2.1"),
    "keyboard-no-exception":      ("2.1.3", "Keyboard (No Exception)", "AAA", "2", "2.1"),
    "character-key-shortcuts":    ("2.1.4", "Character Key Shortcuts", "A", "2", "2.1"),
    # Guideline 2.2: Enough Time
    "timing-adjustable":          ("2.2.1", "Timing Adjustable", "A", "2", "2.2"),
    "pause-stop-hide":            ("2.2.2", "Pause, Stop, Hide", "A", "2", "2.2"),
    "no-timing":                  ("2.2.3", "No Timing", "AAA", "2", "2.2"),
    "interruptions":              ("2.2.4", "Interruptions", "AAA", "2", "2.2"),
    "re-authenticating":          ("2.2.5", "Re-authenticating", "AAA", "2", "2.2"),
    "timeouts":                   ("2.2.6", "Timeouts", "AAA", "2", "2.2"),
    # Guideline 2.3: Seizures and Physical Reactions
    "three-flashes-or-below-threshold": ("2.3.1", "Three Flashes or Below Threshold", "A", "2", "2.3"),
    "three-flashes":              ("2.3.2", "Three Flashes", "AAA", "2", "2.3"),
    "animation-from-interactions": ("2.3.3", "Animation from Interactions", "AAA", "2", "2.3"),
    # Guideline 2.4: Navigable
    "bypass-blocks":              ("2.4.1", "Bypass Blocks", "A", "2", "2.4"),
    "page-titled":                ("2.4.2", "Page Titled", "A", "2", "2.4"),
    "focus-order":                ("2.4.3", "Focus Order", "A", "2", "2.4"),
    "link-purpose-in-context":    ("2.4.4", "Link Purpose (In Context)", "A", "2", "2.4"),
    "multiple-ways":              ("2.4.5", "Multiple Ways", "AA", "2", "2.4"),
    "headings-and-labels":        ("2.4.6", "Headings and Labels", "AA", "2", "2.4"),
    "focus-visible":              ("2.4.7", "Focus Visible", "A", "2", "2.4"),
    "location":                   ("2.4.8", "Location", "AAA", "2", "2.4"),
    "link-purpose-link-only":     ("2.4.9", "Link Purpose (Link Only)", "AAA", "2", "2.4"),
    "section-headings":           ("2.4.10", "Section Headings", "AAA", "2", "2.4"),
    "focus-not-obscured-minimum": ("2.4.11", "Focus Not Obscured (Minimum)", "AA", "2", "2.4"),
    "focus-not-obscured-enhanced": ("2.4.12", "Focus Not Obscured (Enhanced)", "AAA", "2", "2.4"),
    "focus-appearance":           ("2.4.13", "Focus Appearance", "AA", "2", "2.4"),
    # Guideline 2.5: Input Modalities
    "pointer-gestures":           ("2.5.1", "Pointer Gestures", "A", "2", "2.5"),
    "pointer-cancellation":       ("2.5.2", "Pointer Cancellation", "A", "2", "2.5"),
    "label-in-name":              ("2.5.3", "Label in Name", "A", "2", "2.5"),
    "motion-actuation":           ("2.5.4", "Motion Actuation", "A", "2", "2.5"),
    "target-size-enhanced":       ("2.5.5", "Target Size (Enhanced)", "AAA", "2", "2.5"),
    "concurrent-input-mechanisms": ("2.5.6", "Concurrent Input Mechanisms", "AA", "2", "2.5"),
    "dragging-movements":         ("2.5.7", "Dragging Movements", "AA", "2", "2.5"),
    "target-size-minimum":        ("2.5.8", "Target Size (Minimum)", "AA", "2", "2.5"),

    # Principle 3: Understandable
    # Guideline 3.1: Readable
    "language-of-page":           ("3.1.1", "Language of Page", "A", "3", "3.1"),
    "language-of-parts":          ("3.1.2", "Language of Parts", "AA", "3", "3.1"),
    "unusual-words":              ("3.1.3", "Unusual Words", "AAA", "3", "3.1"),
    "abbreviations":              ("3.1.4", "Abbreviations", "AAA", "3", "3.1"),
    "reading-level":              ("3.1.5", "Reading Level", "AAA", "3", "3.1"),
    "pronunciation":              ("3.1.6", "Pronunciation", "AAA", "3", "3.1"),
    # Guideline 3.2: Predictable
    "on-focus":                   ("3.2.1", "On Focus", "A", "3", "3.2"),
    "on-input":                   ("3.2.2", "On Input", "A", "3", "3.2"),
    "consistent-navigation":      ("3.2.3", "Consistent Navigation", "AA", "3", "3.2"),
    "consistent-identification":  ("3.2.4", "Consistent Identification", "AA", "3", "3.2"),
    "change-on-request":          ("3.2.5", "Change on Request", "AAA", "3", "3.2"),
    "consistent-help":            ("3.2.6", "Consistent Help", "A", "3", "3.2"),
    # Guideline 3.3: Input Assistance
    "error-identification":       ("3.3.1", "Error Identification", "A", "3", "3.3"),
    "labels-or-instructions":     ("3.3.2", "Labels or Instructions", "A", "3", "3.3"),
    "error-suggestion":           ("3.3.3", "Error Suggestion", "AA", "3", "3.3"),
    "error-prevention-legal-financial-data": ("3.3.4", "Error Prevention (Legal, Financial, Data)", "AA", "3", "3.3"),
    "help":                       ("3.3.5", "Help", "AA", "3", "3.3"),
    "error-prevention-all":       ("3.3.6", "Error Prevention (All)", "AAA", "3", "3.3"),
    "redundant-entry":            ("3.3.7", "Redundant Entry", "A", "3", "3.3"),
    "accessible-authentication-minimum": ("3.3.8", "Accessible Authentication (Minimum)", "AA", "3", "3.3"),
    "accessible-authentication-enhanced": ("3.3.9", "Accessible Authentication (Enhanced)", "AAA", "3", "3.3"),

    # Principle 4: Robust
    # Guideline 4.1: Compatible
    "parsing":                    ("4.1.1", "Parsing (Obsolete and removed)", "A", "4", "4.1"),
    "name-role-value":            ("4.1.2", "Name, Role, Value", "A", "4", "4.1"),
    "status-messages":            ("4.1.3", "Status Messages", "AA", "4", "4.1"),
}

# Reverse mapping: SC ID → slug  
SC_ID_TO_SLUG = {v[0]: k for k, v in SC_MAP.items()}

# Build hierarchy
PRINCIPLES = {
    "1": {"num": "1", "title": "Perceivable", "handle": "perceivable"},
    "2": {"num": "2", "title": "Operable", "handle": "operable"},
    "3": {"num": "3", "title": "Understandable", "handle": "understandable"},
    "4": {"num": "4", "title": "Robust", "handle": "robust"},
}

GUIDELINES = {
    "1.1": {"num": "1.1", "title": "Text Alternatives", "principle": "1"},
    "1.2": {"num": "1.2", "title": "Time-based Media", "principle": "1"},
    "1.3": {"num": "1.3", "title": "Adaptable", "principle": "1"},
    "1.4": {"num": "1.4", "title": "Distinguishable", "principle": "1"},
    "2.1": {"num": "2.1", "title": "Keyboard Accessible", "principle": "2"},
    "2.2": {"num": "2.2", "title": "Enough Time", "principle": "2"},
    "2.3": {"num": "2.3", "title": "Seizures and Physical Reactions", "principle": "2"},
    "2.4": {"num": "2.4", "title": "Navigable", "principle": "2"},
    "2.5": {"num": "2.5", "title": "Input Modalities", "principle": "2"},
    "3.1": {"num": "3.1", "title": "Readable", "principle": "3"},
    "3.2": {"num": "3.2", "title": "Predictable", "principle": "3"},
    "3.3": {"num": "3.3", "title": "Input Assistance", "principle": "3"},
    "4.1": {"num": "4.1", "title": "Compatible", "principle": "4"},
}

# SCs grouped by guideline
SCS_BY_GUIDELINE = {}
for slug, (sc_id, title, level, principle, guideline) in SC_MAP.items():
    if guideline not in SCS_BY_GUIDELINE:
        SCS_BY_GUIDELINE[guideline] = []
    SCS_BY_GUIDELINE[guideline].append({
        "sc_id": sc_id, "slug": slug, "title": title, "level": level
    })

# SCs grouped by principle
SCS_BY_PRINCIPLE = {}
for slug, (sc_id, title, level, principle, guideline) in SC_MAP.items():
    if principle not in SCS_BY_PRINCIPLE:
        SCS_BY_PRINCIPLE[principle] = []
    SCS_BY_PRINCIPLE[principle].append({
        "sc_id": sc_id, "slug": slug, "title": title, "level": level, "guideline": guideline
    })


def get_sc_id(slug):
    """Get SC ID for a slug."""
    return SC_MAP.get(slug, (None,))[0]


def get_slug(sc_id):
    """Get slug for an SC ID."""
    return SC_ID_TO_SLUG.get(sc_id)


def resolve_sc_identifier(identifier):
    """Resolve '1.1.1' or 'non-text-content' to a normalized slug."""
    identifier = identifier.strip().lower()
    if identifier in SC_ID_TO_SLUG:
        return SC_ID_TO_SLUG[identifier]
    if identifier in SC_MAP:
        return identifier
    # Try partial match
    for slug in SC_MAP:
        if identifier in slug or slug.replace('-', '') == identifier.replace('.', '').replace(' ', ''):
            return slug
    return None
