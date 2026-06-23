# Parts Module Technical Debt

**Version:** 1.0  
**Date:** June 23, 2026  
**Status:** Intentionally Deferred

---

## Overview

This document tracks intentionally deferred technical debt items for the Parts Module v1.0. These items were consciously postponed to maintain the stabilization sprint timeline and will be addressed in future iterations. No items listed here are bugs or regressions; all are enhancements or architectural improvements.

---

## High Priority (Post-Freeze)

### 1. Target Overlay Expansion
**Priority:** High  
**Effort:** 2-3 hours  
**Risk:** Low

**Description:**
Extend target overlay functionality from monthly trend chart to additional charts in Parts Executive. Currently, only the monthly trend chart has target overlay with achievement % and variance.

**Scope:**
- Add target overlay to Category Contribution Waterfall chart
- Add target overlay to Category Growth Heatmap
- Verify target data availability for all chart types
- Ensure consistent styling across all target overlays

**Dependencies:**
- Requires verification of target datasource availability for category-level targets
- May require additional target data structure if category targets not available

**Success Criteria:**
- Target lines render on all applicable charts
- Achievement metrics display consistently
- Graceful degradation when target data unavailable

---

### 2. Health Scorecard Implementation
**Priority:** High  
**Effort:** 4-6 hours  
**Risk:** Low

**Description:**
Create a dedicated Health Scorecard page that expands on the current Health Score KPI card in Parts Executive. The scorecard would provide comprehensive health analysis across all locations with drill-down capabilities.

**Scope:**
- Create new page: Parts Health Scorecard
- Display location-level health scores in sortable table format
- Add health score trend chart (historical health over time)
- Include health score component breakdown (Margin, Oil Pen, Parts/JC, Growth)
- Add drill-down from scorecard to Parts Detail
- Implement health score alerts/notifications for declining health

**Dependencies:**
- Health Score calculation already implemented in parts_executive.py
- Can reuse existing calculation logic
- Requires design approval for scorecard layout

**Success Criteria:**
- Health Scorecard page renders correctly
- Location-level health scores displayed in sortable table
- Health score trend chart shows historical performance
- Drill-down to Parts Detail works
- Component breakdown shows contribution of each factor

---

## Medium Priority

### 3. Advanced Drill-Through
**Priority:** Medium  
**Effort:** 3-4 hours  
**Risk:** Low

**Description:**
Extend drill-through functionality to support additional navigation paths beyond the current Executive → Detail flow.

**Scope:**
- Add drill-through from category panels in Parts Executive to Sales Mix (filtered by category)
- Add drill-through from Command Center Parts KPI to Parts Executive
- Add drill-through from Parts Detail to Sales Mix (filtered by location)
- Extend drill parameter support for additional contexts
- Update drill-through context banners to show more detailed source information

**Dependencies:**
- Builds on existing Sprint 4A drill-through infrastructure
- Requires additional state parameters for new navigation paths
- May require UI updates for drill-through indicators

**Success Criteria:**
- Additional drill-through paths work correctly
- Filters preserved across all navigation paths
- Context banners show correct source information
- No breaking changes to existing drill-through flow

---

### 4. Export Optimization
**Priority:** Medium  
**Effort:** 2-4 hours  
**Risk:** Low

**Description:**
Optimize export functionality for large datasets. Current export may be slow for very large tables with many rows or columns.

**Scope:**
- Add pagination to large exports (CSV, Excel)
- Implement streaming for CSV/Excel exports
- Add progress indicators for long-running exports
- Optimize PDF generation for large tables
- Add export timeout handling

**Dependencies:**
- Requires modifications to export_service.py
- May require UI updates for progress indicators
- Should maintain backward compatibility with existing export flow

**Success Criteria:**
- Exports complete faster for large datasets
- User feedback during long-running exports
- No memory issues with large exports
- Backward compatible with existing export buttons

---

## Low Priority (Infrastructure)

### 5. Sales Mix Merge Architectural Proposal
**Priority:** Low  
**Effort:** 8-12 hours (analysis only)  
**Risk:** Medium

**Description:**
Evaluate and propose architectural changes to merge Sales Mix into Parts Detail as a tabbed interface. This would consolidate the three Parts module pages into a more cohesive user experience.

**Scope:**
- Analyze current data flow and dependencies
- Evaluate tab-based UI pattern vs separate pages
- Assess impact on drill-through navigation
- Propose data layer consolidation opportunities
- Evaluate unified target loader architecture
- Create architectural proposal document
- **Do NOT implement - only analysis and proposal**

**Dependencies:**
- Requires architectural review
- Requires stakeholder approval
- May impact other modules if approved
- Should be evaluated as part of broader module consolidation strategy

