# MealMap

A food bank distribution management system that displays incoming food donations from supermarkets and requests from member food banks across Ireland.

## Features

- **Dashboard** - Overview of donations, requests, expiring items, and membership stats
- **Donations** - Track incoming food items with expiry date monitoring
- **Requests** - Manage food bank requests with membership tier system
- **Membership Tiers** - Basic, Bronze, Silver, Gold tiers with quantity limits

## Getting Started

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

## Deployment

```bash
# Build and deploy to AWS S3
npm run build
aws s3 sync ./dist s3://mealmap-ui
```

---

## Style Guide

Based on the FC Brand Guidelines.

### Color Palette

| Color | Hex | CSS Variable | Usage |
|-------|-----|--------------|-------|
| Teal (Primary) | `#357993` | `--fc-teal` | Navbar, buttons, links, primary actions |
| Teal Dark | `#2a6176` | `--fc-teal-dark` | Hover states, gradients |
| Teal Light | `#eaf2f5` | `--fc-teal-light` | Backgrounds, pending badges |
| Green | `#8ED973` | `--fc-green` | Success states, fresh items |
| Green Light | `#E8F5E1` | `--fc-green-light` | Success backgrounds |
| Mint | `#5BC2A8` | `--fc-mint` | Silver tier, secondary accents |
| Coral | `#FF6F61` | `--fc-coral` | Urgent/high priority, errors |
| Coral Light | `#FFE8E5` | `--fc-coral-light` | Warning backgrounds |
| Gold | `#FFC425` | `--fc-gold` | Medium priority, Gold tier |
| Gold Light | `#FFF8E1` | `--fc-gold-light` | Warning backgrounds |
| Gray | `#C4BCB7` | `--fc-gray` | Bronze tier, neutral elements |
| Gray Dark | `#6B6B6B` | `--fc-gray-dark` | Secondary text |
| Gray Light | `#F5F5F5` | `--fc-gray-light` | Borders, backgrounds |

### Typography

**Font Family:** Nunito (Google Fonts)
*Similar rounded style to Omnes from the brand guidelines*

```css
font-family: 'Nunito', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

**Font Weights:**
- 400 - Regular body text
- 500 - Labels, secondary headings
- 600 - Emphasized text, buttons
- 700 - Headings, card titles
- 800 - Page titles, stat values

### Component Patterns

**Cards:**
- White background (`--bg-white`)
- 12px border radius
- 4px colored left border (indicates status/priority)
- Subtle shadow: `0 2px 8px rgba(0, 0, 0, 0.06)`
- Hover lift effect with increased shadow

**Badges:**
- 20px border radius (pill shape)
- 0.75rem font size, 700 weight
- Color-coded backgrounds with matching text

**Status Colors:**
| Status | Background | Text |
|--------|------------|------|
| Pending | `--fc-teal-light` | `--fc-teal` |
| Partial | `--fc-gold-light` | `#E6A800` |
| Fulfilled | `--fc-green-light` | `#5BA847` |

**Priority Colors:**
| Priority | Border/Text | Background |
|----------|-------------|------------|
| High | `--fc-coral` | `--fc-coral-light` |
| Medium | `--fc-gold` | `--fc-gold-light` |
| Low | `--fc-green` | `--fc-green-light` |

**Membership Tier Colors:**
| Tier | Color | Background |
|------|-------|------------|
| Basic | `#6B6B6B` | `#F5F5F5` |
| Bronze | `#C4BCB7` | `#FAF8F7` |
| Silver | `#5BC2A8` | `#E5F6F5` |
| Gold | `#FFC425` | `#FFF8E1` |

### Spacing

- Page padding: 2rem (1rem on mobile)
- Card padding: 1.25rem
- Grid gaps: 1.5rem
- Section margins: 2rem

### Interactive Elements

**Buttons:**
```css
background: var(--fc-teal);
color: white;
border-radius: 8px;
font-weight: 600;
```

**Inputs/Selects:**
```css
border: 2px solid var(--fc-gray-light);
border-radius: 8px;
/* Focus state */
border-color: var(--fc-teal);
```

### Responsive Breakpoints

- `900px` - Switch to single column layouts
- `600px` - Stack navbar, reduce padding
- `500px` - Single column tier grids
