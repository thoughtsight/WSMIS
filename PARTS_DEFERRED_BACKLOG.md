# Parts Module Deferred Backlog

**Date:** June 23, 2026  
**Status:** DEFERRED POST-FREEZE

---

## Sprint 4C: Target Overlay Support

**Priority:** Medium  
**Risk:** Low  
**Effort:** 2-3 hours

### Description
Add MSIL target/benchmark overlay to monthly trend charts in Parts Executive. This would allow users to compare actual performance against MSIL targets directly on the trend charts.

### Implementation Scope
- Verify target datasource availability in targets_df
- Add target line overlay to Parts Executive monthly trend chart
- Use dashed line with distinct color for target overlay
- Add legend entry for target line
- Handle cases where target data is unavailable

### Files to Modify
- `views/commercial/parts_executive.py` (monthly trend chart in _render_charts)

### Dependencies
- Target datasource verification required
- May require additional target loading logic in app.py

### Success Criteria
- Target line renders on monthly trend chart when data available
- Target line uses appropriate styling (dashed, distinct color)
- Graceful degradation when target data unavailable
- No performance impact

---

## Sprint 4D: Health Scorecard Implementation

**Priority:** Medium  
**Risk:** Low  
**Effort:** 4-6 hours

### Description
Create a dedicated Health Scorecard page that expands on the current Health Score KPI card. The scorecard would provide comprehensive health analysis across all locations with drill-down capabilities.

### Implementation Scope
- Create new page: Parts Health Scorecard
- Display location-level health scores in table format
- Add health score trend chart (historical health over time)
- Include health score component breakdown (Margin, Oil Pen, Parts/JC, Growth)
- Add drill-down from scorecard to Parts Detail
- Implement health score alerts/notifications

### Files to Modify
- Create: `views/commercial/parts_health_scorecard.py`
- Modify: `app.py` (add page routing)
- Modify: `views/dashboard_common.py` (if shared components needed)

### Dependencies
- Health Score calculation already implemented in parts_executive.py
- Can reuse existing calculation logic

### Success Criteria
- Health Scorecard page renders correctly
- Location-level health scores displayed in sortable table
- Health score trend chart shows historical performance
- Drill-down to Parts Detail works
- Component breakdown shows contribution of each factor

---

## Sprint 4E: Architectural Proposal for Sales Mix Merge

**Priority:** Low  
**Risk:** Medium  
**Effort:** 8-12 hours (analysis only)

### Description
Evaluate and propose architectural changes to merge Sales Mix into Parts Detail as a tabbed interface. This would consolidate the three Parts module pages into a more cohesive user experience.

### Implementation Scope
- Analyze current data flow and dependencies
- Evaluate tab-based UI pattern vs separate pages
- Assess impact on drill-through navigation
- Propose data layer consolidation opportunities
- Evaluate unified target loader architecture
- Create architectural proposal document
- Do NOT implement - only analysis and proposal

### Files to Analyze
- `views/commercial/parts_executive.py`
- `views/commercial/parts_detail.py`
- `views/commercial/sales_mix.py`
- `services/aggregation_cache.py`
- `app.py` (routing)

### Dependencies
- Requires architectural review
- Requires stakeholder approval
- May impact other modules

### Success Criteria
- Comprehensive architectural proposal document
- Risk assessment for proposed changes
- Migration plan if approved
- No code changes in this sprint

---

## Additional Non-Critical Items

### Unified Target Loader

**Priority:** Low  
**Risk:** Low  
**Effort:** 4-6 hours

### Description
Create a unified target loader service that can be used across all modules (Parts, Labour, Body Shop, etc.) instead of module-specific target loading logic.

### Implementation Scope
- Create `services/target_loader.py`
- Consolidate target loading logic from all modules
- Provide standardized target API
- Handle target data validation and caching

### Files to Modify
- Create: `services/target_loader.py`
- Modify: All module files that load targets

### Success Criteria
- Single source of truth for target loading
- Consistent target API across modules
- Improved maintainability

---

### Data Layer Consolidation

**Priority:** Low  
**Risk:** Medium  
**Effort:** 12-16 hours

### Description
Consolidate shared aggregation services into a unified data layer. Currently, each module has its own aggregation logic that could be centralized.

### Implementation Scope
- Analyze current aggregation patterns across modules
- Identify shared aggregation operations
- Create unified aggregation service layer
- Migrate modules to use shared services
- Maintain backward compatibility during migration

### Files to Analyze
- `services/aggregation_cache.py`
- `utils/aggregations.py`
- All module view files

### Success Criteria
- Reduced code duplication
- Consistent aggregation logic
- Improved performance through shared caching
- No breaking changes to existing modules

---

### Export Optimization

**Priority:** Low  
**Risk:** Low  
**Effort:** 2-4 hours

### Description
Optimize export functionality for large datasets. Current export may be slow for very large tables.

### Implementation Scope
- Add pagination to large exports
- Implement streaming for CSV/Excel exports
- Add progress indicators for long-running exports
- Optimize PDF generation for large tables

### Files to Modify
- `services/export_service.py`

### Success Criteria
- Exports complete faster for large datasets
- User feedback during long-running exports
- No memory issues with large exports

---

### Advanced Drill-Through

**Priority:** Low  
**Risk:** Low  
**Effort:** 3-4 hours

### Description
Extend drill-through functionality to support additional navigation paths:
- Category panel in Parts Executive → Sales Mix (filtered by category)
- Command Center Parts KPI → Parts Executive
- Parts Detail → Sales Mix (filtered by location)

### Implementation Scope
- Add drill-through from category panels
- Add drill-through from Command Center
- Extend drill parameter support for additional contexts
- Update drill-through context banners

### Files to Modify
- `views/commercial/parts_executive.py`
- `views/commercial/parts_detail.py`
- `views/dashboard_common.py`

### Success Criteria
- Additional drill-through paths work correctly
- Filters preserved across all navigation paths
- Context banners show correct source information

---

## Backlog Prioritization

### High Priority (Post-Freeze)
1. **Sprint 4C: Target Overlay Support** - Medium effort, high value
2. **Sprint 4D: Health Scorecard Implementation** - Medium effort, high value

### Medium Priority
3. **Advanced Drill-Through** - Low effort, improves workflow
4. **Export Optimization** - Low effort, improves UX

### Low Priority
5. **Sprint 4E: Sales Mix Merge (Architectural Proposal)** - Analysis only
6. **Unified Target Loader** - Infrastructure improvement
7. **Data Layer Consolidation** - Infrastructure improvement

---

## Implementation Sequence Recommendation

1. **Sprint 4C** - Target Overlay (quick win, high value)
2. **Sprint 4D** - Health Scorecard (completes health analysis feature)
3. **Advanced Drill-Through** - Improves workflow (builds on Sprint 4A)
4. **Export Optimization** - UX improvement
5. **Sprint 4E** - Architectural analysis (decision point)
6. **Unified Target Loader** - Infrastructure (if Sprint 4E approved)
7. **Data Layer Consolidation** - Infrastructure (if Sprint 4E approved)

---

## Notes

- All items in this backlog are non-critical
- No implementation should begin until Parts Module freeze is approved
- Sprint 4C and 4D are highest priority for post-freeze implementation
- Sprint 4E is an architectural decision that may impact other items
- Infrastructure items (Unified Target Loader, Data Layer Consolidation) should be evaluated as part of Sprint 4E analysis
