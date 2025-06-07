# Football AI Panel Discussion

An AI-powered football panel discussion system that generates dynamic conversations between expert agents about football matches.

## Architecture

### LangChain Components

- **DiscussionChain**: Manages conversation flow and turn-taking
- **RAGChain**: Handles football knowledge retrieval using FAISS vector store
- **BaseAgent**: LangChain-based agent with tools and memory

### Agents

1. **Show Host**

   - Manages discussion flow
   - Ensures balanced participation
   - Guides topic transitions

2. **Stats Expert**

   - Analyzes match statistics
   - Provides data-driven insights
   - Uses RAG for historical context

3. **Tactical Analyst**
   - Discusses formations and strategies
   - Analyzes key tactical moments
   - Provides expert tactical insights

### Key Features

- LangChain-based agent orchestration
- FAISS vector store for efficient knowledge retrieval
- Conversation memory management
- Dynamic topic selection
- Natural turn-taking system

## Setup

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

4. Initialize the vector store:

```bash
python -m backend.initialize_rag
```

5. Run the application:

```bash
uvicorn backend.main:app --reload
```

## Project Structure

```
backend/
├── agents/          # Agent implementations
├── chains/          # LangChain components
├── models/          # Pydantic models
├── services/        # External services
└── match_data/      # Football match data
```

## Usage

1. Start a new discussion:

```python
from backend.panel_discussion import PanelDiscussion

panel = PanelDiscussion(match_id="1234")
script = await panel.generate_discussion()
```

2. API Endpoints:

```bash
POST /api/discussions/start
GET /api/discussions/{discussion_id}
```

## Development

- Use `pre-commit` hooks for code quality
- Run tests with `pytest`
- Format code with `black`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License
