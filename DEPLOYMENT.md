# 🚀 PostPro - Deployment Guide

**Version:** 2.0.0  
**Date:** 2026-01-09  
**Production URL:** https://postpro.nuvemchat.com

---

## 📋 Pre-Deployment Checklist

- [x] All code implemented (Phases 1-4)
- [x] Plugin updated to v2.0.0
- [x] URLs updated to postpro.nuvemchat.com
- [ ] Code committed to Git
- [ ] Docker image built
- [ ] Migrations ready
- [ ] Celery tasks registered

---

## 🔧 Step 1: Commit & Push Code

```bash
# Navigate to project
cd "c:/Users/olx/OneDrive/Desktop/PROJETOS 2026/PostPro"

# Check status
git status

# Add all changes
git add .

# Commit with descriptive message
git commit -m "feat: implement editorial pipeline v2.0.0

- Add 5 new models (SiteProfile, TrendPack, EditorialPlan, EditorialPlanItem, AIModelPolicy)
- Add 6 services (OpenRouter Models, Perplexity, Pollinations, SiteProfile, EditorialPipeline)
- Add 4 Celery tasks (editorial plan generation, scheduled posts, site sync)
- Update WordPress plugin to v2.0.0 with SEO automation
- Add SEO modules (Yoast, Rank Math with schemas, Internal Link Juicer)
- Implement external_id idempotency system
- Add scheduled post support (draft/future/publish)
- Update plugin author to Moisés Kalebbe"

# Push to GitHub
git push origin main
```

---

## 🐳 Step 2: Build & Deploy Docker Image

GitHub Actions will automatically:
1. Build Docker image
2. Push to `ghcr.io/moi-kalebbe/postpro:latest`

**Monitor build:**
- Visit: https://github.com/moi-kalebbe/postpro/actions
- Wait for build to complete (~5-10 minutes)

---

## 🖥️ Step 3: Update Docker Swarm Services

```bash
# SSH into production server
ssh user@postpro.nuvemchat.com

# Pull latest image
docker pull ghcr.io/moi-kalebbe/postpro:latest

# Update services
docker service update --image ghcr.io/moi-kalebbe/postpro:latest postpro_web
docker service update --image ghcr.io/moi-kalebbe/postpro:latest postpro_worker
docker service update --image ghcr.io/moi-kalebbe/postpro:latest postpro_beat

# Check service status
docker service ls | grep postpro
```

---

## 🗄️ Step 4: Run Database Migrations

```bash
# Still on production server

# Get web container ID
WEB_CONTAINER=$(docker ps -q -f name=postpro_web)

# Exec into container
docker exec -it $WEB_CONTAINER bash

# Inside container:
python manage.py migrate automation

# Expected output:
# Running migrations:
#   Applying automation.000X_add_editorial_models... OK

# Exit container
exit
```

---

## 🔄 Step 5: Register Celery Tasks

```bash
# Still on production server

# Restart worker to load new tasks
docker service update --force postpro_worker

# Restart beat scheduler
docker service update --force postpro_beat

# Check worker logs
docker service logs postpro_worker --tail 50

# Should see:
# [tasks]
#   . apps.automation.tasks_editorial.generate_editorial_plan
#   . apps.automation.tasks_editorial.process_scheduled_posts
#   . apps.automation.tasks_editorial.generate_post_from_plan_item
#   . apps.automation.tasks_editorial.sync_site_profile
```

---

## ✅ Step 6: Verify Deployment

### 6.1 Check Django Admin

```bash
# Visit: https://postpro.nuvemchat.com/admin

# Login and verify new models appear:
- Site Profiles
- Trend Packs
- Editorial Plans
- Editorial Plan Items
- AI Model Policies
```

### 6.2 Test API Endpoints

```bash
# Test health check
curl https://postpro.nuvemchat.com/api/health

# Test license validation (replace with real key)
curl -H "X-License-Key: your-license-key" \
  https://postpro.nuvemchat.com/api/v1/validate-license
```

### 6.3 Check Logs

```bash
# Web logs
docker service logs postpro_web --tail 100

# Worker logs
docker service logs postpro_worker --tail 100

# Beat logs
docker service logs postpro_beat --tail 50

# Look for errors or warnings
```

---

## 🔌 Step 7: Update WordPress Plugin

### 7.1 Package Plugin

```bash
# On local machine
cd "c:/Users/olx/OneDrive/Desktop/PROJETOS 2026/PostPro/wordpress-plugin"

# Create zip
Compress-Archive -Path postpro -DestinationPath postpro-v2.0.0.zip -Force

# Upload to server or distribute
```

### 7.2 Install on WordPress

1. **Backup existing plugin** (if installed)
2. **Deactivate** old version
3. **Delete** old version
4. **Upload** `postpro-v2.0.0.zip`
5. **Activate** new version
6. **Configure** license key and API URL

### 7.3 Configure Plugin

```
Settings → PostPro

API URL: https://postpro.nuvemchat.com/api/v1
License Key: [your-license-key]

Click "Test Connection"
```

---

## 🧪 Step 8: Test End-to-End Flow

### 8.1 Create Agency with OpenRouter Key

