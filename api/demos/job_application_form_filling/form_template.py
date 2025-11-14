"""
Form Template
=============

Simple form structure definition for job application form.
"""

from .models import FormStructure, FormField


def get_form_structure() -> FormStructure:
    """
    Get the form structure template.
    
    Returns:
        FormStructure with sections and fields
    """
    fields = [
        # Personal Information Section
        FormField(
            name="full_name",
            label="Full Name",
            type="text",
            section="Personal Information",
            required=True
        ),
        FormField(
            name="email",
            label="Email Address",
            type="email",
            section="Personal Information",
            required=True
        ),
        FormField(
            name="phone",
            label="Phone Number",
            type="tel",
            section="Personal Information",
            required=False
        ),
        FormField(
            name="address",
            label="Address",
            type="textarea",
            section="Personal Information",
            required=False
        ),
        
        # Work Experience Section
        FormField(
            name="work_experience",
            label="Work Experience",
            type="textarea",
            section="Work Experience",
            required=True
        ),
        
        # Education Section
        FormField(
            name="education",
            label="Education",
            type="textarea",
            section="Education",
            required=True
        ),
        
        # Skills Section
        FormField(
            name="skills",
            label="Skills",
            type="textarea",
            section="Skills",
            required=True
        ),
    ]
    
    sections = [
        "Personal Information",
        "Work Experience",
        "Education",
        "Skills"
    ]
    
    return FormStructure(
        sections=sections,
        fields=fields
    )

