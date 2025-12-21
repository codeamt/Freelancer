# Development TODOs - Prioritized

This document tracks development tasks for completing the FastApp platform with admin fixes, core features, and optional add-ons. Tasks are ordered by priority.

## Core Platform vs Add-Ons

**Core Platform (Essential - Complete without add-ons):**
- User authentication and role management
- Admin panel with dashboard
- Content management system (pages, components)
- Settings management (site, theme, email, security)
- Payment processing (Stripe)
- Email marketing (Mailchimp)
- Discount codes
- Theme customization
- Security features

**Optional Add-Ons (Enhancement modules):**
- Social features (posts, profiles, timelines)
- Streaming features (WebRTC, broadcasting)
- Other domain-specific modules

---

## Phase 1: Critical - Admin Module Fixes & Enhancements

### 1.1 Platform Admin Registration
- [ ] **Fix Platform Admin Authentication**: Determine registration approach
  - [ ] Decide if platform admins should register normally or use special route
  - [ ] Create hidden admin registration endpoint if needed
  - [ ] Add proper role assignment for platform admins (super_admin)
  - [ ] Test admin registration and role assignment

### 1.2 Admin UI Styling
- [ ] **Replace Bootstrap with MonsterUI**: Complete admin UI overhaul
  - [ ] Update admin pages to use MonsterUI components
  - [ ] Ensure consistent design with main site
  - [ ] Add responsive design for admin panels
  - [ ] Improve navigation and layout
  - [ ] Test admin UI across different screen sizes

### 1.3 Admin Dashboard
- [ ] **Complete Dashboard Functionality**: Build working admin dashboard
  - [ ] Add system overview widgets (server status, active users, etc.)
  - [ ] Include user statistics (registration, activity, roles)
  - [ ] Add system health monitoring (database, services, integrations)
  - [ ] Implement quick actions panel (common admin tasks)
  - [ ] Add real-time updates for dashboard metrics

### 1.4 Comprehensive Settings Management
- [ ] **Site Configuration Settings**: Basic site management
  - [ ] Basic site info (name, description, logo, favicon)
  - [ ] URL structure and domain settings
  - [ ] Timezone and locale configuration
  - [ ] SEO settings (meta tags, sitemap, robots.txt)
  - [ ] Maintenance mode and downtime messages

- [ ] **Theme Customization Options**: Visual customization
  - [ ] Color scheme and branding customization
  - [ ] Typography settings (fonts, sizes, weights)
  - [ ] Layout options (sidebar, header, footer configurations)
  - [ ] Custom CSS injection for advanced styling
  - [ ] Component library overrides and custom components
  - [ ] Mobile responsiveness settings

- [ ] **Email Configuration**: Email system setup
  - [ ] SMTP server settings (host, port, credentials)
  - [ ] Email template management and customization
  - [ ] Transactional email configuration (welcome, password reset, etc.)
  - [ ] Email delivery testing and verification
  - [ ] Bounce handling and email analytics
  - [ ] Email queue management and throttling

- [ ] **Security Settings**: Security configuration
  - [ ] Password policy configuration (length, complexity, expiration)
  - [ ] Two-factor authentication settings
  - [ ] Session management (timeout, concurrent sessions)
  - [ ] Rate limiting configuration per endpoint
  - [ ] IP whitelist/blacklist management
  - [ ] Security headers and CSP policies
  - [ ] Audit logging and security event monitoring

### 1.5 Non-Demo Mode Integrations
- [ ] **Enable Integrations**: Activate third-party services
  - [ ] Mailchimp integration configuration
  - [ ] Stripe payment settings
  - [ ] Analytics integration setup
  - [ ] Third-party service connections
  - [ ] Integration status monitoring
  - [ ] Integration health checks and error handling

---

## Phase 2: High - Core Features Restoration

### 2.1 Mailchimp Integration Restoration
- [ ] **Restore Mailchimp Service**: Re-implement deleted functionality
  - [ ] **Mailchimp API Client**: Restore `core/integrations/mailchimp/client.py`
    - [ ] Implement Mailchimp API wrapper with API key authentication
    - [ ] Add server prefix configuration (`MAILCHIMP_SERVER_PREFIX`)
    - [ ] Include audience ID configuration (`MAILCHIMP_AUDIENCE_ID`)
    - [ ] Add error handling for API failures and timeouts
  - [ ] **Newsletter Subscription Management**: 
    - [ ] Restore subscription form handling
    - [ ] Implement double opt-in process
    - [ ] Add unsubscribe functionality
    - [ ] Create subscription status tracking
  - [ ] **Campaign Integration**:
    - [ ] Add campaign creation and management
    - [ ] Implement email template handling
    - [ ] Add campaign scheduling and sending
  - [ ] **Audience Management**:
    - [ ] Restore audience list management
    - [ ] Add member data synchronization
    - [ ] Implement audience segmentation
    - [ ] Add member merge field handling
  - [ ] **Email Template System**:
    - [ ] Restore template management
    - [ ] Add custom template creation
    - [ ] Implement template preview functionality
  - [ ] **Configuration & Settings**:
    - [ ] Add Mailchimp settings to admin panel
    - [ ] Implement API key validation
    - [ ] Add webhook configuration for real-time sync
    - [ ] Create integration status monitoring

### 2.2 Discount Code System Restoration
- [ ] **Restore Discount Codes**: Re-implement discount functionality
  - [ ] Discount code model and validation
  - [ ] Code generation and management
  - [ ] Application logic for orders
  - [ ] Usage tracking and limits
  - [ ] Expiration and validation rules
  - [ ] Discount code analytics and reporting

