# Add-Ons TODO List

This document tracks the implementation status and tasks needed to get all add-ons fully operational.

## Overview
The Freelancer platform has 4 add-ons:
- **Stream** - Video streaming and live streaming functionality
- **Commerce** - E-commerce and payment processing
- **LMS** - Learning Management System for courses
- **Social** - Social networking features

---

## 🎥 Stream Add-On

### Status: Partially Implemented
The Stream add-on has the most complete structure with routes, services, schemas, and UI components.

### ✅ Completed
- [x] Directory structure created
- [x] Basic file scaffolding (routes, services, schemas, ui)

### 🔲 TODO
- [ ] **Routes Implementation** (`app/add_ons/stream/routes/`)
  - [ ] Implement `stream.py` - Live streaming endpoints
  - [ ] Implement `video.py` - Video library endpoints
  
- [ ] **Services Implementation** (`app/add_ons/stream/services/`)
  - [ ] Complete `stream_service.py` - Handle live streaming logic
  - [ ] Complete `video_library_service.py` - Video CRUD operations
  
- [ ] **Schemas** (`app/add_ons/stream/schemas/`)
  - [ ] Define `video.py` schemas (VideoCreate, VideoUpdate, VideoResponse)
  
- [ ] **UI Components** (`app/add_ons/stream/ui/`)
  - [ ] Build `components.py` - Video player, stream controls
  - [ ] Build `pages.py` - Stream listing, video library pages
  
- [ ] **Integration**
  - [ ] Mount stream routes in `app/core/app.py`
  - [ ] Add stream dependencies to `dependencies.py`
  - [ ] Configure streaming backend (e.g., AWS MediaLive, Mux, or custom RTMP)
  
- [ ] **Database**
  - [ ] Create migration for stream/video tables
  - [ ] Add Stream and Video models to core models

---

## 💰 Commerce Add-On

### Status: Not Implemented
Empty scaffolding only. Stripe is already in requirements.txt.

### 🔲 TODO
- [ ] **Models & Database**
  - [ ] Expand Product model (inventory, images, categories)
  - [ ] Create Order model
  - [ ] Create Cart model
  - [ ] Create Payment model
  - [ ] Create migration for commerce tables
  
- [ ] **Routes** (`app/add_ons/commerce/routes/`)
  - [ ] Create `products.py` - Product CRUD endpoints
  - [ ] Create `cart.py` - Shopping cart endpoints
  - [ ] Create `checkout.py` - Checkout and payment processing
  - [ ] Create `orders.py` - Order management endpoints
  
- [ ] **Services** (`app/add_ons/commerce/services/`)
  - [ ] Create `product_service.py` - Product management
  - [ ] Create `cart_service.py` - Cart operations
  - [ ] Create `payment_service.py` - Stripe integration
  - [ ] Create `order_service.py` - Order processing
  
- [ ] **Schemas** (`app/add_ons/commerce/schemas/`)
  - [ ] Create product schemas
  - [ ] Create cart schemas
  - [ ] Create order schemas
  - [ ] Create payment schemas
  
- [ ] **UI** (`app/add_ons/commerce/ui/`)
  - [ ] Create product listing pages
  - [ ] Create product detail pages
  - [ ] Create shopping cart UI
  - [ ] Create checkout flow
  - [ ] Create order confirmation pages
  
- [ ] **Integration**
  - [ ] Configure Stripe API keys
  - [ ] Mount commerce routes in `app/core/app.py`
  - [ ] Add commerce dependencies
  - [ ] Implement webhook handlers for Stripe events

---

## 📚 LMS Add-On

### Status: Not Implemented
Empty scaffolding only. Course model exists in core.

### 🔲 TODO
- [ ] **Models & Database**
  - [ ] Expand Course model (instructor, duration, price, etc.)
  - [ ] Create Lesson model
  - [ ] Create Enrollment model
  - [ ] Create Progress model (already referenced in migrations)
  - [ ] Create Quiz/Assessment models
  - [ ] Create Certificate model
  - [ ] Create migration for LMS tables
  
- [ ] **Routes** (`app/add_ons/lms/routes/`)
  - [ ] Create `courses.py` - Course CRUD endpoints
  - [ ] Create `lessons.py` - Lesson management
  - [ ] Create `enrollments.py` - Student enrollment
  - [ ] Create `progress.py` - Track student progress
  - [ ] Create `assessments.py` - Quizzes and tests
  
- [ ] **Services** (`app/add_ons/lms/services/`)
  - [ ] Create `course_service.py` - Course management
  - [ ] Create `enrollment_service.py` - Enrollment logic
  - [ ] Create `progress_service.py` - Progress tracking
  - [ ] Create `assessment_service.py` - Quiz grading
  
- [ ] **Schemas** (`app/add_ons/lms/schemas/`)
  - [ ] Create course schemas
  - [ ] Create lesson schemas
  - [ ] Create enrollment schemas
  - [ ] Create progress schemas
  - [ ] Create assessment schemas
  
