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

const PACKAGES = {
  explorer: {
    name: 'Explorer Package',
    description: '30 Minutes · 2-Seater Buggy · Safety Gear Included',
    amount: 39900,
    currency: 'aed',
  },
  adventurer: {
    name: 'Adventurer Package',
    description: '2 Hours · Choice of 2-Seater · Refreshments Included',
    amount: 69900,
    currency: 'aed',
  },
  dune_master: {
    name: 'Dune Master Package',
    description: '4 Hours · Any Buggy Incl 4-Seater · Snacks & Beverages',
    amount: 129900,
    currency: 'aed',
  },
  vip: {
    name: 'VIP Full Day Adventure',
    description: '8 Hours · Private Guide · Hotel Transfer · Gourmet Lunch',
    amount: 199900,
    currency: 'aed',
  },
};

app.post('/api/create-checkout-session', async (req, res) => {
  try {
    const { packageId, customerName, customerEmail, date, groupSize, notes } = req.body;

    const pkg = PACKAGES[packageId];
    if (!pkg) {
      return res.status(400).json({ error: 'Invalid package' });
    }

    const origin = req.headers.origin || `https://${process.env.REPLIT_DEV_DOMAIN}`;

    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: [
        {
          price_data: {
            currency: pkg.currency,
            product_data: {
              name: pkg.name,
              description: pkg.description,
              images: ['https://cobradunesdxb.com/wp-content/uploads/2025/11/CAN-AM-MAVERICK-R-X-RS-2025-1-1024x960.webp'],
            },
            unit_amount: pkg.amount,
          },
          quantity: 1,
        },
      ],
      mode: 'payment',
      customer_email: customerEmail || undefined,
      metadata: {
        customerName: customerName || '',
        date: date || '',
        groupSize: groupSize || '',
        notes: notes || '',
        packageId,
      },
      success_url: `${origin}/booking/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${origin}/booking`,
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
