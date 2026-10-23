import yfinance as yf
import ta
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
TOKEN = os.getenv("BOT_TOKEN")

def get_analisa(ticker):
    ticker = ticker.upper().strip()
    if ".JK" not in ticker and len(ticker) <= 5: ticker += ".JK"
    df = yf.Ticker(ticker).history(period="6mo")
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA50'] = df['Close'].rolling(50).mean()
    df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
    last = df.iloc[-1]; price = last['Close']
    recent = df.tail(60); high = recent['High'].max(); low = recent['Low'].min(); diff = high-low
    fibo = {"0% High":high,"23.6%":high-diff*0.236,"38.2%":high-diff*0.382,"50%":high-diff*0.5,"61.8% GOLDEN":high-diff*0.618,"78.6%":high-diff*0.786,"100% Low":low}
    closest = min(fibo.items(), key=lambda x: abs(x[1]-price))
    levels = sorted(fibo.values(), reverse=True)
    idx = min(range(len(levels)), key=lambda i: abs(levels[i]-price))
    resistances = levels[:idx]; supports = levels[idx+1:]
    tp1 = fibo["38.2%"]; tp2 = fibo["23.6%"]; tp3 = fibo["0% High"]; sl = fibo["78.6%"]*0.99
    if price >= fibo["50%"]: tp1=fibo["0% High"]; tp2=tp1*1.02; tp3=tp1*1.05; sl=fibo["38.2%"]
    risk = price-sl if price-sl!=0 else 1
    rr1=(tp1-price)/risk; rr2=(tp2-price)/risk; rr3=(tp3-price)/risk
    text = f"📊 {ticker} | {price:.0f}\nHigh {high:.0f} Low {low:.0f}\nDekat: {closest[0]} {closest[1]:.0f}\n\n--- S & R ---\n"
    for r in resistances[:3][::-1]: text+=f"Resistance: {r:.0f}\n"
    text+=f"--> HARGA SEKARANG: {price:.0f}\n"
    for i,s in enumerate(supports[:3]): text+=f"Support {i+1}: {s:.0f}\n"
    text+="\n--- FIBONACCI MAP ---\n"
    for k,v in fibo.items():
        mark=" <-- KAMU" if k==closest[0] else ""
        text+=f"{k:35} : {v:.0f}{mark}\n"
    text+=f"\n--- TRADING PLAN ---\nEntry Ideal: {closest[1]:.0f} - {price:.0f}\nTP1 (38.2%): {tp1:.0f} | Cuan {(tp1/price-1)*100:.1f}% | RR 1:{rr1:.1f}\nTP2 (23.6%): {tp2:.0f} | Cuan {(tp2/price-1)*100:.1f}% | RR 1:{rr2:.1f}\nTP3 (High) : {tp3:.0f} | Cuan {(tp3/price-1)*100:.1f}% | RR 1:{rr3:.1f}\nSL         : {sl:.0f} | Rugi {(sl/price-1)*100:.1f}%\n\nRekomendasi: {'AKUMULASI' if rr1>1.5 else 'WAIT'}"
    return text

async def start(update, context): await update.message.reply_text("Ketik /analisa BBCA")
async def analisa(update, context):
    if not context.args: await update.message.reply_text("Pakai: /analisa BBCA"); return
    hasil = get_analisa(context.args[0]); await update.message.reply_text(hasil)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start)); app.add_handler(CommandHandler("analisa", analisa))
app.run_polling()