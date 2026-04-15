/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        gold: {
          50:  '#FFFDF0',
          100: '#FFF9CC',
          200: '#FFF099',
          300: '#FFE566',
          400: '#FFD700',
          500: '#D4AF37',
          600: '#B8960C',
          700: '#8B6914',
          800: '#5C4309',
          900: '#2E2104',
        },
        dark: {
          50:  '#F5F5F5',
          100: '#E0E0E0',
          200: '#BDBDBD',
          300: '#9E9E9E',
          400: '#757575',
          500: '#616161',
          600: '#424242',
          700: '#2D2D2D',
          800: '#1A1A1A',
          900: '#0D0D0D',
          950: '#080808',
        },
        sand: {
          100: '#FFF8E7',
          200: '#F5DEB3',
          300: '#E8C870',
          400: '#D4A94A',
          500: '#C2912A',
        },
        buggy: {
          red:    '#C41E3A',
          orange: '#FF6B35',
          gold:   '#D4AF37',
          dark:   '#0D0D0D',
        },
      },
      fontFamily: {
        sans:    ['Inter', 'system-ui', 'sans-serif'],
        display: ['Rajdhani', 'Oswald', 'Impact', 'sans-serif'],
        racing:  ['Bebas Neue', 'Impact', 'sans-serif'],
      },
      backgroundImage: {
        'gradient-radial':  'radial-gradient(var(--tw-gradient-stops))',
        'gradient-cobra':   'linear-gradient(135deg, #0D0D0D 0%, #1A1A1A 50%, #0D0D0D 100%)',
        'gradient-gold':    'linear-gradient(135deg, #D4AF37 0%, #FFD700 50%, #B8960C 100%)',
        'gradient-desert':  'linear-gradient(180deg, #D4A94A 0%, #C2912A 100%)',
        'gradient-hero':    'linear-gradient(to bottom, rgba(13,13,13,0.3) 0%, rgba(13,13,13,0.6) 50%, rgba(13,13,13,0.95) 100%)',
      },
      animation: {
        'float':       'float 6s ease-in-out infinite',
        'pulse-gold':  'pulse-gold 2s ease-in-out infinite',
        'slide-up':    'slideUp 0.8s ease forwards',
        'fade-in':     'fadeIn 1s ease forwards',
        'spin-slow':   'spin 8s linear infinite',
        'shimmer':     'shimmer 2.5s linear infinite',
        'bounce-slow': 'bounce 3s infinite',
        'glow':        'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%':      { transform: 'translateY(-20px)' },
        },
        'pulse-gold': {
          '0%, 100%': { boxShadow: '0 0 20px rgba(212,175,55,0.4)' },
          '50%':      { boxShadow: '0 0 40px rgba(212,175,55,0.8)' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(60px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          from: { opacity: '0' },
          to:   { opacity: '1' },
        },
        shimmer: {
          '0%':   { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
        glow: {
          from: { textShadow: '0 0 10px rgba(212,175,55,0.5)' },
          to:   { textShadow: '0 0 30px rgba(212,175,55,1), 0 0 60px rgba(212,175,55,0.5)' },
        },
      },
      boxShadow: {
        'gold':       '0 0 30px rgba(212,175,55,0.4)',
        'gold-lg':    '0 0 60px rgba(212,175,55,0.6)',
        'gold-inner': 'inset 0 0 30px rgba(212,175,55,0.2)',
        'card':       '0 25px 50px -12px rgba(0,0,0,0.8)',
        'card-hover': '0 35px 60px -15px rgba(0,0,0,0.9), 0 0 30px rgba(212,175,55,0.3)',
      },
      backdropBlur: {
        xs: '2px',
      },
      transitionDuration: {
        '400': '400ms',
      },
    },
  },
  plugins: [],
};
