# Website Scraper Update - v10 Alignment

## Overview
Updated the website scraping service to align with the v10 streamlined intake structure, removing assessment purpose questions and focusing on the 7 core organizational profile questions that can be inferred from public websites.

## Changes Made

### 1. Updated Keyword Mappings

#### Industry Detection (INT-ORG-01)
**Expanded from 7 to 14 industry categories:**
- Financial Services
- Healthcare
- Technology / Software
- Manufacturing
- Retail / E-commerce
- Energy / Utilities
- Government / Public Sector
- **Education** (new)
- **Professional Services** (new)
- **Media / Entertainment** (new)
- **Telecommunications** (new)
- **Transportation / Logistics** (new)
- **Insurance** (new)
- Other

#### Regulatory Frameworks (INT-REG-01)
**Expanded from 6 to 18 frameworks:**
- GDPR, SOX, HIPAA, PCI-DSS (original)
- CCPA, NIS2 (original)
- **DORA** (new - Digital Operational Resilience Act)
- **GLBA** (new - Gramm-Leach-Bliley)
- **FERPA** (new - Educational privacy)
- **FedRAMP** (new - Federal cloud)
- **CMMC** (new - Defense)
- **ITAR** (new - Export controls)
- **Export Controls** (new)
- **Whistleblowing Directive** (new - EU)
- **FISMA** (new - Federal security)
- **DFARS** (new - Defense)
- **ISO 27001** (new)
- None

#### Geographic Footprint (INT-ORG-03)
**New detection for 4 footprint types:**
- Global (all continents)
- Global (multi-region)
- Regional (multiple countries)
- Single country

#### Employee Count (INT-ORG-02)
**New detection for 7 size ranges:**
- 100,000+
- 20,000-100,000
- 5,000-20,000
- 1,000-5,000
- 251-1,000
- 51-250
- 1-50

#### IT Environment (INT-TECH-01)
**New detection for 5 environment types:**
- Cloud-native (100% cloud)
- Multi-cloud (AWS + Azure/GCP)
- Hybrid (on-prem + cloud)
- Primarily cloud (>70%)
- On-premises (>70% data centers)

#### Technology Platforms (INT-TECH-03)
**New detection for 12 platforms:**
- Microsoft 365
- Google Workspace
- AWS
- Azure
- GCP
- Salesforce
- SAP
- Oracle
- ServiceNow
- Slack
- Zoom
- Other

### 2. Updated Suggestion Logic

#### Before (v9 intake)
Returned suggestions for:
- `industry`
- `region`
- `size_band`
- `revenue_band`
- `regulated_flags`
- `data_types`

#### After (v10 intake)
Returns suggestions for:
- `INT-ORG-01`: Primary industry sector
- `INT-ORG-02`: Employee count
- `INT-ORG-03`: Geographic footprint
- `INT-ORG-05`: Annual revenue (inferred from employee count)
- `INT-REG-01`: Regulatory frameworks (multi-select, up to 5)
- `INT-TECH-01`: IT environment
- `INT-TECH-03`: Technology platforms (multi-select, up to 6)

### 3. Removed Assessment Purpose Logic

**Eliminated suggestions for:**
- Assessment frequency
- Assessment depth
- Question pack selection
- Auto-advance preference
- Risk appetite levels
- Monitoring preferences
- Program goals

**Rationale:** These questions are about user preferences for taking the assessment, not about the organization's profile. They cannot be inferred from public websites and should be set by the user directly.

### 4. Improved Revenue Inference

**Enhanced logic to map employee count → revenue range:**

```python
if "100,000" in employee_count → "$50B+"
elif "20,000" in employee_count → "$10B-$50B"
elif "5,000" in employee_count → "$1B-$10B"
elif "1,000" in employee_count → "$250M-$1B"
elif "251" in employee_count → "$50M-$250M"
elif "51" in employee_count → "$10M-$50M"
else → "<$10M"
```

This provides reasonable defaults based on typical revenue-per-employee ratios.

## API Response Format

### Before (v9)
```json
{
  "analysis": {
    "industries": ["Financial Services"],
    "regulations": ["GDPR", "SOX"],
    "data_types": ["PII", "Financial Data"],
    "regions": ["North America", "Europe"],
    "company_scale": ["Enterprise"]
  },
  "suggested_intake": {
    "industry": "Financial Services",
    "region": "North America",
    "size_band": "Enterprise",
    "revenue_band": "1B+",
    "regulated_flags": "GDPR, SOX",
    "data_types": "PII, Financial Data"
  },
  "persisted": false
}
```

