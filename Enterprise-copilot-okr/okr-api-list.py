"""
OKR API Endpoints for Selamnew AI Copilot
Base URL: https://test-okr-backend.ienetworks.co/api/v1
"""

# ========================================
# USER OKR APIs
# ========================================

# GET /objective/:userId - Get user's objectives
# GET /objective/user/:userId - Calculate user's OKR score
# GET /key-results/user/:userId - Get user's key results

# ========================================
# TEAM OKR APIs
# ========================================

# POST /objective/team - Get team OKRs with filters
# POST /objective/team-okr - Get team OKRs (simple)
# POST /objective/supervisor-okr - Get supervisor's OKRs

# ========================================
# COMPANY OKR APIs
# ========================================

# POST /objective/company/okr/:userId - Get company OKR
# POST /objective/company-okr - Get company OKR (simple)
# POST /objective/get-okr-progress/all-employees - Get all employees OKR progress

# ========================================
# PLANNING & PERIODS APIs
# ========================================

# GET /planning-periods - Get all planning periods
# GET /planning-periods/:id - Get single planning period
# GET /planning-periods/assignment/assignedUser/:userId - Get user's assigned planning periods
# GET /planning-periods/parent-hierarchy/:planningPeriodId/user/:userId - Get parent hierarchy
# GET /planning-periods/child-hierarchy/:planningPeriodId/user/:userId - Get child hierarchy

# ========================================
# REPORTS & PERFORMANCE APIs
# ========================================

# GET /okr-report/rock-star/user - Get top performers
# GET /okr-report/performance/user - Get user performance data
# GET /okr-report/:reportId - Get report by ID
# POST /okr-report/by-planning-period/:planningPeriodId - Get reports by planning period

# ========================================
# MILESTONES APIs
# ========================================

# GET /milestones - Get all milestones
# GET /milestones/:id - Get single milestone

# ========================================
# DASHBOARD APIs
# ========================================

# GET /dashboard/:id - Get dashboard data for user

# ========================================
# PLANS & TASKS APIs
# ========================================

# GET /plan - Get user's plans
# GET /plan/:id - Get single plan
# GET /plan-tasks - Get plan tasks
# GET /plan-tasks/:id - Get single plan task
# GET /weekly-priorities-week - Get weekly priorities
# GET /weekly-priorities-task - Get weekly priority tasks

# ========================================
# COMMENTS APIs
# ========================================

# GET /plan-comments - Get plan comments
# GET /report-comments - Get report comments

# ========================================
# RECOGNITION APIs
# ========================================

# GET /appreciation-log - Get appreciation logs
# GET /reprimand-log - Get reprimand logs
# GET /recognition-type - Get recognition types

# ========================================
# SCORING & AVERAGE APIs
# ========================================

# POST /average-score - Get all users average score
# POST /average-score/user/:userId - Get user's average score
# GET /average-okr-rule - Get average OKR rules

# ========================================
# SUPPORTING APIs
# ========================================

# GET /metric-types - Get metric types
# GET /failure-reason - Get failure reasons
# GET /okr-total-summary - Get OKR total summary
# GET /check-in-rules - Get check-in rules
# GET /health - Health check endpoint

