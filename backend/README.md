# CVForge NestJS Backend

Full NestJS backend for CVForge connected directly to MongoDB Atlas.

## Features
- **User Authentication**: Register, Login, JWT Strategy, Profile retrieval.
- **Auto-Sync Schema & Database**: Automatically verifies connection to MongoDB Atlas, creates the database (`cvforge`) and collections (`users`, `cvs`, `cover_letters`) if they do not exist, and synchronizes indexes when `DB_AUTO_SYNC=true` / `UPDATE_SCHEMA_ON_CHANGE=true`.
- **CV Persistence**: Create, update, retrieve, and delete CV documents and snapshots.
- **Cover Letter Persistence**: Create, update, retrieve, and delete Cover Letter documents.
- **Unified Document Dashboard**: Aggregates all user documents for the "My CVs" gallery.
- **CORS & Dual Mode**: Ready for direct browser integration with authorization headers or guest identifiers.

## Configuration (.env)
```env
db_url="mongodb+srv://telay:telaynew5870@cluster0.rnebbwt.mongodb.net/"
DB_NAME="cvforge"
DB_AUTO_SYNC="true"
UPDATE_SCHEMA_ON_CHANGE="true"
PORT=3000
JWT_SECRET="cvforge_jwt_secret_key_2026_super_secure"
JWT_EXPIRES_IN="7d"
CORS_ORIGIN="*"
```

## Running the Server
```bash
# 1. Install dependencies
npm install

# 2. Start in development watch mode
npm run start:dev

# 3. Production build and run
npm run build
npm run start:prod
```

## API Endpoints
- `POST /api/auth/register` - Create new user account
- `POST /api/auth/login` - Authenticate and return JWT token
- `GET  /api/auth/me` - Get profile of authenticated user
- `POST /api/cv/save` - Save current CV state to MongoDB
- `GET  /api/cv` - Retrieve current / latest CV
- `GET  /api/cv/all` - List all CVs of user
- `GET  /api/cv/:id` - Get specific CV
- `DELETE /api/cv/:id` - Archive / delete CV
- `POST /api/cover-letter/save` - Save Cover Letter state to MongoDB
- `GET  /api/cover-letter` - Retrieve latest Cover Letter
- `GET  /api/cover-letter/all` - List all Cover Letters of user
- `GET  /api/cover-letter/:id` - Get specific Cover Letter
- `DELETE /api/cover-letter/:id` - Archive / delete Cover Letter
- `GET  /api/documents` - Get all user documents (CVs + Cover Letters)
