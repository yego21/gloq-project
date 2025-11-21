from groq import Groq
from django.conf import settings
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now

from ..models import JournalEntry, Tag
from ..forms import JournalEntryForm


def extract_tags(entry):
    """
    Extract 2-3 thematic tags with emoji and sentiment from journal entry.
    Prioritizes 3 tags when possible, minimum 2 tags.

    Returns list of dicts: [{"name": str, "emoji": str, "sentiment": float}, ...]
    """
    client = Groq(api_key=settings.GROQ_API_KEY)

    prompt = (
        "You are a journaling assistant. Based on the following entry, return emotional or thematic tags.\n"
        "\n"
        "Output requirements:\n"
        "- Always attempt to generate 3 distinct tags that reflect the entry.\n"
        "- If the entry does not have enough content for 3 meaningful tags, return only 2.\n"
        "- Each tag must include: name, emoji, and sentiment score.\n"
        "- Sentiment score ranges from -1.0 (very negative) to 1.0 (very positive).\n"
        "- Tags must be distinct themes or emotions, not duplicates.\n"
        "- Output must be valid JSON only, no extra text.\n"
        "\n"
        "Example output:\n"
        '[{\"name\": \"burnout\", \"emoji\": \"😩\", \"sentiment\": -0.8}, '
        '{\"name\": \"reflection\", \"emoji\": \"💭\", \"sentiment\": 0.0}, '
        '{\"name\": \"hope\", \"emoji\": \"✨\", \"sentiment\": 0.7}]\n'
        "\n"
        "Entry:\n"
    )

    prompt += f"{entry.content.strip()}\n"

    response = client.chat.completions.create(
        model="compound-beta-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=200,  # Increased for 3 tags
    )

    try:
        tag_list = json.loads(response.choices[0].message.content.strip())

        if isinstance(tag_list, list) and len(tag_list) > 0:
            # Ensure we have 2-3 tags
            tag_list = tag_list[:3]  # Cap at 3

            # If less than 2, pad with fallback
            while len(tag_list) < 2:
                tag_list.append({
                    "name": "reflection",
                    "emoji": "💭",
                    "sentiment": 0.0
                })

            # Validate structure of each tag
            validated_tags = []
            for tag in tag_list:
                if all(key in tag for key in ['name', 'emoji', 'sentiment']):
                    # Ensure sentiment is a float between -1 and 1
                    try:
                        sentiment = float(tag['sentiment'])
                        sentiment = max(-1.0, min(1.0, sentiment))  # Clamp to range
                    except (ValueError, TypeError):
                        sentiment = 0.0

                    validated_tags.append({
                        'name': tag['name'],
                        'emoji': tag['emoji'],
                        'sentiment': sentiment
                    })

            return validated_tags if len(validated_tags) >= 2 else fallback_tags()

        return fallback_tags()

    except json.JSONDecodeError as e:
        print(f"Tag extraction JSON error: {e}")
        print(f"Response was: {response.choices[0].message.content}")
        return fallback_tags()
    except Exception as e:
        print(f"Tag extraction failed: {e}")
        return fallback_tags()


def fallback_tags():
    """Fallback tags when AI extraction fails"""
    return [
        {"name": "reflection", "emoji": "💭", "sentiment": 0.0},
        {"name": "journal", "emoji": "📔", "sentiment": 0.0},
    ]


@require_POST
@login_required
def submit_journal_entry(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request."}, status=400)

    today = now().date()
    entries_today = JournalEntry.objects.filter(user=request.user, created_at__date=today)

    if entries_today.count() >= 3:
        return JsonResponse({
            "error": "Daily entry limit reached."
        }, status=400)

    form = JournalEntryForm(request.POST)
    if form.is_valid():
        entry = form.save(commit=False)
        entry.user = request.user
        entry.save()

        # Extract tags (name + emoji + sentiment)
        extracted_tags = extract_tags(entry)

        for tag_data in extracted_tags:
            tag_name = tag_data.get("name")
            tag_emoji = tag_data.get("emoji")
            tag_sentiment = tag_data.get("sentiment", 0.0)  # NEW: Get sentiment

            if not tag_name:
                continue

            # Get or create tag with defaults
            tag_obj, created = Tag.objects.get_or_create(
                name=tag_name,
                defaults={
                    'emoji': tag_emoji,
                    'sentiment_score': tag_sentiment  # NEW: Set on creation
                }
            )

            # Update emoji if tag exists but didn't have one
            if tag_emoji and not created and not tag_obj.emoji:
                tag_obj.emoji = tag_emoji
                tag_obj.save()

            # NEW: Update sentiment if tag exists but has default/stale sentiment
            # This handles existing tags getting updated sentiment from new context
            if not created and tag_obj.sentiment_score == 0.0 and tag_sentiment != 0.0:
                tag_obj.sentiment_score = tag_sentiment
                tag_obj.save()

            entry.tags.add(tag_obj)

        # NEW: Check if we should generate commentary using the UserProfile method
        show_commentary = request.user.profile.can_receive_commentary(entry.content)

        response_data = {
            "success": True,
            "message": "Journal entry saved successfully!",
            "entry_id": entry.id,
            "show_commentary": show_commentary  # Add this flag to response
        }

        if show_commentary:
            # Increment the counter since we'll show commentary
            request.user.profile.increment_commentary_count()
            # We'll add the actual commentary generation in the next step
            response_data["commentary_queued"] = True

        return JsonResponse(response_data)
    else:
        return JsonResponse({
            "error": "Please correct the errors in the form.",
            "form_errors": form.errors
        }, status=400)