**Success Criteria:**
- Comprehensive architectural proposal document
- Risk assessment for proposed changes
- Migration plan if approved
- No code changes in this sprint

---

### 6. Unified Target Loader
**Priority:** Low  
**Effort:** 4-6 hours  
**Risk:** Low

**Description:**
Create a unified target loader service that can be used across all modules (Parts, Labour, Body Shop, etc.) instead of module-specific target loading logic.

**Scope:**
- Create services/target_loader.py
- Consolidate target loading logic from all modules
- Provide standardized target API
- Handle target data validation and caching
- Migrate Parts module to use unified loader
- Plan migration for other modules

**Dependencies:**
- Should be evaluated as part of Sprint 4E (Sales Mix Merge) analysis
- May require coordination with other module owners
- Should maintain backward compatibility during migration

**Success Criteria:**
- Single source of truth for target loading
- Consistent target API across modules
- Improved maintainability
- No breaking changes to existing modules

---

### 7. Data Layer Consolidation
**Priority:** Low  
**Effort:** 12-16 hours  
**Risk:** Medium

**Description:**
Consolidate shared aggregation services into a unified data layer. Currently, each module has its own aggregation logic that could be centralized.

**Scope:**
- Analyze current aggregation patterns across modules
- Identify shared aggregation operations
- Create unified aggregation service layer
- Migrate modules to use shared services
- Maintain backward compatibility during migration
- Document new aggregation API

**Dependencies:**
- Should be evaluated as part of Sprint 4E (Sales Mix Merge) analysis
- Requires coordination with other module owners
- May require significant refactoring
- Should maintain backward compatibility

**Success Criteria:**
- Reduced code duplication
- Consistent aggregation logic
- Improved performance through shared caching
- No breaking changes to existing modules

---

## Low Priority (Code Quality)

### 8. Category Data Fallback Logic Centralization
**Priority:** Low  
**Effort:** 1-2 hours  
**Risk:** Low

**Description:**
Category data fallback logic is currently scattered across multiple functions in parts_detail.py. This could be centralized into a single helper function for better maintainability.

**Scope:**
- Identify all locations where category data fallback is used
- Create single helper function for category data availability check
- Replace scattered fallback logic with centralized helper
- Add unit tests for fallback logic

**Dependencies:**
- No external dependencies
- Pure refactoring effort
- Should not change business logic

**Success Criteria:**
- Single source of truth for category data fallback
- Code is more readable and maintainable
- No functional changes
- Unit tests pass

---

### 9. State Management Namespace Enforcement
**Priority:** Low  
**Effort:** 2-3 hours  
**Risk:** Low

**Description:**
Parts module uses 'parts_' prefix for state keys, but this is not enforced by the framework. Other modules may have inconsistent naming conventions.

**Scope:**
- Evaluate framework-level namespace enforcement
- Propose namespace validation mechanism
- Document namespace conventions
- Optionally add linting rules for namespace compliance

**Dependencies:**
- Requires framework-level changes
- Should be coordinated with framework team
- May impact other modules

**Success Criteria:**
- Consistent namespace usage across all modules
- Framework-level enforcement (if approved)
- Documented namespace conventions

---

### 10. Chart Legend Positioning
**Priority:** Low  
**Effort:** 1-2 hours  
**Risk:** Low

**Description:**
Some charts have hardcoded legend positions. This could be centralized in ChartEngine for consistency.

**Scope:**
- Identify all charts with hardcoded legend positions
- Add legend positioning parameters to ChartEngine
- Migrate charts to use centralized legend positioning
- Document legend positioning best practices

**Dependencies:**
- Requires modifications to ChartEngine
- Should maintain backward compatibility
- May require coordination with UI team

**Success Criteria:**
- Consistent legend positioning across all charts
- Centralized legend positioning logic
- No visual regressions
- Documented best practices

---

## Summary

### Total Items: 10
### High Priority: 2
### Medium Priority: 2
### Low Priority: 6

### Implementation Sequence Recommendation
1. **Sprint 4C Deferred (Post-Freeze):** Target Overlay Expansion, Health Scorecard
2. **Medium Priority:** Advanced Drill-Through, Export Optimization
3. **Architectural Analysis:** Sales Mix Merge (Sprint 4E)
4. **Infrastructure (if Sprint 4E approved):** Unified Target Loader, Data Layer Consolidation
5. **Code Quality:** Category Fallback Centralization, Namespace Enforcement, Legend Positioning

### Notes
- All items are intentionally deferred, not bugs
- No items are regressions or critical issues
- All items can be addressed in future iterations without impacting v1.0 stability
- Sprint 4C deferred items (1-2) are highest priority for post-freeze implementation
- Infrastructure items (5-7) should be evaluated as part of architectural planning
- Code quality items (8-10) can be addressed during regular maintenance
