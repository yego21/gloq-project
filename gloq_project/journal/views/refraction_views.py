from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from ..models import JournalEntry
from modes.utils import get_active_mode, get_synthesis_prompt
from groq import Groq
from django.conf import settings

@login_required
def load_insight_panel(request):
    return render(request, 'journal/ai_insights/insight_panel.html')

@login_required
def load_insight_tab(request, tab_name):
    return render(request, f'journal/ai_insights/_{tab_name}.html')

@require_GET
@login_required
def synthesize_entries(request):
    synthesis_type = request.GET.get('type', 'reflect')
    mode_slug = get_active_mode(request)
    entries = JournalEntry.objects.filter(user=request.user).order_by('-created_at')
    if not entries:
        return HttpResponse("No entries yet.", status=400)

    summary = generate_summary_by_mode_and_type(entries, mode_slug, synthesis_type)
    return render(request, 'journal/ai_insights/_synthesis.html', {
        'synthesis': summary,
        'synthesis_type': synthesis_type,
        'mode': mode_slug
    })



def generate_summary_by_mode_and_type(entries, mode_slug, synthesis_type):
    client = Groq(api_key=settings.GROQ_API_KEY)

    # Get the right prompt for mode + type combination
    prompt = get_synthesis_prompt(mode_slug, synthesis_type)

    # Add entries to prompt
    for entry in entries:
        prompt += f"\nDate: {entry.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        prompt += f"Entry: {entry.content}\n"

    response = client.chat.completions.create(
        model="compound-beta-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=500,
    )

    return response.choices[0].message.content.strip()


@require_GET
def synthesize_entries(request):
    # Get parameters
    synthesis_type = request.GET.get('type', 'reflect')  # Default to reflect
    mode_slug = get_active_mode(request)  # Get current mode

    entries = JournalEntry.objects.filter(user=request.user).order_by('-created_at')
    if not entries:
        return HttpResponse("No entries yet to summarize.", status=400)

    # Generate based on mode + type combination
    summary = generate_summary_by_mode_and_type(entries, mode_slug, synthesis_type)

    return render(request, 'journal/ai_insights/_synthesis.html', {
        'synthesis': summary,
        'synthesis_type': synthesis_type,
        'mode': mode_slug
    })