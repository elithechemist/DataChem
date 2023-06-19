from django import forms
from crispy_forms.helper import FormHelper
from file_storage.models import Project
from .models import ResponseEntry

class UploadFileForm(forms.Form):
    file = forms.FileField(widget=forms.FileInput)
    project = forms.ModelChoiceField(queryset=Project.objects.all())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'

class ResponseEntryForm(forms.ModelForm):
    class Meta:
        model = ResponseEntry
        fields = ['values']

    def clean_values(self):
        values = self.cleaned_data.get('values')
        return values