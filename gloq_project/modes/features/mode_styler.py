MODE_STYLER_CONFIG = {
    "default": {
        "background_class": "bg-white",
        "text_class": "text-gray-800",
        "button_class": "btn-outline-secondary",
    },
    "mystical": {
        # "background_class": "bg-purple-100",
        "header_background_class": "bg-gradient-to-r from-purple-100 to-indigo-100",
        # "content_background_class": "bg-gradient-to-br from-purple-25 to-indigo-25",

        "card_class": "bg-white border-l-4 border-purple-400 shadow-lg shadow-purple-100/50",
        "card_header_class": "bg-gradient-to-r from-purple-50 to-indigo-50 border-b border-purple-200",
        "feature_card_class": "bg-gradient-to-br from-purple-50 to-white border border-purple-200",

        "text_class": "text-blue-900",
        "button_class": "bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded shadow",
        "synthesis_reflect_class": "bg-purple-50 hover:bg-purple-100 border border-purple-200",
        "synthesis_digest_class": "bg-indigo-50 hover:bg-indigo-100 border border-indigo-200",
    # ... etc
},
    "philosophical": {
        "background_class": "bg-pink-100",
        "text_class": "text-pink-900",
        "button_class": "bg-green-500 hover:bg-green-600 text-black py-2 px-4 rounded-lg",
        "view_entries_class": "bg-green-50 border-green-300",
        "view_entries_button": "bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded"
    },
}

MODE_HEADER_CONFIG = {
    "mystical": {
        "icon": "✨",
        "icon_bg": "bg-gradient-to-br from-purple-500 to-indigo-600",
        "title": "Mystical Journey",
        "description": "Explore the mysterious and transcendent realms",
        "svg": """
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"/>
        """
    },
    "philosophical": {
        "icon": "🤔",
        "icon_bg": "bg-gradient-to-br from-blue-500 to-indigo-600",
        "title": "Philosophical Inquiry",
        "description": "Engage in deep thinking and fundamental questions",
        "svg": """
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
        """
    },
    "creative": {
        "icon": "🎨",
        "icon_bg": "bg-gradient-to-br from-pink-500 to-rose-600",
        "title": "Creative Expression",
        "description": "Unleash your artistic potential and innovative thinking",
        "svg": """
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v14a2 2 0 01-2 2h-4zM7 3V1M13 21a4 4 0 004-4V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v14a2 2 0 002 2h4zM17 3V1"/>
        """
    },
    "exploratory": {
        "icon": "🔍",
        "icon_bg": "bg-gradient-to-br from-cyan-500 to-blue-600",
        "title": "Exploratory Discovery",
        "description": "Discover new horizons and uncharted territories",
        "svg": """
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
        """
    },
    "medical": {
        "icon": "⚕️",
        "icon_bg": "bg-gradient-to-br from-green-500 to-emerald-600",
        "title": "Medical Insights",
        "description": "Focus on health, wellness, and medical knowledge",
        "svg": """
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
        """
    },
    "spiritual": {
        "icon": "🕯️",
        "icon_bg": "bg-gradient-to-br from-teal-500 to-cyan-600",
        "title": "Spiritual Connection",
        "description": "Connect with deeper meaning and inner wisdom",
        "svg": """
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"/>
        """
    },
    "visionary": {
        "icon": "🔮",
        "icon_bg": "bg-gradient-to-br from-indigo-500 to-purple-600",
        "title": "Visionary Thinking",
        "description": "Envision future possibilities and breakthrough ideas",
        "svg": """
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
        """
    },
    "productive": {
        "icon": "⚡",
        "icon_bg": "bg-gradient-to-br from-yellow-500 to-orange-600",
        "title": "Productive Focus",
        "description": "Optimize efficiency and achieve your goals",
        "svg": """
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M13 10V3L4 14h7v7l9-11h-7z"/>
        """
    }
}


