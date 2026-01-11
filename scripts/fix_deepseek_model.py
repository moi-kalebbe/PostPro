
from apps.projects.models import Project
from apps.authentication.models import Agency

def run():
    print("Starting DeepSeek model ID fix...")
    
    # Fix Projects
    projects = Project.objects.filter(text_model='deepseek/deepseek-v3')
    count = projects.count()
    print(f"Found {count} projects with invalid model ID.")
    
    for project in projects:
        print(f"Fixing project: {project.name}")
        project.text_model = 'deepseek/deepseek-chat'
        project.save(update_fields=['text_model'])
        
    # Fix Agencies (default model)
    agencies = Agency.objects.filter(default_text_model='deepseek/deepseek-v3')
    agency_count = agencies.count()
    print(f"Found {agency_count} agencies with invalid default model.")
    
    for agency in agencies:
        print(f"Fixing agency: {agency.name}")
        agency.default_text_model = 'deepseek/deepseek-chat'
        agency.save(update_fields=['default_text_model'])
        
    print("Fix complete!")
