import asyncio
import logging
from mcp.server.fastmcp import FastMCP

# Create a FastMCP server
mcp = FastMCP("Currency Converter")

# Mock exchange rates
RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "JPY": 150.0,
    "CAD": 1.35,
    "AUD": 1.52,
}

@mcp.tool()
async def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """
    Converts currency amount from one currency to another.
    Supported currencies: USD, EUR, GBP, JPY, CAD, AUD.
    """
    from_curr = from_currency.upper()
    to_curr = to_currency.upper()
    
    if from_curr not in RATES or to_curr not in RATES:
        return f"Error: Unsupported currency. Supported: {', '.join(RATES.keys())}"
    
    # Convert to USD first (base), then to target
    amount_in_usd = amount / RATES[from_curr]
    converted_amount = amount_in_usd * RATES[to_curr]
    
    return f"{amount} {from_curr} = {converted_amount:.2f} {to_curr}"

if __name__ == "__main__":
    # Run the server using stdio transport (default for FastMCP)
    mcp.run()
