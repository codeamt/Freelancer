# Doodle Institute Summer Art Camp - Product Specification

## Project Overview

**Client**: Doodle Institute  
**Project**: Summer Art Camp Landing Page & LMS Integration  
**Budget**: $2,500  
**Timeline**: 4-6 weeks  
**Platform**: Freelancer (FastHTML/FastAPI)

---

## Executive Summary

Build a custom landing page and course management system for Doodle Institute's Summer Art Camp program. The system will handle course registration, payment processing, promotional campaigns, and integrate with Zoom for live instruction delivery.

---

## Business Objectives

### Primary Goals
1. **Increase Enrollment**: Convert 30%+ of landing page visitors to registrations
2. **Streamline Operations**: Automate registration, payment, and course access
3. **Support Promotions**: Enable time-limited offers (e.g., Black Friday 40% off)
4. **Family-Friendly**: Support multi-child registrations with single payment

### Success Metrics
- 100+ student enrollments for Summer 2026
- 90%+ customer satisfaction rating
- 50% reduction in manual administrative work
- $15,000+ in revenue (150 students × $99/week average)

---

## Target Audience

### Primary Users
- **Parents** (Ages 30-50)
  - Looking for summer activities for children
  - Value creativity and skill development
  - Budget-conscious but willing to invest in quality education
  - Tech-comfortable (Zoom users)

### Secondary Users
- **Students** (Ages 6-14)
  - Interested in art and creativity
  - Varying skill levels (beginners welcome)
  - Need engaging, age-appropriate instruction

### Tertiary Users
- **Instructor** (Diane Bleck)
  - Needs simple course management
  - Requires student roster and attendance tracking
  - Wants to focus on teaching, not admin

---

## Feature Requirements

### Phase 1: Landing Page (Week 1-2) ✅ COMPLETE
**Budget Allocation**: $800

#### Core Components
- [x] Hero section with compelling headline
- [x] Promotional banner with countdown timer
- [x] "How It Works" feature grid
- [x] Testimonial carousel (social proof)
- [x] Weekly schedule showcase (6 themed weeks)
- [x] Pricing table (single week vs. multi-week)
- [x] FAQ accordion
- [x] Instructor bio section
- [x] Email capture form
- [x] Final CTA banner

#### Technical Specs
- Fully responsive (mobile-first)
- Fast load times (<2 seconds)
- SEO optimized
- Accessible (WCAG 2.1 AA)

**Status**: ✅ Implemented using core landing page components

---

### Phase 2: Registration & Payment (Week 2-3)
**Budget Allocation**: $700

#### Registration Flow
1. **Week Selection**
   - Display available weeks with capacity
   - Allow multiple week selection
   - Show pricing with multi-week discount
   - Apply promo codes (e.g., "BLACK" for 40% off)

2. **Student Information**
   - Parent/guardian details
   - Student name(s) and age(s)
   - Emergency contact
   - Email for Zoom links

3. **Payment Processing**
   - Stripe integration
   - Support for credit/debit cards
   - Single payment for multiple children
   - Automatic receipt generation

4. **Confirmation**
   - Email confirmation with details
   - Calendar invite (.ics file)
   - Supply list PDF
   - Zoom link (sent 24 hours before start)

#### Database Models Needed
```python
# Registration model
- id
- parent_name
- parent_email
- parent_phone
- students (JSON: [{name, age}])
- selected_weeks (JSON: [week_ids])
- total_amount
- promo_code
- payment_status
- stripe_payment_id
- created_at
```

#### API Endpoints
- `POST /api/register` - Submit registration
- `POST /api/validate-promo` - Validate promo code
- `GET /api/weeks/availability` - Check week capacity
- `POST /api/payment/process` - Process Stripe payment

---

### Phase 3: Course Management (Week 3-4)
**Budget Allocation**: $600

#### Admin Dashboard
- View all registrations by week
- Export student roster (CSV)
- Mark attendance
- Send bulk emails to participants
- Manage week capacity
- Create/edit promo codes

#### Student Portal
- View registered weeks
- Access Zoom links
- Download recordings (post-session)
- View supply lists
- Certificate of completion (after week ends)

#### Zoom Integration
- Generate unique Zoom links per week
- Automatic email reminders (24h, 1h before)
- Record sessions automatically
- Upload recordings to student portal

#### Email Automation
- Welcome email (upon registration)
- Payment confirmation
- Week reminder (1 week before)
- Daily session reminders
- Post-week survey
- Certificate delivery

---

### Phase 4: Promotions & Marketing (Week 4-5)
**Budget Allocation**: $400

#### Promo Code System
```python
# PromoCode model
- code (e.g., "BLACK")
- discount_type (percentage/fixed)
- discount_value (40 for 40%)
- valid_from
- valid_until
- max_uses
- current_uses
- applicable_weeks (all or specific)
```