### After (v10)
```json
{
  "analysis": {
    "industries": ["Financial Services"],
    "regulations": ["GDPR", "SOX", "DORA"],
    "footprints": ["Global (multi-region)"],
    "company_sizes": ["5,000-20,000"],
    "it_environments": ["Hybrid (on-prem + cloud)"],
    "platforms": ["Microsoft 365", "AWS", "Salesforce"]
  },
  "suggested_intake": {
    "INT-ORG-01": "Financial Services",
    "INT-ORG-02": "5,000-20,000",
    "INT-ORG-03": "Global (multi-region)",
    "INT-ORG-05": "$1B-$10B",
    "INT-REG-01": "GDPR, SOX, DORA",
    "INT-TECH-01": "Hybrid (on-prem + cloud)",
    "INT-TECH-03": "Microsoft 365, AWS, Salesforce"
  },
  "persisted": false
}
```

## Usage

### Endpoint
```
POST /api/v1/intake/scrape
```

### Request Payload
```json
{
  "base_url": "https://example.com",
  "assessment_id": "abc123",
  "persist": false
}
```

### Parameters
- **base_url** (required): The organization's website URL
- **assessment_id** (optional): If provided with persist=true, suggestions will be saved
- **persist** (optional, default=false): Whether to save suggestions to the assessment

### Response
Returns analysis results and suggested intake answers mapped to v10 question IDs.

## Coverage

### Questions Covered by Scraper (7/25 = 28%)
1. ✅ INT-ORG-01: Primary industry sector
2. ✅ INT-ORG-02: Employee count
3. ✅ INT-ORG-03: Geographic footprint
4. ❌ INT-ORG-04: Organizational maturity (not inferable)
5. ✅ INT-ORG-05: Annual revenue (inferred from employee count)
6. ✅ INT-REG-01: Regulatory frameworks (multi-select)
7. ❌ INT-REG-02: Data protection requirements (not reliably inferable)
8. ❌ INT-REG-03: Industry compliance obligations (too specific)
9. ❌ INT-REG-04: Cross-border transfers (not public)
10. ❌ INT-WF-01: Remote work policy (not always public)
11. ❌ INT-WF-02: Contractor percentage (not public)
12. ❌ INT-WF-03: Privileged user percentage (not public)
13. ❌ INT-WF-04: High-risk roles (not public)
14. ✅ INT-TECH-01: IT environment
15. ❌ INT-TECH-02: Cloud service usage (partially covered by TECH-01)
16. ✅ INT-TECH-03: Technology platforms (multi-select)
17. ❌ INT-PROG-01: Program maturity (not public)
18. ❌ INT-PROG-02: Dedicated team (not public)
19. ❌ INT-PROG-03: Executive sponsorship (not public)
20. ❌ INT-PROG-04: Annual budget (not public)
21. ❌ INT-PROG-05: Program focus areas (not public)
22. ❌ INT-CTX-01: Assessment frequency (user preference)
23. ❌ INT-CTX-02: Assessment depth (user preference)
24. ❌ INT-CTX-03: Question pack (user preference)
25. ❌ INT-CTX-04: Auto-advance (user preference)

### Rationale for Coverage
The scraper focuses on **organizational profile** questions (sections 1-2) that can be reliably inferred from public websites:
- Industry, size, footprint, revenue (Organization Profile)
- Regulatory frameworks, IT environment, platforms (Regulatory & Technology)

It **does not** attempt to infer:
- Internal program details (maturity, team size, budget)
- Workforce characteristics (remote policy, contractor %, privileged users)
- Assessment preferences (depth, frequency, question pack)

This prevents inaccurate guesses and respects that most intake data should come from the user directly.

## Benefits

### 1. Faster Intake Completion
- Pre-fills 7 key questions automatically
- Reduces manual entry by ~28%
- User only reviews/corrects instead of entering from scratch

### 2. Higher Data Quality
- Standardized matching to dropdown options
- No typos or inconsistent formatting
- Multi-select questions get up to 5-6 relevant options

