# Community Stakeholder Profile Enhancement Design

**Date:** 2026-03-05
**Status:** Approved

## Overview

Transform community stakeholder profiles from generic role descriptions into detailed, ACS-based "digital doubles" that represent authentic Chicago residents across key demographic and geographic segments. Profiles will be grounded in Census data while including ethnographic details that reflect lived experiences.

## Objectives

1. Create 8 community stakeholder profiles representing Chicago's demographic diversity
2. Ground profiles in ACS 2022 5-year estimates for methodological rigor
3. Use geographic stratification to capture place-based concerns
4. Include ethnographic realism (neighborhoods, institutions, daily patterns) for authenticity
5. Document methodology in README for transparency and reproducibility

## Sampling Framework

### Strategy: Geographic Stratification

**Rationale:** Stadium and urban development projects have geographically differentiated impacts. Neighborhoods vary systematically in demographics, housing markets, transit access, and vulnerability to displacement. Geographic sampling ensures representation of these place-based differences.

**Distribution:** 8 profiles across 4 zones (2 per zone)

### Geographic Zones and Profile Allocation

#### South Side (2 profiles)
1. **Bronzeville/South Shore area**
   - Target: Established middle-income homeowner
   - Archetype: Retired public sector worker, long-term resident
   - Key concerns: Neighborhood legacy, property values, community institutions

2. **Englewood/Greater Grand Crossing area**
   - Target: Working-class renter with family
   - Archetype: Service worker, transit-dependent, young household
   - Key concerns: Displacement risk, transit access, family-oriented amenities

#### West Side (2 profiles)
3. **Pilsen/Lower West Side**
   - Target: Low-income service worker, renter
   - Archetype: Hospitality/service sector, limited English proficiency
   - Key concerns: Rent increases, gentrification, language access, affordability

4. **Austin/West Garfield Park**
   - Target: Small business owner/homeowner
   - Archetype: Lower-middle income entrepreneur with property stake
   - Key concerns: Business viability, employment, community investment

#### North Side (2 profiles)
5. **Rogers Park/Uptown**
   - Target: Lower-middle renter, public sector
   - Archetype: CPS teacher or city worker, diverse household
   - Key concerns: Rent affordability, school quality, transit access

6. **Lincoln Park/Lakeview**
   - Target: Upper-middle homeowner, professional
   - Archetype: White-collar professional, shorter tenure
   - Key concerns: Amenities, property values, quality of life

#### Loop-adjacent/Near South (2 profiles)
7. **South Loop**
   - Target: Higher-income professional renter
   - Archetype: Young professional, mobile, career-focused
   - Key concerns: Economic development, convenience, urban vitality

8. **Near West Side/Illinois Medical District**
   - Target: Middle-income homeowner, healthcare sector
   - Archetype: Established family, balancing stability and growth
   - Key concerns: Neighborhood schools, safety, property values

### Within-Zone Variation

Each zone's 2 profiles vary by:
- **Housing tenure** (own vs. rent)
- **Income level** (low, lower-middle, middle, upper-middle)
- **Life stage** (young family, mid-career, established, retired)
- **Employment sector** (service, public, professional, business owner)

This creates intersectional diversity while maintaining geographic structure.

## Profile Structure

### Template

Each profile follows this comprehensive structure:

```markdown
# [Full Name]

## Personal Profile
- Age: [specific age]
- Household composition: [detailed]
- Years in Chicago/neighborhood: [specific]
- Primary language: [if relevant]

## Location & Housing
- Neighborhood: [specific area with landmarks]
- Address context: [housing type and details]
- Housing tenure: [Own/Rent + specifics]
- Monthly housing cost: [specific amount]
- Property value (if owner): [approximate value]

## Economic Profile
- Occupation: [specific job title]
- Employment sector: [industry]
- Annual household income: [specific amount]*
- Education: [highest level completed]
- Commute: [mode, time, route with specific details]

## Community Context
- Neighborhood ties: [specific institutions, businesses, places]
- Community involvement: [if any]
- Local patterns: [authentic daily life details]

## Stakeholder Perspective
- Primary concerns: [3-4 development-related concerns]
- Priorities: [policy decision criteria]
- Perspective on development: [brief characterization]

---
*Methodology notes: [ACS table references]
```

### Section Design Rationale

