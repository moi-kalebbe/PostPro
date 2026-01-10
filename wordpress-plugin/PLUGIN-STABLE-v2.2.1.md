# PostPro WordPress Plugin - Documentation

## Current Stable Version: v2.2.1

**Tag**: `v2.2.1-stable`
**Commit**: `2930cd0`
**Date**: 2026-01-10

## Files Location

- **Source**: `wordpress-plugin/postpro/`
- **ZIP for installation**: `C:\Users\olx\OneDrive\Desktop\postpro.zip`

## To Restore This Version

```bash
git checkout v2.2.1-stable -- wordpress-plugin/
```

## Key Configuration

- **API URL**: `https://postpro.nuvemchat.com/api/v1`
- **Validate License Endpoint**: `/validate-license`

## Features

- ✅ License validation working
- ✅ Test connection button functional
- ✅ Sync profile working
- ✅ Keywords form
- ✅ Editorial plan display
- ✅ Uninstall hooks for proper plugin deletion

## Known Limitations

### Newspaper Theme Compatibility
The editorial plan table displays with vertical/broken text in the Newspaper WordPress theme due to aggressive CSS overrides in that theme. The plugin works correctly on other themes (tested with Hello theme).

**Workaround**: Use a different theme or apply custom CSS fixes specific to Newspaper.

## ZIP Structure

The ZIP file must have this structure for WordPress to install correctly:

```
postpro.zip
└── postpro/
    ├── postpro.php
    └── assets/
        ├── css/
        └── js/
```

## Creating New ZIP

```powershell
$tempDir = "temp-zip"
Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path "$tempDir\postpro" -Force | Out-Null
Copy-Item -Path "wordpress-plugin\postpro\*" -Destination "$tempDir\postpro" -Recurse -Force
Compress-Archive -Path "$tempDir\postpro" -DestinationPath "postpro.zip" -Force
Remove-Item $tempDir -Recurse -Force
```

## Backend Endpoints Used

| Plugin Action | HTTP Method | Endpoint |
|--------------|-------------|----------|
| Test Connection | GET | /validate-license |
| Sync Profile | POST | /project/sync-profile |
| Get Editorial Plan | GET | /project/editorial-plan |
| Save Keywords | POST | /project/keywords |
| Approve All | POST | /project/editorial-plan/approve-all |
| Reject Plan | POST | /project/editorial-plan/reject |