### 3. Better User Experience
- "Smart intake" feels modern and helpful
- Reduces friction for first-time users
- Shows system understands their organization

### 4. Improved Accuracy
- Expanded keyword dictionaries (18 regulations vs 6)
- Better industry coverage (14 categories vs 7)
- Geographic footprint detection (new capability)
- IT environment detection (new capability)

## Testing

### Manual Test
```bash
# Start the backend
python main.py

# Test the scraper endpoint
curl -X POST http://localhost:8000/api/v1/intake/scrape \
  -H "Content-Type: application/json" \
  -d '{"base_url": "https://stripe.com", "persist": false}' | jq .
```

### Expected Output
```json
{
  "analysis": {
    "industries": ["Financial Services", "Technology / Software"],
    "regulations": ["PCI-DSS", "SOX"],
    "footprints": ["Global (all continents)"],
    "company_sizes": ["1,000-5,000"],
    "it_environments": ["Cloud-native (100% cloud)"],
    "platforms": ["AWS"]
  },
  "suggested_intake": {
    "INT-ORG-01": "Financial Services",
    "INT-ORG-02": "1,000-5,000",
    "INT-ORG-03": "Global (all continents)",
    "INT-ORG-05": "$250M-$1B",
    "INT-REG-01": "PCI-DSS, SOX",
    "INT-TECH-01": "Cloud-native (100% cloud)",
    "INT-TECH-03": "AWS"
  },
  "persisted": false
}
```

### Test Cases
1. **Financial Services:** Test with banks, fintech, investment firms
2. **Healthcare:** Test with hospitals, pharma, health insurers
3. **Technology:** Test with SaaS companies, cloud providers, software vendors
4. **Government:** Test with federal agencies, municipalities
5. **Multi-Region:** Test with global enterprises
6. **Multi-Regulatory:** Test with highly regulated industries (financial, healthcare)

## Limitations

### Cannot Infer (18/25 questions)
- Internal program maturity/capabilities
- Workforce composition (contractors, privileged users)
- Specific compliance obligations beyond major frameworks
- User assessment preferences
- Budget and resource allocation

### May Be Inaccurate
- **Employee count:** Often not published or outdated on website
- **Revenue:** Inferred from employee count (rough approximation)
- **IT environment:** May detect marketing claims vs reality
- **Platforms:** May miss platforms not mentioned on public pages

### Best Practices
1. **Always allow user to review/edit:** Treat suggestions as helpful hints, not truth
2. **Show confidence indicators:** If multiple industries detected, show all options
3. **Provide "Unknown" option:** Don't force a match if no good fit
4. **Log accuracy:** Track how often users accept vs modify suggestions

## Future Enhancements

### Potential Improvements
1. **LinkedIn Integration:** Scrape company page for more accurate employee count
2. **SEC Filing Integration:** For public companies, pull revenue from 10-K filings
3. **Crunchbase API:** Get funding, employee count, industry for startups
4. **Confidence Scoring:** Return confidence level (high/medium/low) for each suggestion
5. **Multi-Language Support:** Detect and parse non-English websites
6. **Job Posting Analysis:** Infer technology stack from engineering job postings
7. **News Article Analysis:** Parse recent news for regulatory mentions
8. **Privacy Policy Parsing:** Extract data types, regions, compliance frameworks

### Considerations
- Cost of API integrations (LinkedIn, Crunchbase)
- Rate limiting and IP blocking
- Privacy implications of aggressive scraping
- GDPR compliance for processing scraped data

## Conclusion

The scraper has been successfully updated to align with the v10 streamlined intake structure:

✅ **Expanded keyword coverage** (14 industries, 18 regulations)
✅ **New capabilities** (geographic footprint, IT environment, platforms)
✅ **Removed assessment purpose** questions (user preferences)
✅ **Improved inference logic** (employee count → revenue mapping)
✅ **Question ID mapping** (INT-ORG-01, INT-REG-01, etc.)
✅ **Multi-select support** (up to 5-6 options per question)

The scraper now provides intelligent suggestions for 7 of 25 intake questions (28%), focusing on organizational profile data that can be reliably inferred from public websites.

---

**File Updated:** `app/modules/assessment/scraper.py`
**Lines Changed:** ~150 lines (keyword mappings + suggestion logic)
**Status:** ✅ Ready for testing
