# PayPilot Core Foundation

Build the foundation of a desktop-first web application called PAYPILOT.

Do NOT build all application modules yet.

This first build is ONLY for the application shell and the cinematic 3D PayPilot Core.

PAYPILOT is a spatial AI Revenue Operating System for merchants.

The key product idea:

THE PAYPILOT CORE IS THE APPLICATION'S PRIMARY NAVIGATION.

This is NOT a generic SaaS dashboard.

It is a full-screen desktop web application where the user enters a spatial 3D environment and navigates into application modules through interactive nodes.

TECH STACK:

- React
- TypeScript
- Tailwind CSS
- React Router
- Three.js
- React Three Fiber
- @react-three/drei
- GSAP
- GSAP ScrollTrigger
- Lucide React

Install the required packages.

TARGET:

1440×900 desktop.

Desktop is the primary experience.

Do NOT create phone mockups.
Do NOT create mobile-first layouts.
Do NOT create a sidebar-heavy dashboard.
Do NOT use static images as the 3D Core.

==================================================
VISUAL IDENTITY
==================================================

Background:
near-black graphite

Typography:
warm ivory / off-white

Secondary:
muted gray

Accent:
restrained warm red/orange

Style:

premium
cinematic
financial
intelligent
spatial
minimal
high-end

Avoid:

cyberpunk
excessive neon
excessive gradients
generic SaaS cards
crypto-dashboard aesthetics
gaming UI

==================================================
APPLICATION SHELL
==================================================

Create a minimal desktop header.

Left:

PAYPILOT

Center:

CORE

Right:

COMMAND
ACTIVITY
merchant profile

The navigation must be subtle.

The 3D Core should occupy most of the viewport.

==================================================
PAYPILOT CORE
==================================================

Create an actual React Three Fiber scene.

The central object is PAYPILOT CORE.

It must NOT be a simple glowing sphere.

Create an abstract financial intelligence engine using:

- concentric geometric layers
- orbital rings
- connected points
- small particles
- thin data pathways
- subtle internal glow
- transparent layers
- depth
- slow rotation

The Core should feel like a sophisticated computational financial system.

==================================================
SPATIAL NODES
==================================================

Create these actual 3D interactive nodes:

REVENUE
CUSTOMERS
OPPORTUNITIES
AI COPILOT
GUARDIAN
EXECUTION
AUDIT
AI COMMERCE

They must be actual Three.js / React Three Fiber objects.

Do NOT put them inside rectangular cards.

Each node should have:

module name
small metric
spatial marker

Examples:

REVENUE
₹8.42L

OPPORTUNITIES
₹73,420

CUSTOMERS
1,024

GUARDIAN
17 BLOCKED

Place nodes around the Core at different positions and depths.

Do not make the scene a flat diagram.

Use perspective.

==================================================
CONNECTIONS
==================================================

Connect nodes to the Core using thin elegant pathways.

Use subtle moving particles to represent information flow.

Do not create a bright spiderweb.

==================================================
INTERACTION
==================================================

Hovering a node should:

- slightly increase scale
- increase brightness
- activate its connection
- reveal its metric

Clicking a node should:

- make it dominant
- move the camera toward it
- push other nodes into the background
- prepare the transition into its future application module

For now, clicking can navigate to placeholder routes:

/dashboard
/customers
/opportunities
/copilot
/guardian
/actions
/audit
/commerce

Create these routes with minimal placeholder pages containing:

← CORE

MODULE NAME

Do not build the full module interfaces yet.

==================================================
SCROLL EXPERIENCE
==================================================

Use GSAP ScrollTrigger.

Create a cinematic sequence:

SCROLL 1:
PayPilot Core appears.

SCROLL 2:
Core rotates and becomes active.

SCROLL 3:
Data particles and pathways appear.

SCROLL 4:
Spatial nodes emerge.

SCROLL 5:
Complete PayPilot system becomes visible.

The animation must feel like camera choreography rather than simple fade-ins.

Use:

camera movement
depth
parallax
rotation
node emergence
particle motion

Respect prefers-reduced-motion.

==================================================
HERO TEXT
==================================================

Place refined editorial typography around the scene.

YOUR REVENUE
IS TALKING.

Supporting text:

PayPilot continuously discovers and evaluates revenue opportunities across your merchant ecosystem.

Small system indicators:

PAYPILOT CORE / ONLINE

AI CONFIDENCE
94%

OPPORTUNITIES
27

RECOVERABLE
₹73,420

These must feel integrated into the spatial interface, not like dashboard cards.

==================================================
CODE ARCHITECTURE
==================================================

Create reusable components:

PayPilotCore
CoreNode
CoreConnections
CoreParticles
CoreCameraController
SpatialLabel
ApplicationShell

Create a centralized mock data file.

Use TypeScript interfaces.

Keep the 3D scene isolated and modular so it can later be enhanced with more advanced Three.js effects.

Do not create one giant React component.

==================================================
MOST IMPORTANT REQUIREMENT
==================================================

This first version is judged primarily on the PayPilot Core.

The result must feel like:

ENTER PAYPILOT
↓
ENTER A LIVING FINANCIAL SYSTEM
↓
SEE THE CORE
↓
SEE THE SPATIAL NETWORK
↓
SELECT A NODE
↓
TRAVEL INTO THE APPLICATION

It must NOT feel like:

"Here is a SaaS dashboard with a 3D animation."

Build ONLY this foundation and Core experience in this iteration.

Do not spend time implementing the full application modules yet.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/0391560b-a353-42ce-b2ef-9b28b124688b).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
