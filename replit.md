# Buggy Sahara DXB — Project Overview

## What This Is
Dubai's premier dune buggy rental and desert adventure website. Built with Astro + Tailwind + React. Features lead generation funnels, Stripe payment processing, and a full SEO strategy targeting Dubai/UAE desert rental keywords.

## Architecture
- **Frontend**: Astro (static) served on port 5000
- **Backend API**: Express.js on port 3001 (Stripe checkout, lead capture)
- **Start command**: `bash start.sh` — starts both API and Astro dev server
- **Workflow**: "Start application" → `bash start.sh`

## Key Features
1. **Lead Generation Funnel** (`src/components/LeadFunnel.astro`)
   - Urgency top bar with countdown timer + slot scarcity
   - Exit-intent popup with AED 100 discount lead magnet (code: DUNE100)
   - Social proof toast notifications (fake booking activity)
   - Sticky mobile CTA bar
   - Lead capture to `/api/lead-capture`

2. **Stripe Payment** (`src/components/StripePayment.astro`, `server.js`)
   - Modal checkout flow on all pricing cards
   - Packages: Explorer (AED 399), Adventurer (AED 699), Dune Master (AED 1,299), VIP (AED 1,999)
   - Discount codes: DUNE100 (−100), SAHARA50 (−50), VIP200 (−200)
   - Success page: `/success`
   - API endpoint: `POST /api/create-checkout-session`

3. **SEO Landing Pages** (Astro static pages)
   - `/dune-buggy-dubai` — targets "dune buggy Dubai" keywords
   - `/buggy-rental-dubai` — targets "buggy rental Dubai" keywords
   - `/safari-rental-dubai` — targets "safari rental Dubai / desert safari" keywords
   - `/4x4-rental-uae` — targets "4x4 rental UAE / off-road" keywords
   - All pages have Schema.org structured data

4. **SEO Strategy**
   - Enhanced sitemap at `/sitemap.xml` with all pages
   - Schema.org LocalBusiness JSON-LD on homepage
   - Individual page Schema (TouristAttraction, TouristTrip, Vehicle)
   - Geo meta tags for Dubai
   - robots.txt blocks `/api/` from indexing

## Secrets Required
- `STRIPE_SECRET_KEY` — Stripe secret (sk_live_... or sk_test_...)
- `STRIPE_PUBLISHABLE_KEY` — Stripe publishable (pk_live_... or pk_test_...)

## Ports
- 5000 — Astro frontend (webview)
- 3001 — Express API backend

## Key Files
- `server.js` — Express API with Stripe + lead capture
- `start.sh` — Starts API + Astro together
- `src/components/LeadFunnel.astro` — Exit-intent popup, urgency bar, social proof
- `src/components/StripePayment.astro` — Payment modal
- `src/components/Pricing.astro` — Updated pricing with Stripe + WhatsApp CTAs
- `src/pages/success.astro` — Post-payment confirmation page
- `src/pages/dune-buggy-dubai.astro` — SEO page
- `src/pages/buggy-rental-dubai.astro` — SEO page
- `src/pages/safari-rental-dubai.astro` — SEO page
- `src/pages/4x4-rental-uae.astro` — SEO page

## Contact/Business Info
- Phone/WhatsApp: +971 50 537 1693
- Email: info@buggysaharadxb.com
- Location: Al Lahbab (Big Red), Dubai, UAE
- Hours: Daily 6:00 AM – 10:00 PM