def get_feature_styles(mode):
    """
    Enhanced styling system with card-based layouts and expandable functionality.
    Returns both container styles and content type configurations.
    """

    # Base card structure that all modes inherit
    base_card_style = "mode-card p-6 rounded-xl expandable-card cursor-pointer hover:shadow-lg transition-all duration-300"

    styles = {
        'mystical': {
            # Card containers with enhanced styling
            'astronomical_container': f"{base_card_style} content-inquiry bg-gradient-to-br from-purple-50 to-indigo-50 border border-purple-100",
            'action_container': f"{base_card_style} content-action bg-gradient-to-br from-purple-100 to-indigo-100 border-l-4 border-purple-400",
            'fact_container': f"{base_card_style} content-insight bg-gradient-to-br from-purple-50 to-indigo-50 border border-purple-100",

            # Icon containers
            'icon_container': 'w-10 h-10 bg-gradient-to-br from-purple-400 to-purple-600 rounded-lg flex items-center justify-center',
            'icon_class': 'w-5 h-5 text-white icon-float',

            # Typography
            'title': 'text-lg font-semibold text-gray-900 mb-2',
            'text': 'text-gray-700 mb-3',
            'subtitle': 'text-xs text-purple-500 mt-2',
            'fact_title': 'text-lg font-semibold text-gray-900 mb-2',

            # Expanded content styling
            'expanded_content': 'card-content-expanded mt-4 p-4 bg-white/50 rounded-lg',
            'expanded_text': 'text-sm text-gray-600',

            # Action buttons
            'action_btn': 'action-btn px-3 py-1 text-xs bg-purple-100 text-purple-700 rounded-full hover:bg-purple-200 transition-colors',

            # Color scheme
            'primary_color': 'purple',
            'gradient_from': 'from-purple-400',
            'gradient_to': 'to-purple-600'
        },

        'philosophical': {
            'question_container': f"{base_card_style} content-inquiry bg-gradient-to-br from-blue-50 to-cyan-50 border border-blue-100",
            'action_container': f"{base_card_style} content-action bg-gradient-to-br from-blue-100 to-cyan-100 border-l-4 border-blue-400",
            'fact_container': f"{base_card_style} content-insight bg-gradient-to-br from-blue-50 to-cyan-50 border border-blue-100",

            'icon_container': 'w-10 h-10 bg-gradient-to-br from-blue-400 to-blue-600 rounded-lg flex items-center justify-center',
            'icon_class': 'w-5 h-5 text-white icon-float',

            'title': 'text-lg font-semibold text-gray-900 mb-2',
            'text': 'text-gray-700 mb-3',
            'subtitle': 'text-xs text-blue-500 mt-2',
            'fact_title': 'text-lg font-semibold text-gray-900 mb-2',

            'expanded_content': 'card-content-expanded mt-4 p-4 bg-white/50 rounded-lg',
            'expanded_text': 'text-sm text-gray-600',
            'action_btn': 'action-btn px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded-full hover:bg-blue-200 transition-colors',

            'primary_color': 'blue',
            'gradient_from': 'from-blue-400',
            'gradient_to': 'to-blue-600'
        },

        'medical': {
            'question_container': f"{base_card_style} content-inquiry bg-gradient-to-br from-green-50 to-emerald-50 border border-green-100",
            'action_container': f"{base_card_style} content-action bg-gradient-to-br from-green-100 to-emerald-100 border-l-4 border-green-400",
            'fact_container': f"{base_card_style} content-insight bg-gradient-to-br from-green-50 to-emerald-50 border border-green-100",

            'icon_container': 'w-10 h-10 bg-gradient-to-br from-green-400 to-green-600 rounded-lg flex items-center justify-center',
            'icon_class': 'w-5 h-5 text-white icon-pulse',

            'title': 'text-lg font-semibold text-gray-900 mb-2',
            'text': 'text-gray-700 mb-3',
            'subtitle': 'text-xs text-green-500 mt-2',
            'fact_title': 'text-lg font-semibold text-gray-900 mb-2',

            'expanded_content': 'card-content-expanded mt-4 p-4 bg-white/50 rounded-lg',
            'expanded_text': 'text-sm text-gray-600',
            'action_btn': 'action-btn px-3 py-1 text-xs bg-green-100 text-green-700 rounded-full hover:bg-green-200 transition-colors',

            'primary_color': 'green',
            'gradient_from': 'from-green-400',
            'gradient_to': 'to-green-600'
        },

        'creative': {
            'question_container': f"{base_card_style} content-inquiry bg-gradient-to-br from-pink-50 to-rose-50 border border-pink-100",
            'action_container': f"{base_card_style} content-action bg-gradient-to-br from-pink-100 to-rose-100 border-l-4 border-pink-400",
            'fact_container': f"{base_card_style} content-insight bg-gradient-to-br from-pink-50 to-rose-50 border border-pink-100",

            'icon_container': 'w-10 h-10 bg-gradient-to-br from-pink-400 to-pink-600 rounded-lg flex items-center justify-center',
            'icon_class': 'w-5 h-5 text-white icon-float',

            'title': 'text-lg font-semibold text-gray-900 mb-2',
            'text': 'text-gray-700 mb-3',
            'subtitle': 'text-xs text-pink-500 mt-2',
            'fact_title': 'text-lg font-semibold text-gray-900 mb-2',

            'expanded_content': 'card-content-expanded mt-4 p-4 bg-white/50 rounded-lg',
            'expanded_text': 'text-sm text-gray-600',
            'action_btn': 'action-btn px-3 py-1 text-xs bg-pink-100 text-pink-700 rounded-full hover:bg-pink-200 transition-colors',

            'primary_color': 'pink',
            'gradient_from': 'from-pink-400',
            'gradient_to': 'to-pink-600'
        },

        'productive': {
            'question_container': f"{base_card_style} content-inquiry bg-gradient-to-br from-yellow-50 to-amber-50 border border-yellow-100",
            'action_container': f"{base_card_style} content-action bg-gradient-to-br from-yellow-100 to-amber-100 border-l-4 border-yellow-400",
            'fact_container': f"{base_card_style} content-insight bg-gradient-to-br from-yellow-50 to-amber-50 border border-yellow-100",

            'icon_container': 'w-10 h-10 bg-gradient-to-br from-yellow-400 to-yellow-600 rounded-lg flex items-center justify-center',
            'icon_class': 'w-5 h-5 text-white icon-pulse',

            'title': 'text-lg font-semibold text-gray-900 mb-2',
            'text': 'text-gray-700 mb-3',
            'subtitle': 'text-xs text-yellow-600 mt-2',
            'fact_title': 'text-lg font-semibold text-gray-900 mb-2',

            'expanded_content': 'card-content-expanded mt-4 p-4 bg-white/50 rounded-lg',
            'expanded_text': 'text-sm text-gray-600',
            'action_btn': 'action-btn px-3 py-1 text-xs bg-yellow-100 text-yellow-700 rounded-full hover:bg-yellow-200 transition-colors',

            'primary_color': 'yellow',
            'gradient_from': 'from-yellow-400',
            'gradient_to': 'to-yellow-600'
        },

        'exploratory': {
            'question_container': f"{base_card_style} content-inquiry bg-gradient-to-br from-cyan-50 to-blue-50 border border-cyan-100",
            'action_container': f"{base_card_style} content-action bg-gradient-to-br from-cyan-100 to-blue-100 border-l-4 border-cyan-400",
            'fact_container': f"{base_card_style} content-insight bg-gradient-to-br from-cyan-50 to-blue-50 border border-cyan-100",

            'icon_container': 'w-10 h-10 bg-gradient-to-br from-cyan-400 to-cyan-600 rounded-lg flex items-center justify-center',
            'icon_class': 'w-5 h-5 text-white icon-float',

            'title': 'text-lg font-semibold text-gray-900 mb-2',
            'text': 'text-gray-700 mb-3',
            'subtitle': 'text-xs text-cyan-500 mt-2',
            'fact_title': 'text-lg font-semibold text-gray-900 mb-2',

            'expanded_content': 'card-content-expanded mt-4 p-4 bg-white/50 rounded-lg',
            'expanded_text': 'text-sm text-gray-600',
            'action_btn': 'action-btn px-3 py-1 text-xs bg-cyan-100 text-cyan-700 rounded-full hover:bg-cyan-200 transition-colors',

            'primary_color': 'cyan',
            'gradient_from': 'from-cyan-400',
            'gradient_to': 'to-cyan-600'
        },

        'visionary': {
            'question_container': f"{base_card_style} content-inquiry bg-gradient-to-br from-indigo-50 to-purple-50 border border-indigo-100",
            'action_container': f"{base_card_style} content-action bg-gradient-to-br from-indigo-100 to-purple-100 border-l-4 border-indigo-400",
            'fact_container': f"{base_card_style} content-insight bg-gradient-to-br from-indigo-50 to-purple-50 border border-indigo-100",

            'icon_container': 'w-10 h-10 bg-gradient-to-br from-indigo-400 to-indigo-600 rounded-lg flex items-center justify-center',
            'icon_class': 'w-5 h-5 text-white icon-float',

            'title': 'text-lg font-semibold text-gray-900 mb-2',
            'text': 'text-gray-700 mb-3',
            'subtitle': 'text-xs text-indigo-500 mt-2',
            'fact_title': 'text-lg font-semibold text-gray-900 mb-2',

            'expanded_content': 'card-content-expanded mt-4 p-4 bg-white/50 rounded-lg',
            'expanded_text': 'text-sm text-gray-600',
            'action_btn': 'action-btn px-3 py-1 text-xs bg-indigo-100 text-indigo-700 rounded-full hover:bg-indigo-200 transition-colors',

            'primary_color': 'indigo',
            'gradient_from': 'from-indigo-400',
            'gradient_to': 'to-indigo-600'
        },

        'spiritual': {
            'question_container': f"{base_card_style} content-inquiry bg-gradient-to-br from-teal-50 to-green-50 border border-teal-100",
            'action_container': f"{base_card_style} content-action bg-gradient-to-br from-teal-100 to-green-100 border-l-4 border-teal-400",
            'fact_container': f"{base_card_style} content-insight bg-gradient-to-br from-teal-50 to-green-50 border border-teal-100",

            'icon_container': 'w-10 h-10 bg-gradient-to-br from-teal-400 to-teal-600 rounded-lg flex items-center justify-center',
            'icon_class': 'w-5 h-5 text-white icon-float',

            'title': 'text-lg font-semibold text-gray-900 mb-2',
            'text': 'text-gray-700 mb-3',
            'subtitle': 'text-xs text-teal-500 mt-2',
            'fact_title': 'text-lg font-semibold text-gray-900 mb-2',

            'expanded_content': 'card-content-expanded mt-4 p-4 bg-white/50 rounded-lg',
            'expanded_text': 'text-sm text-gray-600',
            'action_btn': 'action-btn px-3 py-1 text-xs bg-teal-100 text-teal-700 rounded-full hover:bg-teal-200 transition-colors',

            'primary_color': 'teal',
            'gradient_from': 'from-teal-400',
            'gradient_to': 'to-teal-600'
        }
    }

    # Return the mode styles or fallback to mystical
    return styles.get(mode, styles['mystical'])


