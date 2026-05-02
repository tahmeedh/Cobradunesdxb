import express from 'express';
import cors from 'cors';
import Stripe from 'stripe';
import { readFileSync } from 'fs';

const app = express();
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

app.use(cors({ origin: '*' }));
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
      success_url: `${origin}/success?session_id={CHECKOUT_SESSION_ID}&pkg=${encodeURIComponent(pkg.name)}`,
      cancel_url: `${origin}/#pricing`,
    });

    res.json({ url: session.url, sessionId: session.id });
  } catch (err) {
    console.error('Stripe error:', err);
    res.status(500).json({ error: err.message });
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
app.listen(PORT, 'localhost', () => {
  console.log(`Buggy Sahara API running on port ${PORT}`);
});
