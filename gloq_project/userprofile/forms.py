# from django import forms
# from .models import UserProfile
#
# class UserProfileForm(forms.ModelForm):
#     class Meta:
#         model = UserProfile
#         fields = ["birth_date", "birth_time", "birth_place", "timezone"]
#         widgets = {
#             "birth_date": forms.DateInput(
#                 attrs={
#                     "type": "date",  # This is the key change!
#                     "class": "block w-full rounded-xl border-0 py-3 px-4 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 bg-white transition-all duration-200 hover:ring-gray-400",
#                     "max": "2025-12-31",  # Prevent future dates
#                     "min": "1900-01-01"   # Set reasonable minimum
#                 }
#             ),
#             "birth_time": forms.TimeInput(
#                 attrs={
#                     "type": "time",  # This is the key change!
#                     "class": "block w-full rounded-xl border-0 py-3 px-4 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 bg-white transition-all duration-200 hover:ring-gray-400"
#                 }
#             ),
#             "birth_place": forms.TextInput(
#                 attrs={
#                     "class": "block w-full rounded-xl border-0 py-3 px-4 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 bg-white transition-all duration-200 hover:ring-gray-400",
#                     "placeholder": "Enter your birth place"
#                 }
#             ),
#             "timezone": forms.Select(
#                 attrs={
#                     "class": "block w-full rounded-xl border-0 py-3 px-4 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 bg-white transition-all duration-200 hover:ring-gray-400"
#                 }
#             ),
#         }
