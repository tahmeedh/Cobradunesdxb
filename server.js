import express from 'express';
import cors from 'cors';
import Stripe from 'stripe';
import { readFileSync } from 'fs';

const app = express();
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

app.use(cors({ origin: '*' }));

// Raw body needed for Stripe webhook signature verification
app.use('/api/webhook', express.raw({ type: 'application/json' }));
app.use(express.json());

// Buggy base prices (AED per 30 min)
const BUGGY_PRICES = {
  'kymco-mxu-250':                        150,
  'can-am-maverick-r-x-rs-2025':          800,
  'can-am-maverick-3x-turbo-rr-2-seater': 550,
  'can-am-maverick-3x-turbo-rr-4-seater': 600,
  'polaris-rzr-2-seater-1000xp':           400,
  'polaris-rzr-4-seater-1000xp':           450,
  'cf-moto-1000cc-4x4':                    249,
  'can-am-maverick-r-x-rs-2024':           700,
};

// Duration multipliers (applied to 30-min base price)
const DURATION_MULT = { 30: 1.0, 60: 1.7, 90: 2.3, 120: 3.0, 180: 4.0, 240: 5.0 };

// Add-on prices (AED)
const ADDON_PRICES = {
  drone:   350,
  photo:   250,
  sunset:  200,
  bedouin: 180,
  film:    500,
  gear:    120,
};

const ADDON_NAMES = {
  drone:   'Drone Aerial Package',
  photo:   'Desert Photo Session',
  sunset:  'Sunset VIP Experience',
  bedouin: 'Bedouin Camp After-Ride',
  film:    'Full Adventure Film',
  gear:    'Safari Head Gear Set',
};

const DISCOUNT_CODES = { DUNE100: 100, SAHARA50: 50, VIP200: 200 };