```python
# Django shell
python manage.py shell

from apps.agencies.models import Agency

agency = Agency.objects.create(
    name="Test Agency",
    plan="pro"
)

# Set OpenRouter API key
agency.set_openrouter_key("your-openrouter-key")
agency.save()
```

### 8.2 Create AI Model Policy

```python
from apps.automation.models import AIModelPolicy

policy = AIModelPolicy.objects.create(
    agency=agency,
    preset_category="budget",
    planning_trends_model="perplexity/sonar",
    planning_titles_model="mistralai/mistral-nemo",
    article_model="openai/gpt-oss-120b",
    seo_model="openai/gpt-5-nano",
    image_provider="pollinations",
    pollinations_model="flux",
    is_active=True
)
```

### 8.3 Create Project

```python
from apps.projects.models import Project

project = Project.objects.create(
    agency=agency,
    name="Test WordPress Site",
    wordpress_url="https://your-wordpress-site.com",
    license_key="test-license-key"
)
```

### 8.4 Test Site Profile Sync

```python
from services.site_profile import SiteProfileService

service = SiteProfileService(project)
profile = service.get_or_create_profile()

print(f"Site: {profile.site_name}")
print(f"Categories: {len(profile.categories)}")
print(f"Posts: {len(profile.recent_posts)}")
```

### 8.5 Test Editorial Plan Generation

```python
from services.editorial_pipeline import EditorialPipelineService
from services.openrouter import OpenRouterService
from datetime import date

api_key = agency.get_openrouter_key()
openrouter = OpenRouterService(api_key)
pipeline = EditorialPipelineService(project, openrouter)

plan = pipeline.create_editorial_plan(
    keywords=["SEO", "content marketing", "AI tools"],
    start_date=date.today(),
    posts_per_day=1,
    use_trends=True
)

print(f"Plan ID: {plan.id}")
print(f"Status: {plan.status}")
print(f"Items: {plan.items.count()}")

# Check first few titles
for item in plan.items.all()[:5]:
    print(f"Day {item.day_index}: {item.title}")
```

### 8.6 Test WordPress Post Creation

```python
from apps.automation.tasks import publish_to_wordpress
from apps.automation.models import Post

# Create a test post
post = Post.objects.create(
    project=project,
    keyword="test keyword",
    title="Test Post from PostPro v2.0",
    content="<p>This is a test post to verify the new SEO integration.</p>",
    meta_description="Test meta description",
    external_id="test_post_001",
    post_status="draft",
    seo_data={
        "keyword": "test keyword",
        "seo_title": "Test Post SEO Title",
        "seo_description": "Test SEO description",
        "faq": [
            {
                "question": "What is this test?",
                "answer": "This is a test of the new PostPro v2.0 system."
            }
        ],
        "article_type": "BlogPosting"
    }
)

# Publish to WordPress
publish_to_wordpress.delay(str(post.id))

# Check WordPress for the post
```

---

## 📊 Step 9: Monitor Production

### Key Metrics to Watch

1. **Database Connections**
   - Check PostgreSQL connection pool
   - Monitor query performance

2. **Celery Workers**
   - Task completion rate
   - Failed tasks
   - Queue length

3. **API Response Times**
   - `/receive-post` endpoint
   - License validation
   - Health checks

4. **Error Rates**
   - Django logs
   - Celery logs
   - WordPress plugin errors

### Monitoring Commands

```bash
# Check database connections
docker exec -it postpro_db psql -U postgres -d postpro_db -c "SELECT count(*) FROM pg_stat_activity;"

# Check Redis queue length
docker exec -it postpro_redis redis-cli LLEN celery

# Check service health
docker service ps postpro_web
docker service ps postpro_worker
docker service ps postpro_beat
```

---

## 🐛 Troubleshooting

### Issue: Migrations Fail

```bash
# Check migration status
python manage.py showmigrations automation

# If stuck, fake the migration (ONLY if safe)
python manage.py migrate automation --fake

# Or rollback and retry
python manage.py migrate automation zero
python manage.py migrate automation
```

### Issue: Celery Tasks Not Running

```bash
# Check worker is running
docker service ps postpro_worker

# Check task registration
docker exec -it $(docker ps -q -f name=postpro_worker) celery -A config inspect registered

# Restart worker
docker service update --force postpro_worker
```

### Issue: WordPress Plugin Connection Fails

1. Check license key is correct
2. Verify API URL: `https://postpro.nuvemchat.com/api/v1`
3. Check firewall/CORS settings
4. Test endpoint manually with curl

---

## 📝 Post-Deployment Tasks

- [ ] Update documentation
- [ ] Notify users of new features
- [ ] Create tutorial videos
- [ ] Update pricing/plans if needed
- [ ] Monitor for 24-48 hours
- [ ] Collect user feedback

---

## 🎯 Success Criteria

✅ All services running  
✅ Migrations applied  
✅ New models visible in admin  
✅ Celery tasks registered  
✅ WordPress plugin connects  
✅ Test post created successfully  
✅ SEO data applied correctly  
✅ No errors in logs  

---

**Deployment Time Estimate:** 20-30 minutes  
**Rollback Plan:** Revert to previous Docker image if issues occur  
**Support:** Check logs and contact dev team if needed

🚀 **Ready to deploy!**
