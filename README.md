# discord-bot
Translates messages (sometimes) and plays music

### Setup
1. Install uv
    1. `curl -LsSf https://astral.sh/uv/install.sh | sh`
    2. `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
3. `uv sync`
2. Create `.env` file with "DISCORD_TOKEN=your_token"

4. Run `drive_integration.py` to initialize `credentials.json` delete if already exists
5. Get `variables.ini`

### Running the bot
`uv run src/main.py`