app.post('/api/create-checkout-session', async (req, res) => {
  try {
    const {
      buggyId, buggyName, durationMins, addOnIds = [], discountCode,
      rideDescription, customerName, customerEmail,
      date, startTime, duration, groupSize, notes,
    } = req.body;

    // Validate buggy
    const basePrice = BUGGY_PRICES[buggyId];
    if (!basePrice) return res.status(400).json({ error: 'Invalid buggy selected' });

    // Compute prices server-side
    const mult        = DURATION_MULT[parseInt(durationMins)] || 1.0;
    const buggyAED    = Math.round(basePrice * mult);
    const addOnsAED   = addOnIds.reduce((s, id) => s + (ADDON_PRICES[id] || 0), 0);
    const discountAED = DISCOUNT_CODES[discountCode] || 0;
    const totalAED    = Math.max(50, buggyAED + addOnsAED - discountAED);

    const origin = req.headers.origin || `https://${process.env.REPLIT_DEV_DOMAIN}`;

    // Build line items — buggy ride first
    const lineItems = [
      {
        price_data: {
          currency: 'aed',
          product_data: {
            name: buggyName || 'Dune Buggy Ride',
            description: rideDescription || `${duration || durationMins + ' min'} · ${date || ''}`,
            images: ['https://cobradunesdxb.com/wp-content/uploads/2025/11/CAN-AM-MAVERICK-R-X-RS-2025-1-1024x960.webp'],
          },
          unit_amount: buggyAED * 100,
        },
        quantity: 1,
      },
    ];

    // Add each add-on as a separate line item for transparency
    for (const id of addOnIds) {
      if (ADDON_PRICES[id]) {
        lineItems.push({
          price_data: {
            currency: 'aed',
            product_data: { name: ADDON_NAMES[id] || id },
            unit_amount: ADDON_PRICES[id] * 100,
          },
          quantity: 1,
        });
      }
    }

    const addOnsSummary = addOnIds.map(id => ADDON_NAMES[id]).filter(Boolean).join(', ');

    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: lineItems,
      mode: 'payment',
      customer_email: customerEmail || undefined,
      discounts: discountAED > 0 ? [] : [],  // Stripe coupon could be added here
      metadata: {
        customerName:  customerName  || '',
        buggyId:       buggyId       || '',
        buggyName:     buggyName     || '',
        date:          date          || '',
        startTime:     startTime     || '',
        duration:      duration      || '',
        groupSize:     groupSize     || '',
        notes:         notes         || '',
        addOns:        addOnsSummary || '',
        discountCode:  discountCode  || '',
        discountAED:   String(discountAED),
      },
      success_url: `${origin}/booking/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url:  `${origin}/booking`,
    });

    res.json({ url: session.url, sessionId: session.id });
  } catch (err) {
    console.error('Stripe error:', err);
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/webhook', (req, res) => {
  const sig = req.headers['stripe-signature'];
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;

  let event;
  try {
    event = stripe.webhooks.constructEvent(req.body, sig, webhookSecret);
  } catch (err) {
    console.error('Webhook signature verification failed:', err.message);
    return res.status(400).send(`Webhook Error: ${err.message}`);
  }

  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object;
      const meta = session.metadata || {};
      const amountAED = session.amount_total ? (session.amount_total / 100).toFixed(0) : '?';
      console.log('✅ Payment completed:', {
        sessionId: session.id,
        customerEmail: session.customer_email,
        amount: `AED ${amountAED}`,
        customerName: meta.customerName,
        date: meta.date,
        groupSize: meta.groupSize,
        packageId: meta.packageId,
      });

      // WhatsApp notification via CallMeBot (free service)
      const apiKey = process.env.CALLMEBOT_API_KEY;
      const phone  = process.env.OWNER_WHATSAPP || '971505371693';
      if (apiKey) {
        const msg = encodeURIComponent(
          `🏜️ NEW BOOKING - Buggy Sahara DXB\n` +
          `👤 ${meta.customerName || 'Guest'}\n` +
          `📧 ${session.customer_email || '—'}\n` +
          `🏎️ ${meta.packageId || '—'}\n` +
          `📅 ${meta.date || '—'}\n` +
          `👥 Group: ${meta.groupSize || '—'}\n` +
          `💰 AED ${amountAED}\n` +
          `🔑 Ref: ${session.id.slice(0, 20)}`
        );
        fetch(`https://api.callmebot.com/whatsapp.php?phone=${phone}&text=${msg}&apikey=${apiKey}`)
          .then(() => console.log('📱 WhatsApp notification sent'))
          .catch(e => console.error('WhatsApp notify failed:', e.message));
      } else {
        console.log('ℹ️  CALLMEBOT_API_KEY not set — WhatsApp notification skipped');
        console.log(`📋 Booking summary: ${meta.customerName} | ${meta.packageId} | ${meta.date} | AED ${amountAED}`);
      }
      break;
    }
    case 'payment_intent.payment_failed': {
      const intent = event.data.object;
      console.log('❌ Payment failed:', intent.id, intent.last_payment_error?.message);
      break;
    }
    default:
      console.log(`Unhandled webhook event: ${event.type}`);
  }

  res.json({ received: true });
});

app.get('/api/session', async (req, res) => {
  const { id } = req.query;
  if (!id) return res.status(400).json({ error: 'session id required' });
  try {
    const session = await stripe.checkout.sessions.retrieve(id);
    const meta = session.metadata || {};
    res.json({
      customerName: meta.customerName || '',
      packageName:  meta.packageId    || '',
      date:         meta.date         || '',
      groupSize:    meta.groupSize    || '',
      notes:        meta.notes        || '',
      amountTotal:  session.amount_total,
      currency:     session.currency,
      email:        session.customer_email || '',
      status:       session.payment_status,
    });
  } catch (err) {
    console.error('Session fetch error:', err.message);
    res.status(500).json({ error: 'Could not retrieve session' });
  }
});

app.get('/api/lead-magnet', (req, res) => {
  res.json({ success: true, message: 'Lead captured' });
});

app.post('/api/lead-capture', async (req, res) => {
  const { name, email, phone, interest } = req.body;
  console.log('Lead captured:', { name, email, phone, interest, timestamp: new Date().toISOString() });
  res.json({ success: true });
});

const PORT = process.env.API_PORT || 3001;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Buggy Sahara API running on port ${PORT}`);
});