- **Personal Profile:** Establishes demographic context without race coding
- **Location & Housing:** Place-based identity and housing vulnerability
- **Economic Profile:** Income, opportunity, and mobility constraints
- **Community Context:** Rootedness and authenticity through specific institutions
- **Stakeholder Perspective:** How demographics translate to policy concerns

## Data Sourcing

### Primary Source: ACS 2022 5-year Estimates

**Key tables:**
- **B19013:** Median household income by geography/occupation
- **B25003:** Housing tenure (owner/renter distribution)
- **B25064:** Median gross rent
- **B25077:** Median home values
- **B08303:** Travel time to work
- **B08301:** Means of transportation to work
- **B15003:** Educational attainment
- **C24010:** Occupation by sex
- **B11001:** Household types and sizes
- **B16004:** Language spoken at home and English-speaking ability

**Geographic granularity:**
- Use Community Area data where available (Chicago's 77 areas)
- Fall back to census tract or Cook County when Community Area unavailable
- Cross-reference with City of Chicago data portal

### Supplementary Authenticity Sources

**Not statistically sampled, but used for realism:**
- Real street names and intersections (Google Maps)
- Actual CTA routes and approximate travel times (CTA trip planner)
- Existing businesses, schools, churches (local searches)
- Neighborhood institutions and landmarks (community area profiles)

**Principle:** Ethnographic details must be *plausible* for the demographic profile, even if not statistically derived.

## Methodology Notes in Profiles

Each profile will include a methodology footnote at the bottom:

```markdown
---
*Methodology notes:
- Income: ACS 2022 Table B19013 (median HH income, [occupation], Cook County)
- Rent/Home value: ACS 2022 Table B25064/B25077 (Community Area [number])
- Commute: ACS 2022 Table B08303 (travel time distribution) + CTA trip planner
```

## Example Profile

See design document for full Rosa Delgado example (Pilsen renter, service worker profile).

## README Documentation

Add new section: **"Community Stakeholder Methodology"**

### Content:
1. **Overview** of the digital doubles approach
2. **Sampling framework** (geographic stratification rationale)
3. **Data sources** (ACS tables, supplementary sources)
4. **Profile structure** (what each section represents)
5. **Interpreting profiles** in deliberation context
6. **Limitations and design choices**:
   - Race/ethnicity not explicitly coded (demographic data inferred through other variables)
   - Ethnographic details are illustrative, not statistical samples
   - Profiles represent *types* not specific individuals
7. **References** to ACS documentation

### Placement in README:
After "Adding or editing personas" section, before "Lint and test"

## Implementation Scope

### New Files (8 total)
Replace existing 6 community stakeholder files with new 8 profiles:

1. `agents/community/bronzeville_homeowner.md`
2. `agents/community/englewood_renter.md`
3. `agents/community/pilsen_renter.md`
4. `agents/community/austin_business_owner.md`
5. `agents/community/rogers_park_renter.md`
6. `agents/community/lincoln_park_homeowner.md`
7. `agents/community/south_loop_renter.md`
8. `agents/community/near_west_homeowner.md`

### Modified Files
- `README.md` - add Community Stakeholder Methodology section

### Removed Files
- Existing 6 community `.md` files (will be archived or replaced)

## Quality Criteria

Each profile must:
1. ✅ Include all 5 sections (Personal, Location, Economic, Community, Stakeholder)
2. ✅ Reference specific ACS tables in methodology notes
3. ✅ Include specific Chicago places (streets, businesses, transit)
4. ✅ Have income, housing cost, and commute details
5. ✅ Avoid explicit race/ethnicity coding
6. ✅ Feel authentic and specific (not generic)
7. ✅ Connect demographic details to stakeholder concerns

## Success Metrics

- Profiles are used in deliberation without confusion
- Reviewers can verify ACS data grounding
- Profiles feel distinct and realistic
- Geographic and socioeconomic diversity is represented
- Methodology is transparent and reproducible

## Future Enhancements

- Add more profiles for finer-grained representation
- Include profiles from Northwest/Southwest zones
- Create seasonal workers or gig economy profiles
- Add business owner perspectives beyond West Side
- Extend to suburban Cook County stakeholders

---

**Approved by:** User
**Next step:** Create implementation plan (writing-plans skill)