def get_card_icons():
    """
    Returns SVG icons for different content types.
    These can be used in the template for consistent iconography.
    """
    return {
        'inquiry': '''<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>''',

        'action': '''<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>''',

        'insight': '''<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>''',

        'astronomical': '''<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"/>''',

        'mystical': '''<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>'''
    }



# def get_feature_styles(mode):
#     styles = {
#         'mystical': {
#             'astronomical_container': 'bg-purple-50 rounded-lg p-4 mb-4',
#             'action_container': 'bg-purple-100 rounded-lg p-4 mb-4 border-l-4 border-purple-300',
#             'fact_container': 'bg-purple-50 rounded-lg p-4',
#             'title': 'font-medium text-purple-800',
#             'text': 'text-sm text-purple-700',
#             'subtitle': 'text-xs text-purple-600 mt-2',
#             'fact_title': 'text-sm font-medium text-purple-900 mb-1'
#         },
#           'philosophical': {
#             'question_container': 'bg-blue-50 rounded-lg p-4',
#             'action_container': 'bg-blue-100 rounded-lg p-4 mb-4 border-l-4 border-green-300',
#              'fact_container': 'bg-blue-50 rounded-lg p-4',
#             'title': 'font-medium text-blue-800',
#             'text': 'text-sm text-blue-700',
#             'subtitle': 'text-xs text-blue-600 mt-2',
#             'fact_title': 'text-sm font-medium text-blue-900 mb-1'
#         },
#         'medical': {
#             'question_container': 'bg-green-50 rounded-lg p-4 mb-4',
#             'action_container': 'bg-green-100 rounded-lg p-4 mb-4 border-l-4 border-green-300',
#             'fact_container': 'bg-green-50 rounded-lg p-4',
#             'title': 'font-medium text-green-800',
#             'text': 'text-sm text-green-700',
#             'subtitle': 'text-xs text-green-600 mt-2',
#             'fact_title': 'text-sm font-medium text-green-900 mb-1'
#         },
#         'creative': {
#             'question_container': 'bg-pink-50 rounded-lg p-4 mb-4',
#             'action_container': 'bg-pink-100 rounded-lg p-4 mb-4 border-l-4 border-pink-300',
#             'fact_container': 'bg-pink-50 rounded-lg p-4',
#             'title': 'font-medium text-pink-800',
#             'text': 'text-sm text-pink-700',
#             'subtitle': 'text-xs text-pink-600 mt-2',
#             'fact_title': 'text-sm font-medium text-pink-900 mb-1'
#         },
#         'productive': {
#             'question_container': 'bg-yellow-50 rounded-lg p-4 mb-4',
#             'action_container': 'bg-yellow-100 rounded-lg p-4 mb-4 border-l-4 border-yellow-300',
#             'fact_container': 'bg-yellow-50 rounded-lg p-4',
#             'title': 'font-medium text-yellow-800',
#             'text': 'text-sm text-yellow-700',
#             'subtitle': 'text-xs text-yellow-600 mt-2',
#             'fact_title': 'text-sm font-medium text-yellow-900 mb-1'
#         },
#         'exploratory': {
#             'question_container': 'bg-cyan-50 rounded-lg p-4 mb-4',
#             'action_container': 'bg-cyan-100 rounded-lg p-4 mb-4 border-l-4 border-cyan-300',
#             'fact_container': 'bg-cyan-50 rounded-lg p-4',
#             'title': 'font-medium text-cyan-800',
#             'text': 'text-sm text-cyan-700',
#             'subtitle': 'text-xs text-cyan-600 mt-2',
#             'fact_title': 'text-sm font-medium text-cyan-900 mb-1'
#         },
#         'visionary': {
#             'question_container': 'bg-indigo-50 rounded-lg p-4 mb-4',
#             'action_container': 'bg-indigo-100 rounded-lg p-4 mb-4 border-l-4 border-indigo-300',
#             'fact_container': 'bg-indigo-50 rounded-lg p-4',
#             'title': 'font-medium text-indigo-800',
#             'text': 'text-sm text-indigo-700',
#             'subtitle': 'text-xs text-indigo-600 mt-2',
#             'fact_title': 'text-sm font-medium text-indigo-900 mb-1'
#         },
#         'spiritual': {
#             'question_container': 'bg-teal-50 rounded-lg p-4 mb-4',
#             'action_container': 'bg-teal-100 rounded-lg p-4 mb-4 border-l-4 border-teal-300',
#             'fact_container': 'bg-teal-50 rounded-lg p-4',
#             'title': 'font-medium text-teal-800',
#             'text': 'text-sm text-teal-700',
#             'subtitle': 'text-xs text-teal-600 mt-2',
#             'fact_title': 'text-sm font-medium text-teal-900 mb-1'
#         }
#     }
#     return styles.get(mode, styles.get('default', styles['mystical']))

def get_card_styles(mode):
    # Another helper for different component types
    pass