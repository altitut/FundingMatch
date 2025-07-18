# FundingMatch Frontend Documentation

## Overview

The FundingMatch frontend is a modern React application built with TypeScript and Tailwind CSS. It provides a clean, intuitive interface for uploading funding opportunities, creating user profiles, and discovering relevant funding matches using AI-powered embeddings.

## Technology Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **Lucide React** - Icon library

## Architecture

### Component Structure

```
frontend/src/
├── App.tsx                    # Main app component with routing
├── components/
│   ├── DataIngestion.tsx      # CSV upload for funding opportunities
│   ├── UserProfile.tsx        # User profile creation
│   ├── Matching.tsx           # Funding opportunity matching
│   └── OpportunityDetail.tsx  # Detailed view with AI explanations
└── index.css                  # Tailwind CSS imports
```

### Backend API Integration

The frontend communicates with a Flask backend via REST API endpoints:

- `GET /api/health` - Health check
- `GET /api/stats` - Database statistics
- `POST /api/ingest/csv` - Upload funding opportunities
- `POST /api/profile/upload` - Upload user documents
- `POST /api/profile/create` - Create user profile
- `POST /api/match` - Find matching opportunities
- `POST /api/opportunity/:index/explain` - Get AI explanations

## Features

### 1. Data Ingestion

**Purpose**: Upload CSV files containing funding opportunities

**Key Features**:
- Drag-and-drop file upload
- Real-time statistics display
- Automatic duplicate handling
- Progress feedback

**CSV Format Requirements**:
- Required columns: `title`, `description`, `url`, `agency`, `keywords`
- Date columns: `close_date`, `due_date`, or `deadline`
- Keywords should be comma-separated

### 2. User Profile

**Purpose**: Create comprehensive user profiles from documents and URLs

**Key Features**:
- Multiple file upload (PDF, JSON)
- URL input for online profiles
- Research interests tagging
- Document type detection

**Supported Documents**:
- PDF files (CV, papers, proposals)
- JSON profile with structured data
- URLs (faculty pages, Google Scholar, etc.)

### 3. Matching

**Purpose**: Find and rank funding opportunities based on semantic similarity

**Key Features**:
- Configurable result count
- Confidence score visualization
- Keyword display
- Direct links to opportunities
- Click-through to detailed view

**Confidence Levels**:
- High (≥70%): Strong alignment with expertise
- Medium (40-69%): Moderate alignment
- Low (<40%): Weak alignment

### 4. Opportunity Detail

**Purpose**: Provide detailed analysis and recommendations for specific opportunities

**Key Features**:
- Full opportunity information
- AI-generated match explanations
- Reusable content identification
- Personalized next steps
- Application tips

## Installation & Setup

### Prerequisites

- Node.js 16+ and npm
- Python 3.8+
- Google Gemini API key

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start development server:
```bash
npm start
```

3. Build for production:
```bash
npm run build
```

### Backend Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables in `.env`:
```
GEMINI_API_KEY=your_api_key_here
```

3. Start Flask server:
```bash
python app.py
```

### Quick Start

Use the provided startup script:
```bash
./start_app.sh
```

This will:
- Install all dependencies
- Start the Flask backend
- Launch the React frontend
- Open the application in your browser

## User Interface Design

### Design Principles

1. **Clean & Modern**: Minimal design with focus on content
2. **Responsive**: Works on desktop and tablet devices
3. **Intuitive Navigation**: Clear section tabs with icons
4. **Visual Feedback**: Loading states, success/error messages
5. **Accessibility**: Semantic HTML, ARIA labels where needed

### Color Scheme

- **Primary**: Indigo (`indigo-600`)
- **Success**: Green (`green-600`)
- **Warning**: Yellow (`yellow-600`)
- **Error**: Red (`red-600`)
- **Background**: Gray (`gray-50`)
- **Cards**: White with shadows

### Component Patterns

1. **Cards**: White backgrounds with subtle shadows
2. **Buttons**: Primary actions in indigo, secondary in gray
3. **Forms**: Consistent input styling with focus states
4. **Alerts**: Color-coded with icons for clarity
5. **Navigation**: Tab-based with active state highlighting

## API Integration

### Error Handling

All API calls include proper error handling:
- Connection errors display user-friendly messages
- Server errors show specific error details
- Loading states prevent duplicate requests
- Timeout handling for long operations

### Data Flow

1. **Upload Flow**:
   - File validation on client
   - Multipart form upload
   - Progress tracking
   - Success/error feedback

2. **Matching Flow**:
   - Profile verification
   - Embedding generation
   - Similarity search
   - Result ranking

3. **Explanation Flow**:
   - Opportunity data caching
   - Async explanation generation
   - Progressive enhancement

## Testing

### Manual Testing Checklist

1. **Data Ingestion**:
   - [ ] Upload valid CSV file
   - [ ] Drag and drop functionality
   - [ ] Error handling for invalid files
   - [ ] Statistics update after upload

2. **User Profile**:
   - [ ] Upload multiple PDFs
   - [ ] Add/remove URLs
   - [ ] Create profile with all fields
   - [ ] Error handling for missing data

3. **Matching**:
   - [ ] Search with different result counts
   - [ ] View confidence scores
   - [ ] Click through to details
   - [ ] Handle no results scenario

4. **Opportunity Detail**:
   - [ ] View full opportunity info
   - [ ] Generate AI explanation
   - [ ] View reusable content
   - [ ] External link functionality

### Automated Testing

Run the test suite:
```bash
python test_frontend.py
```

This tests:
- API connectivity
- Endpoint functionality
- File upload handling
- Frontend build status

## Deployment

### Production Build

1. Build the React app:
```bash
cd frontend
npm run build
```

2. Configure Flask for production:
- Set `DEBUG=False` in `.env`
- Use a production WSGI server (e.g., Gunicorn)
- Configure proper CORS origins

3. Serve static files:
- Flask serves the React build automatically
- Access the app at the Flask server URL

### Environment Variables

Production `.env` file:
```
GEMINI_API_KEY=your_production_key
DEBUG=False
PORT=5000
```

## Troubleshooting

### Common Issues

1. **CORS Errors**:
   - Ensure Flask CORS is properly configured
   - Check API endpoint URLs in frontend

2. **File Upload Failures**:
   - Verify file size limits (16MB default)
   - Check file permissions
   - Ensure upload directory exists

3. **No Matches Found**:
   - Verify user profile was created
   - Check database has opportunities
   - Ensure embeddings were generated

4. **Slow Performance**:
   - Check API rate limits
   - Monitor embedding generation time
   - Consider caching strategies

### Debug Mode

Enable debug logging:
1. Set `DEBUG=True` in `.env`
2. Open browser console for frontend logs
3. Check Flask console for backend logs

## Future Enhancements

1. **User Management**:
   - User authentication
   - Profile persistence
   - Multiple profile support

2. **Advanced Matching**:
   - Filtering by agency/deadline
   - Saved searches
   - Match history

3. **Collaboration**:
   - Share opportunities
   - Team profiles
   - Proposal collaboration

4. **Analytics**:
   - Success tracking
   - Match quality metrics
   - User behavior analytics

## Contributing

### Code Style

- Follow React best practices
- Use TypeScript for type safety
- Keep components focused and reusable
- Write descriptive variable names
- Add comments for complex logic

### Testing Requirements

- Test all new features manually
- Add to test checklist
- Ensure no console errors
- Verify mobile responsiveness

## License

This project is proprietary. All rights reserved.