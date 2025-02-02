# discord_ollama_bot

A bot that takes input from discord and starts github actions.

Requires the following environment variables:
- 'DISCORD_TOKEN' = The token for your Discord bot.
- 'OLLAMA_HOST' = The url of your Ollama instance - eg. http://192.168.0.10:11434
- 'OLLAMA_MODEL' = The exact name of the LLM model you would like to use - eg. deepseek-r1:7b. This must already be downloaded to your instance.