### 2.3 Payment Processing & JWT Auth
- [ ] **Stripe Integration Restoration**: Re-implement payment system
  - [ ] Restore Stripe API client and configuration
  - [ ] Add payment intent creation and management
  - [ ] Implement webhook handling for payment events
  - [ ] Add subscription management (create, cancel, update)
  - [ ] Implement refund processing
  - [ ] Add payment method storage and management
  - [ ] Create payment history tracking
  - [ ] Add error handling for Stripe API failures

- [ ] **JWT Auth Role Sync**: Ensure JWT tokens sync with role system
  - [ ] Update JWT token generation to include current roles array
  - [ ] Add role_version field to JWT payload for revocation support
  - [ ] Implement role version bumping on role changes
  - [ ] Add JWT validation for stale role versions
  - [ ] Create role change detection and token invalidation
  - [ ] Add session management integration with role updates
  - [ ] Implement role-based JWT audience/issuer claims
  - [ ] Add logout functionality with role version reset

---

## Phase 3: Optional - Add-Ons Module Completion

### 3.1 Streaming Add-On (Optional Enhancement)
- [ ] **Complete Streaming Domain**: Finish streaming functionality
  - [ ] WebRTC implementation completion
  - [ ] Stream management interface
  - [ ] Broadcasting features
  - [ ] Viewer authentication
  - [ ] Stream recording/archiving
  - [ ] Chat and interaction features
  - [ ] Stream analytics and metrics

### 3.2 Social Add-On (Optional Enhancement)
- [ ] **Adapt Social Domain**: Convert legacy FastAPI to FastHTML
  - [ ] Review `add_ons/domain/SOCIAL_ADDON.md` for requirements
  - [ ] Convert existing FastAPI routes to FastHTML
  - [ ] Update models for new auth system
  - [ ] Implement social features (posts, comments, likes)
  - [ ] User profiles and timelines
  - [ ] Social authentication integration
  - [ ] Privacy settings and permissions
  - [ ] Social media sharing features

### 3.3 Add-On Infrastructure (Optional Enhancement)
- [ ] **Add-On Management**: Complete add-on system
  - [ ] Dynamic add-on loading
  - [ ] Add-on configuration management
  - [ ] Add-on permissions integration
  - [ ] Add-on health monitoring
  - [ ] Add-on update mechanism
  - [ ] Add-on marketplace integration

---

## Phase 4: Testing & Quality Assurance

### 4.1 Role System Testing
- [ ] **Authentication Testing**: Test new role hierarchy
  - [ ] Verify role assignment works correctly (super_admin, admin, instructor, editor, student, user, guest)
  - [ ] Test permission enforcement for each role level
  - [ ] Validate backward compatibility with legacy roles (member, site_owner, site_admin, support_staff)
  - [ ] Test role versioning and revocation
  - [ ] Multi-role scenarios testing
  - [ ] Domain-specific role testing (blog_admin, blog_author, lms_admin)

### 4.2 Integration Testing
- [ ] **Service Integration Testing**: Test all integrations
  - [ ] Mailchimp API connectivity and functionality
  - [ ] Stripe payment processing and webhooks
  - [ ] Database connections (PostgreSQL, MongoDB, Redis)
  - [ ] Email delivery testing and template rendering
  - [ ] File upload/storage testing
  - [ ] Third-party service authentication

### 4.3 Add-On Testing
- [ ] **Add-On Functionality**: Test completed add-ons
  - [ ] Streaming add-on end-to-end testing
  - [ ] Social add-on feature testing
  - [ ] Cross-add-on interaction testing
  - [ ] Add-on enable/disable testing
  - [ ] Add-on performance testing

### 4.4 Performance & Security
- [ ] **Performance Testing**: Ensure system performance
  - [ ] Load testing for concurrent users
  - [ ] Database query optimization
  - [ ] Memory usage monitoring
  - [ ] Response time benchmarks
  - [ ] Scalability testing

- [ ] **Security Testing**: Verify security measures
  - [ ] Authentication flow testing
  - [ ] Authorization bypass testing
  - [ ] Input validation testing
  - [ ] XSS and CSRF protection testing
  - [ ] Rate limiting verification
  - [ ] Penetration testing

### 4.5 Documentation & Deployment
- [ ] **Documentation Updates**: Complete project documentation
  - [ ] API documentation for all endpoints
  - [ ] Admin panel user guide
  - [ ] Integration setup guides
  - [ ] Deployment documentation

- [ ] **Deployment Preparation**: Prepare for production
  - [ ] Environment configuration
  - [ ] Database migration scripts
  - [ ] Docker container optimization
  - [ ] Monitoring and logging setup
  - [ ] Backup and recovery procedures

---

## Success Criteria

### Core Platform (Essential - Complete without add-ons)
- [ ] Platform admins can register and access admin panel (super_admin role)
- [ ] Admin UI is properly styled with MonsterUI and responsive
- [ ] Admin dashboard provides comprehensive system overview
- [ ] All settings management features are functional (site, theme, email, security)
- [ ] All integrations work in non-demo mode (Mailchimp, Stripe, analytics)
- [ ] Mailchimp integration is fully restored with all features
- [ ] Stripe integration is restored with payment processing
- [ ] JWT auth properly syncs with role system and supports revocation
- [ ] Discount codes are fully functional
- [ ] All tests pass with >90% coverage including role hierarchy testing
- [ ] System is production-ready and performant
- [ ] Documentation is complete and up-to-date

### Optional Add-Ons (Enhancement modules)
- [ ] Streaming add-on is complete and tested (optional)
- [ ] Social add-on is complete and tested (optional)