#### Features
- Create time-limited promotions
- Countdown timer on landing page
- Automatic code validation
- Usage tracking and analytics
- Early bird pricing support

#### Marketing Tools
- Email capture integration (Mailchimp/SendGrid)
- Referral tracking (UTM parameters)
- Social sharing buttons
- Testimonial collection form

---

## Technical Architecture

### Frontend
- **Framework**: FastHTML (existing)
- **Components**: Phase 1 landing page components (implemented)
- **Styling**: Inline styles + theme system
- **Forms**: Native HTML forms with validation

### Backend
- **Framework**: FastAPI (existing)
- **Database**: PostgreSQL (existing)
- **ORM**: SQLAlchemy async (existing)
- **Migrations**: Alembic (existing)

### Third-Party Services
- **Payments**: Stripe ($0 setup, 2.9% + $0.30 per transaction)
- **Email**: SendGrid (Free tier: 100 emails/day)
- **Video**: Zoom (Client's existing account)
- **Hosting**: Client's existing infrastructure

### Security
- HTTPS only
- PCI compliance (via Stripe)
- GDPR-compliant data handling
- Secure session management
- Input validation and sanitization

---

## User Flows

### Registration Flow
```
1. Land on homepage
2. View promotional offer + countdown
3. Scroll through features & testimonials
4. Review weekly themes
5. Click "Register Now" CTA
6. Select week(s)
7. Enter student/parent info
8. Apply promo code (optional)
9. Review order summary
10. Enter payment details (Stripe)
11. Receive confirmation email
12. Access student portal
```

### Student Experience Flow
```
1. Receive welcome email
2. Get week reminder (7 days before)
3. Receive Zoom link (24 hours before)
4. Get daily reminders (1 hour before)
5. Join Zoom session
6. Access recording (after session)
7. Complete week
8. Receive certificate
9. Get survey request
```

### Admin Flow
```
1. Log into admin dashboard
2. View registrations by week
3. Export student roster
4. Send bulk emails
5. Mark attendance
6. Upload recordings
7. Generate certificates
8. View revenue reports
```

---

## Design Specifications

### Brand Colors (Doodle Institute)
```css
Primary: #FF6B6B (Playful Red)
Secondary: #4ECDC4 (Teal)
Accent: #FFE66D (Yellow)
Text: #2D3748 (Dark Gray)
Background: #F7FAFC (Light Gray)
```

### Typography
- **Headings**: System font stack (bold, 700-800 weight)
- **Body**: System font stack (regular, 400 weight)
- **Size Scale**: 1rem base, 1.2 ratio

### Visual Style
- Playful and colorful
- Rounded corners (12px border-radius)
- Soft shadows
- Emoji icons for features
- High contrast for readability
- Mobile-first responsive design

---

## Content Requirements

### Copy Needed from Client
- [ ] Instructor bio (150-200 words)
- [ ] Instructor photo (high-res)
- [ ] 3-5 parent testimonials
- [ ] Detailed weekly theme descriptions
- [ ] Supply list
- [ ] Refund policy details
- [ ] Terms and conditions
- [ ] Privacy policy

### Media Assets
- [ ] Hero background image/video (optional)
- [ ] Sample student artwork photos
- [ ] Instructor headshot
- [ ] Logo (SVG preferred)

---

## Budget Breakdown

| Phase | Deliverable | Hours | Rate | Cost |
|-------|-------------|-------|------|------|
| **Phase 1** | Landing Page Components | 10 | $80/hr | $800 |
| **Phase 2** | Registration & Payment | 9 | $80/hr | $720 |
| **Phase 3** | Course Management | 7 | $80/hr | $560 |
| **Phase 4** | Promotions & Marketing | 5 | $80/hr | $400 |
| **Testing** | QA & Bug Fixes | 2 | $80/hr | $160 |
| **Total** | | **33 hrs** | | **$2,640** |

**Adjusted to Budget**: $2,500 (includes small discount for package deal)

### What's Included
✅ Custom landing page (Phase 1 - COMPLETE)  
✅ Registration system with Stripe  
✅ Admin dashboard  
✅ Student portal  
✅ Email automation  
✅ Promo code system  
✅ Zoom integration  
✅ 30 days post-launch support  

### What's NOT Included
❌ Custom Zoom account setup (client provides)  
❌ Content writing (client provides copy)  
❌ Professional photography  
❌ Ongoing hosting/maintenance  
❌ Marketing campaigns  
❌ Custom mobile app  

---

## Timeline

### Week 1-2: Foundation ✅
- [x] Landing page components
- [x] Example page implementation
- [x] Route setup
- [ ] Client content collection

### Week 3: Registration System
- [ ] Database models
- [ ] Registration form
- [ ] Stripe integration
- [ ] Email confirmations

### Week 4: Course Management
- [ ] Admin dashboard
- [ ] Student portal
- [ ] Zoom integration
- [ ] Recording management

### Week 5: Promotions & Polish
- [ ] Promo code system
- [ ] Email automation
- [ ] Analytics tracking
- [ ] Final testing

### Week 6: Launch & Support
- [ ] Production deployment
- [ ] Client training
- [ ] Documentation
- [ ] Bug fixes

---

## Risk Assessment

### Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Stripe integration issues | Low | High | Use Stripe's official SDK, test thoroughly |
| Zoom API limitations | Medium | Medium | Use webhooks, implement fallbacks |
| Email deliverability | Medium | High | Use SendGrid, implement SPF/DKIM |
| Database performance | Low | Medium | Optimize queries, add indexes |

### Business Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Low enrollment | Medium | High | Strong marketing, early bird pricing |
| Payment disputes | Low | Medium | Clear refund policy, good support |
| Technical support load | Medium | Medium | Comprehensive documentation, FAQs |
| Zoom capacity issues | Low | High | Monitor attendance, set capacity limits |

---

## Success Criteria

### Launch Criteria (Must Have)
- [ ] Landing page live and responsive
- [ ] Registration flow working end-to-end
- [ ] Stripe payments processing successfully
- [ ] Email confirmations sending
- [ ] Admin dashboard accessible
- [ ] Student portal functional
- [ ] All links and CTAs working
- [ ] Mobile responsive
- [ ] Load time <2 seconds
- [ ] Zero critical bugs

### Post-Launch Metrics (90 Days)
- 100+ registrations
- 30%+ conversion rate (visitors to registrations)
- <1% payment failure rate
- 4.5+ star average rating
- <5% refund rate
- 95%+ email delivery rate

---

## Maintenance & Support

### Included (30 Days Post-Launch)
- Bug fixes
- Minor content updates
- Email template adjustments
- Performance optimization
- Client training sessions (2 hours)

### Ongoing Support (Optional)
- **Monthly Retainer**: $200/month
  - Up to 2 hours of updates/changes
  - Priority support
  - Performance monitoring
  - Security updates

---

## Deliverables

### Code & Documentation
- [ ] Source code (GitHub repository)
- [ ] Database schema documentation
- [ ] API documentation
- [ ] Admin user guide
- [ ] Deployment guide
- [ ] Environment setup guide

### Access & Credentials
- [ ] Admin dashboard login
- [ ] Database access
- [ ] Stripe dashboard access
- [ ] SendGrid account access
- [ ] GitHub repository access

---

## Assumptions

1. Client provides Zoom account and manages sessions
2. Client provides all content (copy, images, testimonials)
3. Client has existing hosting infrastructure
4. Client handles customer support inquiries
5. Client manages refunds through Stripe dashboard
6. Payment processing fees paid by client (2.9% + $0.30)
7. Email sending limits within SendGrid free tier
8. Maximum 30 students per week (capacity limit)

---

## Next Steps

### Immediate Actions
1. ✅ Phase 1 landing page components (COMPLETE)
2. ⏳ Client review and content gathering
3. ⏳ Finalize design mockups
4. ⏳ Set up Stripe test account
5. ⏳ Configure SendGrid account

### Client Responsibilities
- [ ] Provide content (copy, images, testimonials)
- [ ] Review and approve design
- [ ] Set up Stripe account
- [ ] Provide Zoom account details
- [ ] Review and test registration flow
- [ ] Approve final product before launch

### Developer Responsibilities
- [x] Build landing page components
- [ ] Implement registration system
- [ ] Integrate payment processing
- [ ] Build admin dashboard
- [ ] Set up email automation
- [ ] Deploy to production
- [ ] Provide training and documentation

---

## Approval

**Client Signature**: ________________________  
**Date**: ________________________

**Developer Signature**: ________________________  
**Date**: ________________________

---

## Appendix

### A. Technology Stack Details
- **Python**: 3.11+
- **FastAPI**: Latest stable
- **FastHTML**: Latest stable
- **PostgreSQL**: 14+
- **Stripe API**: v2023-10-16
- **SendGrid API**: v3
- **Zoom API**: v2

### B. Compliance Requirements
- PCI DSS Level 1 (via Stripe)
- GDPR compliant data handling
- COPPA compliant (children's data)
- CAN-SPAM Act compliant (emails)

### C. Browser Support
- Chrome/Edge (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)
- Mobile Safari (iOS 14+)
- Chrome Mobile (Android 10+)

### D. Performance Targets
- First Contentful Paint: <1.5s
- Time to Interactive: <3.0s
- Lighthouse Score: 90+
- Mobile Speed: 85+

---

**Document Version**: 1.0  
**Last Updated**: November 29, 2025  
**Status**: Draft - Awaiting Client Approval
