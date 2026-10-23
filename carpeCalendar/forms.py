from django import forms

from carpeCalendar.models import Category


class EventForm(forms.Form):
    title = forms.CharField(max_length=200)
    description = forms.CharField(widget=forms.Textarea, required=False)
    location = forms.CharField(max_length=200)
    category = forms.ModelChoiceField(queryset=Category.objects.all())
    organizer = forms.CharField(max_length=200)
    facebook_link = forms.URLField(max_length=200, required=False)
    email_organizer = forms.EmailField(max_length=200, required=False)
    form_link = forms.URLField(max_length=200, required=False)

    pmr_friendly = forms.BooleanField(required=False)
    deaf_friendly = forms.BooleanField(required=False)
    blind_friendly = forms.BooleanField(required=False)
    neurodiversity_friendly = forms.BooleanField(required=False)
    granz_filled = forms.BooleanField(required=False)

    def clean(self):
        facebook_link = self.cleaned_data['facebook_link']
        return
        # Check if facebook link is an event link
        if facebook_link and not (
            facebook_link.startswith('https://facebook.com') or
            facebook_link.startswith('https://www.facebook.com') or
            facebook_link.startswith('https://m.facebook.com') or
            facebook_link.startswith('facebook.com')
        ):
            raise forms.ValidationError("Facebook link must be an event link")


class DateForm(forms.Form):
    start = forms.DateTimeField()
    end = forms.DateTimeField()

    def clean(self):
        start = self.cleaned_data['start']
        end = self.cleaned_data['end']

        if start > end:
            raise forms.ValidationError("End date must be after start date")
