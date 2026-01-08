from django.urls import path
from .views import mystical_views, spiritual_views, creative_views, productive_views, philosophical_views, medical_views, exploratory_views, visionary_views


app_name = "deep_dive"


urlpatterns = [
    path("mystical/", mystical_views.mystical, name="mystical"),    
    path('mystical/moon_planet/', mystical_views.moon_planets, name='moon_planets'),
    # path('mystical/astro_chart_reading/', mystical_views.astro_chart_reading, name='astro_chart_reading'),
    path('mystical/astro_birth_chart/', mystical_views.astro_birth_chart, name='astro_birth_chart'),
    path('mystical/astro_ai_readings/', mystical_views.astro_ai_readings, name='astro_ai_readings'),
    path('mystical/mystical/', mystical_views.interactive_mystical, name='interactive_mystical'),
    path('mystical/generate-natal-chart/', mystical_views.generate_natal_chart, name='generate_natal_chart'),
    path('chart/unified/', mystical_views.unified_chart_modal, name='unified_chart_modal'),
    path('planet/<str:planet_name>/', mystical_views.planet_detail, name='planet_detail'),
    path('aspect/<str:planet1>/<str:planet2>/<str:aspect_type>/', mystical_views.aspect_detail, name='aspect_detail'),

    path('mystical/draw_tarot_card', mystical_views.draw_tarot_card, name='draw_tarot_card'),
    # path('mystical/generate_tarot_card_from_chart', mystical_views.generate_tarot_card_from_chart, name='generate_tarot_card_from_chart'),
    path('mystical/tarot_card_history', mystical_views.tarot_card_history, name='tarot_card_history'),
    path('mystical/draw_tarot_spread', mystical_views.draw_tarot_spread, name='draw_tarot_spread'),

    # Planet Modal Endpoints
    path('planet/<str:planet_name>/meaning/',
         mystical_views.planet_meaning,
         name='planet_meaning'),

    path('planet/<str:planet_name>/journals/',
         mystical_views.planet_journals,
         name='planet_journals'),



    # AI Reading endpoints
    path('ai-reading/generate/',
         mystical_views.generate_ai_reading,
         name='generate_ai_reading'),

    path('ai-reading/options/',
         mystical_views.get_reading_options,
         name='reading_options'),

    path('ai-reading/refresh/',
         mystical_views.refresh_reading_display,
         name='refresh_reading'),
    path('view-reading/<str:reading_type>/', mystical_views.view_reading, name='view_reading'),




    path("spiritual/", spiritual_views.spiritual, name="spiritual"),
    path("creative/", creative_views.creative, name="creative"),
    path("philosophical/", philosophical_views.philosophical, name="philosophical"),
    path("medical", medical_views.medical, name="medical"),
    path("visionary/", visionary_views.visionary, name="visionary"),
    path("exploratory/", exploratory_views.exploratory, name="exploratory"),
    path("productive/", productive_views.productive, name="productive"),

    # path('rhythm/data/',
    #      mystical_views.get_personal_rhythm_data,
    #      name='rhythm_data'),

    path('rhythm/section/',
         mystical_views.personal_rhythm_section,
         name='rhythm_section'),

    # Testing endpoint (remove after testing)
    path('test-rhythm/',
         mystical_views.test_rhythm_analysis,
         name='test_rhythm'),

    path('rhythm/', mystical_views.rhythm_dashboard, name='rhythm_dashboard'),
   


    # path('api/moon-phase/', mystical_views.moon_phase_api, name='moon_phase_api'),
    # path('api/planetary/', mystical_views.planetary_api, name='planetary_api'),

]