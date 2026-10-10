# Azure DevOps Field Specification Examples

Concrete `wit_create_work_item` field payloads for each work item type. Rich text fields use
`"format": "Markdown"`; newlines are escaped as `\n` inside the JSON string.

Field reference names used below:

| Purpose             | Reference name                                |
| ------------------- | --------------------------------------------- |
| Title               | `System.Title`                                |
| Description         | `System.Description`                          |
| Story Points        | `Microsoft.VSTS.Scheduling.StoryPoints`       |
| Acceptance Criteria | `Microsoft.VSTS.Common.AcceptanceCriteria`    |
| Iteration Path      | `System.IterationPath`                        |
| Repro Steps         | `Microsoft.VSTS.TCM.ReproSteps`               |
| System Info         | `Microsoft.VSTS.TCM.SystemInfo`               |
| Severity            | `Microsoft.VSTS.Common.Severity`              |
| Priority            | `Microsoft.VSTS.Common.Priority`              |

---

## User Story

```json
{
  "fields": [
    {
      "name": "System.Title",
      "value": "Allow users to upload profile pictures"
    },
    {
      "name": "System.Description",
      "value": "As a registered user, I want to upload a profile picture so that other users can identify me.\n\n#### Additional Context\n\n- Support common image formats\n- Implement size restrictions for storage optimization",
      "format": "Markdown"
    },
    {
      "name": "Microsoft.VSTS.Scheduling.StoryPoints",
      "value": 5
    },
    {
      "name": "Microsoft.VSTS.Common.AcceptanceCriteria",
      "value": "### 1. Upload Functionality\n\n- [ ] User can select image from device\n- [ ] Upload accepts JPG, PNG, and GIF up to 10MB\n\n### 2. Validation\n\n- [ ] Error displays for unsupported formats\n- [ ] Error displays when file exceeds 10MB\n\n### 3. Display\n\n- [ ] Thumbnail generates at 150x150 pixels\n- [ ] Image displays on user profile",
      "format": "Markdown"
    },
    {
      "name": "System.IterationPath",
      "value": "ProjectName\\Sprint 1"
    }
  ]
}
```

---

## Bug

Bugs put expected/actual behavior and reproduction steps in `ReproSteps`, not `Description`.

```json
{
  "fields": [
    {
      "name": "System.Title",
      "value": "Login button unresponsive on mobile Safari"
    },
    {
      "name": "Microsoft.VSTS.TCM.ReproSteps",
      "value": "### Steps to Reproduce\n\n1. Open application on iOS Safari\n2. Enter valid credentials\n3. Tap Login button\n4. Observe button does not respond\n\n### Expected Behavior\n\nUser is authenticated and redirected to dashboard.\n\n### Actual Behavior\n\nButton tap is not registered; no action occurs.",
      "format": "Markdown"
    },
    {
      "name": "Microsoft.VSTS.TCM.SystemInfo",
      "value": "- Device: iPhone 14 Pro\n- OS: iOS 17.2\n- Browser: Safari 17.2\n- App Version: 2.3.1",
      "format": "Markdown"
    },
    {
      "name": "Microsoft.VSTS.Common.Severity",
      "value": "2 - High"
    },
    {
      "name": "Microsoft.VSTS.Common.Priority",
      "value": "1"
    }
  ]
}
```

---

## Issue (Technical)

```json
{
  "fields": [
    {
      "name": "System.Title",
      "value": "Implement caching layer for API responses"
    },
    {
      "name": "System.Description",
      "value": "We need a Redis caching layer to reduce database load and improve response times.\n\n#### Additional Context\n\n- Current avg response time: 800ms\n- Target response time: 200ms\n- Expected cache hit ratio: 70%",
      "format": "Markdown"
    },
    {
      "name": "Microsoft.VSTS.Scheduling.StoryPoints",
      "value": 8
    },
    {
      "name": "Microsoft.VSTS.Common.AcceptanceCriteria",
      "value": "### 1. Implementation\n\n- [ ] Redis cache configured and connected\n- [ ] Frequently accessed endpoints use cache\n\n### 2. Performance\n\n- [ ] Cached responses return in under 100ms\n- [ ] Cache invalidation works correctly\n\n### 3. Monitoring\n\n- [ ] Cache hit/miss metrics available in dashboard",
      "format": "Markdown"
    }
  ]
}
```
