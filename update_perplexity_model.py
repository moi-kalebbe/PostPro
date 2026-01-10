from apps.projects.models import Project

# Atualizar todos os projetos para usar o novo modelo Perplexity
projects = Project.objects.all()
for p in projects:
    if 'llama-3.1-sonar' in p.research_model:
        p.research_model = 'perplexity/sonar'
        p.save()
        print(f'Updated project {p.name} to use {p.research_model}')
    else:
        print(f'Project {p.name} already using {p.research_model}')
