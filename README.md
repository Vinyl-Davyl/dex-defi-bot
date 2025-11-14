# dex defi bot 

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License: MIT">
  <img src="https://img.shields.io/badge/Telegram-Bot-blue" alt="Telegram Bot">
</p>

A powerful Telegram bot that helps users find the best yield opportunities in DeFi, analyze market sentiment, and make data-driven trading decisions. Built for the Sentient AI Agent Builders Program.

## 🌟 Features

### Yield Finding

- **Top Yields**: Discover the highest APY opportunities across DeFi protocols
- **Protocol-Specific Yields**: Find yields on specific protocols like Aave, Compound, etc.
- **Chain-Specific Yields**: Find yields on specific blockchains like Ethereum, Solana, etc.
- **Yield Comparison**: Compare yields between different protocols
- **Personalized Recommendations**: Get yield recommendations based on preferences

### Market Analysis

- **Token Price Tracking**: Get current prices and 24h changes
- **Market Sentiment Analysis**: Analyze overall market sentiment
- **Token-Specific Sentiment**: Get sentiment analysis for specific tokens
- **Trading Signals**: Receive technical and fundamental trading signals
- **Yield Entry Recommendations**: Get timing recommendations for entering yield positions

### AI-Powered Insights

- **Yield Opportunity Analysis**: Get AI analysis of yield opportunities
- **Trading Insights**: Receive AI-generated trading insights
- **Yield Comparison Explanations**: Understand differences between yield options
- **Market Sentiment Summaries**: Get AI summaries of market sentiment
- **Yield Entry Explanations**: Understand the reasoning behind yield entry recommendations

## Commands

| Command              | Description                                         | Example                         |
| -------------------- | --------------------------------------------------- | ------------------------------- |
| `/start`             | Start the bot and get welcome message               | `/start`                        |
| `/help`              | Show available commands and their descriptions      | `/help`                         |
| `/top_yields`        | Get top yield opportunities                         | `/top_yields 10`                |
| `/yield_by_protocol` | Get yields for a specific protocol                  | `/yield_by_protocol aave`       |
| `/yield_by_chain`    | Get yields for a specific blockchain                | `/yield_by_chain ethereum`      |
| `/compare_yields`    | Compare yields between protocols                    | `/compare_yields aave,compound` |
| `/recommend_yields`  | Get personalized yield recommendations              | `/recommend_yields stable`      |
| `/token_price`       | Get current price of a token                        | `/token_price bitcoin`          |
| `/market_sentiment`  | Get overall market sentiment                        | `/market_sentiment`             |
| `/token_sentiment`   | Get sentiment analysis for a token                  | `/token_sentiment ethereum`     |
| `/trading_signals`   | Get trading signals for a token                     | `/trading_signals bitcoin`      |
| `/yield_entry`       | Check if it's a good time to enter a yield position | `/yield_entry ethereum`         |

## Setup and Installation

### Prerequisites

- Python 3.9 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Fireworks AI API Key (for AI-powered insights)
- DeFiLlama API access (free)
- CoinGecko API access (free)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/dex-defi-bot.git
   cd dex-defi-bot
   ```

2. Create a `.env` file in the root directory with your API keys:

   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   FIREWORKS_API_KEY=your_fireworks_api_key
   BOT_NAME=Dex Defi Bot
   ```

3. Run the setup script:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

## 🏗️ Project Structure

```
DeFi-Yield-Finder/
├── src/
│   ├── bot/
│   │   └── bot.py           # Telegram bot implementation
│   ├── config/
│   │   └── config.py        # Configuration settings
│   ├── services/
│   │   ├── ai_service.py    # AI-powered analysis services
│   │   ├── yield_service.py # DeFi yield data services
│   │   └── trading_service.py # Trading and sentiment services
│   ├── utils/
│   │   ├── helpers.py       # Helper functions
│   │   └── logger.py        # Logging configuration
│   └── main.py              # Main entry point
├── data/                    # Data storage directory
├── logs/                    # Log files directory
├── .env                     # Environment variables
├── .env.example            # Example environment file
├── requirements.txt         # Python dependencies
├── run.sh                   # Setup and run script
└── README.md               # Project documentation
```

## API Integrations

- **DeFiLlama API**: Used to fetch yield data across DeFi protocols
- **CoinGecko API**: Used for token prices and market data
- **Fireworks AI API**: Used for AI-powered analysis and insights

## Technologies Used

- **Python**: Core programming language
- **python-telegram-bot**: Framework for Telegram bot development
- **aiohttp**: Asynchronous HTTP client for API requests
- **Fireworks AI**: AI model for generating insights and analysis
- **asyncio**: For asynchronous programming

## Data Sources

- **DeFiLlama**: For yield data across DeFi protocols
- **CoinGecko**: For token prices, market caps, and trading volumes
- **TradingView**: For technical indicators and trading signals

## Privacy and Security

- All API keys are stored locally in the `.env` file and never shared
- No user data is collected or stored
- All API requests are made directly from the bot to the respective APIs

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Sentient AI](https://sentient.io/) for the Agent Builders Program
- [DeFiLlama](https://defillama.com/) for providing comprehensive DeFi data
- [CoinGecko](https://www.coingecko.com/) for token and market data
- [Fireworks AI](https://fireworks.ai/) for AI capabilities

## Contact

For questions or feedback, please open an issue on this repository or contact the maintainer.

