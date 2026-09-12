# BANORTE MUUK
Personalized UI for Banorte users

## Format
```
src/
├── screens/
│   ├── HomeScreen.tsx
│   └── ...
│
├── components/
│   ├── ChatInput.tsx
│   └── ...
│
├── a2ui/
│   └── renderer/
│
└── api/
    └── backend.ts
```
````
backend/
│
├── server.ts
│
├── agent/
│   ├── gemini.ts
│   └── prompts.ts
│
├── middleware/
│   ├── auth.ts
│   ├── validation.ts
│   ├── permissions.ts
│   └── uiPlanner.ts
│
├── database/
│   └── tigerdata.ts
│
├── mcp/
│   └── bankServer.ts
│
├── a2ui/
│   └── generator.ts
│
└── voice/
    └── elevenlabs.ts
```