# Football AI Panel Discussion

An AI-powered football panel discussion system that generates dynamic conversations between expert agents about football matches. The system uses AI agents to analyze match data, create engaging discussions, and can optionally generate audio or video output.

## Technologies Used

### Core Technologies

- **LangChain**: For AI agent orchestration and conversation management
- **OpenAI GPT-4**: For natural language generation and agent responses
- **ElevenLabs**: For text-to-speech generation
- **FFmpeg**: For audio processing and segment combination
- **Docker**: For containerization and easy deployment

### Data Processing

- **Pydub**: For audio file manipulation and processing
- **Python-dotenv**: For environment variable management

### Data Collection Tools (Development Only)

- **NLTK**: Used in development for analyzing YouTube panelist patterns
- **Speech Recognition**: Used in development for analyzing YouTube audio

### APIs and Services

- **AI-football API**: For match data and statistics
- **OpenAI API**: For AI model access
- **ElevenLabs API**: For voice synthesis

### Development Tools

- **Python 3.8+**: Main programming language
- **Docker Compose**: For container orchestration
- **Git**: For version control

## Features

### Approach 2 (Current Working Version)

- AI-powered panel discussion with multiple expert agents
- Match data analysis from AI-football API
- Dynamic conversation generation with context awareness
- Text-to-speech capabilities using YouTube video learning
- Comprehensive match analysis including:
  - Statistics and data insights
  - Player performance analysis
  - Tactical breakdowns
  - Match conclusions and team performance evaluation

### Approach 1 (Experimental)

- Text-to-video generation with AI avatars
- Currently has an issue with avatar synchronization
- Work in progress for future development

## Setup and Usage

### Using Docker (Recommended)

1. Build and start the container:

```bash
cd backend
docker-compose up -d
```

2. Connect to the container:

```bash
docker-compose exec football-ai-panel bash
```

3. Run the scripts:

```bash
# Generate panel discussion
python approach_2/football_panel.py <match_id>

# Generate audio (optional)
python approach_2/generate_audio.py --script approach_2/scripts/<script_name>.txt

Example with match ID:
python approach_2/football_panel.py 1374812

Example with audio generation:
python approach_2/generate_audio.py --script approach_2/scripts/inter_psg.txt
```

### Manual Setup

1. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

```bash
cp .env.example .env
# Add your API keys to .env
```

## Project Structure

```
backend/
├── approach_1/          # Experimental text-to-video approach
├── approach_2/          # Current working implementation
│   ├── football_panel.py    # Main panel discussion generator
│   ├── generate_audio.py    # Audio generation script
├── services/            # External services
└── match_data/         # Football match data
```

## How It Works

### Panel Discussion Generation

1. Fetches match data from AI-football API
2. Creates multiple AI agents with different expertise:
   - Host: Manages discussion flow
   - Stats Expert: Analyzes match statistics
   - Tactical Analyst: Discusses formations and strategies
3. Generates a natural conversation based on match data
4. Includes statistics, player analysis, and match conclusions

### Audio Generation

- Uses YouTube video learning for text-to-speech
- Generates individual audio segments for each speaker
- Combines segments into a final audio file

## Project Timeline

### Week 1: Core Development

- Created all AI agents with distinct personalities
- Implemented API integrations (OpenAI, API-Football)
- Set up basic conversation logic and memory management
- Developed initial system prompts and personality profiles

### Week 2: Approach 1 - Text-to-Video

- Implemented D-ID integration for avatar generation
- Tested video generation with AI avatars
- Faced challenges with avatar synchronization
- Made strategic decision to pivot to Approach 2 due to time constraints

### Week 2-3: Approach 2 - Text-to-Speech

- Switched focus to audio-based solution
- Implemented ElevenLabs TTS integration
- Refined prompt engineering for more natural conversations
- Fine-tuned voice settings and personality traits
- Improved conversation syntax and flow
- Enhanced audio processing and transitions

### Current Focus

- Optimizing prompt engineering
- Fine-tuning voice settings
- Improving conversation naturality
- Enhancing personality consistency

## Future Development

### Approach 1 Improvements

- Fix avatar synchronization issues
- Implement proper speaker-to-avatar mapping
- Enhance video generation quality

### General Improvements

- Add more AI agents with different expertise
- Enhance natural language generation
- Improve audio quality and speaker differentiation
- Add support for more match types and competitions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License