- [ ] **UI** (`app/add_ons/lms/ui/`)
  - [ ] Create course catalog page
  - [ ] Create course detail page
  - [ ] Create lesson viewer
  - [ ] Create student dashboard
  - [ ] Create instructor dashboard
  - [ ] Create progress tracking UI
  
- [ ] **Integration**
  - [ ] Mount LMS routes in `app/core/app.py`
  - [ ] Add LMS dependencies
  - [ ] Integrate with media service for course content
  - [ ] Integrate with commerce for course purchases

---

## 👥 Social Add-On

### Status: Not Implemented
Empty scaffolding only. Post model exists in core.

### 🔲 TODO
- [ ] **Models & Database**
  - [ ] Expand Post model (author, timestamps, media)
  - [ ] Create Comment model
  - [ ] Create Like model
  - [ ] Create Follow model
  - [ ] Create Notification model (already referenced in migrations)
  - [ ] Create migration for social tables
  
- [ ] **Routes** (`app/add_ons/social/routes/`)
  - [ ] Create `posts.py` - Post CRUD endpoints
  - [ ] Create `comments.py` - Comment management
  - [ ] Create `likes.py` - Like/unlike endpoints
  - [ ] Create `follows.py` - Follow/unfollow endpoints
  - [ ] Create `feed.py` - Social feed generation
  - [ ] Create `notifications.py` - Notification endpoints
  
- [ ] **Services** (`app/add_ons/social/services/`)
  - [ ] Create `post_service.py` - Post management
  - [ ] Create `comment_service.py` - Comment operations
  - [ ] Create `social_graph_service.py` - Follow relationships
  - [ ] Create `feed_service.py` - Feed algorithm
  - [ ] Create `notification_service.py` - Notification system
  
- [ ] **Schemas** (`app/add_ons/social/schemas/`)
  - [ ] Create post schemas
  - [ ] Create comment schemas
  - [ ] Create follow schemas
  - [ ] Create notification schemas
  
- [ ] **UI** (`app/add_ons/social/ui/`)
  - [ ] Create social feed page
  - [ ] Create post composer
  - [ ] Create post detail page
  - [ ] Create user profile page
  - [ ] Create notifications UI
  - [ ] Create followers/following lists
  
- [ ] **Integration**
  - [ ] Mount social routes in `app/core/app.py`
  - [ ] Add social dependencies
  - [ ] Integrate with media service for post images/videos
  - [ ] Set up real-time notifications (WebSocket/SSE)

---

## 🔧 Cross-Cutting Tasks

### Infrastructure
- [ ] **Database Migrations**
  - [ ] Review existing migrations (0004_add_lms_progress, 0005_add_notifications)
  - [ ] Create comprehensive migrations for all add-on models
  - [ ] Test migration rollback scenarios
  
- [ ] **Dependencies**
  - [ ] Implement proper dependency injection for each add-on
  - [ ] Add any missing packages to `requirements.txt`
  - [ ] Document environment variables needed
  
- [ ] **Configuration**
  - [ ] Create `.env.example` with all required variables
  - [ ] Document third-party service setup (Stripe, streaming provider, etc.)
  - [ ] Add feature flags for enabling/disabling add-ons

### Testing
- [ ] Write unit tests for each service
- [ ] Write integration tests for each add-on
- [ ] Write end-to-end tests for critical flows
- [ ] Add performance tests for high-traffic endpoints

### Documentation
- [ ] Create API documentation for each add-on
- [ ] Write user guides for each feature
- [ ] Document deployment procedures
- [ ] Create architecture diagrams

### Security & Performance
- [ ] Implement rate limiting for all endpoints
- [ ] Add proper authorization checks
- [ ] Optimize database queries
- [ ] Add caching where appropriate
- [ ] Implement CDN for media delivery

---

## Priority Recommendations

### Phase 1: Foundation (Week 1-2)
1. Complete database models and migrations for all add-ons
2. Set up proper dependency injection
3. Create comprehensive `.env.example`

### Phase 2: Core Features (Week 3-4)
1. **Commerce**: Basic product listing and Stripe checkout
2. **LMS**: Course creation and enrollment
3. **Social**: Post creation and feed

### Phase 3: Advanced Features (Week 5-6)
1. **Stream**: Live streaming implementation
2. **Commerce**: Order management and inventory
3. **LMS**: Progress tracking and assessments
4. **Social**: Notifications and real-time features

### Phase 4: Polish (Week 7-8)
1. UI/UX improvements
2. Performance optimization
3. Testing and bug fixes
4. Documentation

---

## Notes
- All add-ons currently have empty `__init__.py` and `dependencies.py` files
- The Stream add-on has the most structure but still needs implementation
- Database models exist for Product, Course, and Post but need expansion
- Stripe is already in requirements.txt for commerce
- MongoDB is set up for dynamic data (chats, events, analytics)
- PostgreSQL is set up for relational data (users, products, courses, etc.)
