# Known Limitations

This document tracks known constraints, deferred items, and future enhancements for the WSMIS v1.0.0-rc1 release.

## Current Limitations

1. **Large Dataset Memory Spikes**
   - The application currently processes all data in-memory using Pandas. If the Google Sheet grows beyond 100,000 rows, the application may experience memory pressure leading to increased load times.
   
2. **Real-Time Data Refresh**
   - Data is cached for 300 seconds (5 minutes) by default. Edits made in the Google Sheet will not appear instantaneously. Users must use the "🔄 Refresh" button in the header or wait for the cache to expire.

3. **External API Dependencies**
   - The AI Narrative Report relies on the external Anthropic API. If the Anthropic service experiences downtime or the API key limit is reached, the AI narrative generation will fail gracefully, but the feature will be unavailable.

4. **Internal Audit App Architecture**
   - The `internal_audit_app.py` is currently a legacy monolithic script loaded dynamically. It does not perfectly adhere to the new decoupled UI component architecture. 

## Future Enhancements

1. **Database Migration**
   - **Target:** v2.0
   - **Plan:** Migrate from Google Sheets as the primary data source to a robust relational database (e.g., PostgreSQL or BigQuery) to handle multi-year historical data efficiently.

2. **User Authentication & Role-Based Access Control (RBAC)**
   - **Target:** v1.1
   - **Plan:** Implement distinct logins for Advisors, Workshop Managers, and Executives, restricting views based on user roles (e.g., an Advisor can only see their own scorecard).

3. **Automated Email Reports**
   - **Target:** v1.2
   - **Plan:** Build a background cron job to automatically compile the MIS Summary Excel and email it to the Executive team every Monday morning.

## Deferred Items

1. **Mobile-First Responsive Redesign**
   - *Deferred*: The current dashboard is responsive but optimized primarily for iPad/Desktop viewing. Dedicated mobile views for smartphones are deferred.
   
2. **Bodyshop (BS) Specific Scorecards**
   - *Deferred*: The Advisor Scorecard currently evaluates all service types under a unified framework. Distinct scoring metrics specific to Bodyshop operations are deferred.
