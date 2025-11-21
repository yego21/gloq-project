from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def themed_class(context, element_type):
    mode = context.get('current_mode', 'default')

    styles = {
        'card': {
            'default': 'bg-white text-gray-800 shadow',
            'focus': 'bg-blue-100 text-blue-900 shadow-lg',
            'reflect': 'bg-yellow-100 text-yellow-800 shadow-md',
        },
        'button': {
            'default': 'bg-gray-800 text-white',
            'focus': 'bg-blue-700 text-white',
            'reflect': 'bg-yellow-600 text-white',
        },
        'journal_container': {
            'default': 'bg-gray-50 text-gray-900',
            'focus': 'bg-blue-50 text-blue-900',
            'reflect': 'bg-yellow-50 text-yellow-900',
        },
    }

    return styles.get(element_type, {}).get(mode, '')