# Documentation Assistant - React + Next.js Frontend

Modern React frontend for the Documentation Assistant, replacing the Streamlit UI.

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS v3
- **State Management**: Zustand
- **Data Fetching**: Axios + SWR
- **Visualizations**: React Flow, Recharts
- **UI Components**: Headless UI, Heroicons

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Home page (redirects to login)
│   │   ├── login/              # Login page
│   │   ├── register/           # Registration page
│   │   ├── chat/               # Chat interface (in progress)
│   │   └── globals.css         # Global styles
│   ├── components/             # React components
│   │   ├── auth/               # Authentication components
│   │   ├── chat/               # Chat interface components
│   │   ├── admin/              # Admin dashboard components
│   │   ├── knowledge-graph/    # Knowledge graph visualization
│   │   ├── analysis/           # Decision/gap/impact analysis
│   │   └── ui/                 # Reusable UI components
│   ├── lib/                    # Utilities and API clients
│   │   ├── api.ts              # Base API client (Axios)
│   │   ├── api/                # API modules
│   │   │   ├── auth.ts         # Authentication API
│   │   │   ├── chat.ts         # Chat API
│   │   │   ├── sync.ts         # Data sync API
│   │   │   ├── knowledge-graph.ts  # Knowledge graph API
│   │   │   ├── admin.ts        # Admin API
│   │   │   └── decisions.ts    # Decision analysis API
│   │   └── utils.ts            # Utility functions
│   ├── stores/                 # Zustand state stores
│   │   ├── auth.ts             # Authentication state
│   │   └── chat.ts             # Chat state
│   └── types/                  # TypeScript type definitions
│       └── index.ts            # All types
├── public/                     # Static assets
├── .env.local                  # Environment variables
├── next.config.js              # Next.js configuration
├── tailwind.config.ts          # Tailwind CSS configuration
├── tsconfig.json               # TypeScript configuration
└── package.json                # Dependencies

```

## Features Implemented

### ✅ Completed
- [x] Next.js project setup with TypeScript and Tailwind CSS
- [x] Comprehensive API client library with modules for:
  - Authentication (login, register, OAuth)
  - Chat (questions, streaming, analytics)
  - Data sync (Confluence, Jira, Repository)
  - Knowledge graph (relationships, tickets, developers)
  - Admin (organization metrics, health monitoring)
  - Decision analysis
- [x] Zustand stores for state management (auth, chat)
- [x] TypeScript type definitions for all data models
- [x] Login page with demo account info
- [x] Register page with validation
- [x] Protected route wrapper
- [x] **Full chat interface with:**
  - Real-time chat with AI assistant
  - Source filtering (Confluence, Jira, Git, Code)
  - AI settings (model, max results, search type)
  - Source badges showing document types
  - Expandable source details
  - Auto-scrolling messages
  - Loading states
  - Error handling
- [x] **Feature-rich sidebar with:**
  - User info and organization details
  - Source filters
  - AI settings panel
  - Navigation to other features
  - Usage quota display
  - Clear chat and logout buttons

### 🚧 In Progress
- [ ] Knowledge graph visualization (React Flow)

### 📋 Pending
- [ ] Admin dashboard with charts
- [ ] Decision analysis pages
- [ ] Gap analysis pages
- [ ] Impact analysis pages
- [ ] Docker integration

## Getting Started

### Development

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Build

```bash
npm run build
npm start
```

### Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:4000
```

## Demo Accounts

- **Admin**: admin@acmecorp.com / admin123
- **User**: john@acmecorp.com / user123

## Migration from Streamlit

This frontend replaces the Python Streamlit UI (`ui/`) with a modern React + Next.js application while maintaining feature parity with the original implementation.

### Original Streamlit Components Mapped to React

| Streamlit Component | React Equivalent | Status |
|---------------------|------------------|--------|
| `components/auth.py` | `src/app/login`, `src/app/register` | ✅ Complete |
| `components/chat.py` | `src/app/chat` (WIP) | 🚧 In Progress |
| `components/sidebar.py` | Chat sidebar (TODO) | 📋 Pending |
| `components/admin.py` | Admin dashboard (TODO) | 📋 Pending |
| `components/relationships.py` | Knowledge graph (TODO) | 📋 Pending |
| `components/decisions.py` | Decision analysis (TODO) | 📋 Pending |
| `components/gaps.py` | Gap analysis (TODO) | 📋 Pending |
| `components/impact.py` | Impact analysis (TODO) | 📋 Pending |

## API Integration

All API calls use the centralized API client with automatic:
- JWT token injection
- Error handling
- Authentication redirects on 401 errors
- TypeScript type safety

Example:
```typescript
import { chatApi } from '@/lib/api'

const response = await chatApi.ask({
  question: 'What is this codebase about?',
  model: 'mistral',
  max_results: 5,
})
```

## State Management

Using Zustand with persistence:

```typescript
import { useAuthStore } from '@/stores/auth'

function Component() {
  const { user, login, logout } = useAuthStore()
  // ...
}
```
