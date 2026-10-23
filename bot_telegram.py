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
    if len(df) < 50: return f"Ticker {ticker} data kurang"
    
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA50'] = df['Close'].rolling(50).mean()
    df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
    last = df.iloc[-1]; price = last['Close']
    recent = df.tail(60); high = recent['High'].max(); low = recent['Low'].min(); diff = high-low
    if diff == 0: diff = price * 0.1
    
    fibo = {"0% High":high,"23.6%":high-diff*0.236,"38.2%":high-diff*0.382,"50%":high-diff*0.5,"61.8% GOLDEN":high-diff*0.618,"78.6%":high-diff*0.786,"100% Low":low}
    closest = min(fibo.items(), key=lambda x: abs(x[1]-price))
    levels = sorted(fibo.values(), reverse=True)
    idx = min(range(len(levels)), key=lambda i: abs(levels[i]-price))
    resistances = levels[:idx]
    supports = levels[idx+1:]
    resistances = sorted([r for r in resistances if r > price]) # pastikan di atas harga
    supports = sorted([s for s in supports if s < price], reverse=True) # pastikan di bawah harga

    # --- LOGIKA BARU: TP REALISTIS ---
    if len(resistances) >= 3:
        tp1 = resistances[0]
        tp2 = resistances[1]
        tp3 = resistances[2]
    elif len(resistances) == 2:
        tp1 = resistances[0]
        tp2 = resistances[1]
        tp3 = resistances[1] * 1.08
    elif len(resistances) == 1:
        tp1 = resistances[0]
        tp2 = tp1 * 1.08
        tp3 = tp1 * 1.15
    else: # udah di atas semua resistance
        tp1 = price * 1.07
        tp2 = price * 1.12
        tp3 = price * 1.18

    # CAP biar gak kegedean
    if price < 100: # saham gocap
        tp1 = min(tp1, price * 1.15)
        tp2 = min(tp2, price * 1.25)
        tp3 = min(tp3, price * 1.40)
    elif price < 1000:
        tp1 = min(tp1, price * 1.10)
        tp2 = min(tp2, price * 1.18)
        tp3 = min(tp3, price * 1.25)
    else:
        tp1 = min(tp1, price * 1.06)
        tp2 = min(tp2, price * 1.10)
        tp3 = min(tp3, price * 1.15)

    # --- LOGIKA BARU: SL PASTI DI BAWAH ---
    if supports:
        sl = supports[0] * 0.97 # support terdekat - 3%
    else:
        sl = low * 0.97

    if sl >= price: # SAFETY
        sl = price * 0.93
    
    sl = max(sl, low * 0.80)
    
    risk = abs(price - sl)
    if risk < price * 0.02: risk = price * 0.05 # minimal risk 5% biar RR gak aneh

    rr1 = (tp1-price)/risk; rr2 = (tp2-price)/risk; rr3 = (tp3-price)/risk
    
    text = f"📊 {ticker} | {price:.0f}\nHigh {high:.0f} Low {low:.0f}\nDekat: {closest[0]} {closest[1]:.0f}\n\n--- S & R ---\n"
    for r in resistances[:3][::-1]: text+=f"Resistance: {r:.0f}\n"
    text+=f"--> HARGA: {price:.0f}\n"
    for i,s in enumerate(supports[:3]): text+=f"Support {i+1}: {s:.0f}\n"
    text+=f"\n--- PLAN REALISTIS ---\nEntry: {closest[1]:.0f} - {price:.0f}\n"
    text+=f"TP1: {tp1:.0f} | +{(tp1/price-1)*100:.1f}% | RR 1:{rr1:.1f}\n"
    text+=f"TP2: {tp2:.0f} | +{(tp2/price-1)*100:.1f}% | RR 1:{rr2:.1f}\n"
    text+=f"TP3: {tp3:.0f} | +{(tp3/price-1)*100:.1f}% | RR 1:{rr3:.1f}\n"
    text+=f"SL : {sl:.0f} | {(sl/price-1)*100:.1f}%\n\n"
    text+=f"Rekomendasi: {'AKUMULASI' if rr1 >= 1.5 else 'WAIT & SEE'}"
    return text

async def start(update, context): await update.message.reply_text("Ketik /analisa BBCA")
async def analisa(update, context):
    if not context.args: await update.message.reply_text("Pakai: /analisa BBCA"); return
    hasil = get_analisa(context.args[0]); await update.message.reply_text(hasil)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start)); app.add_handler(CommandHandler("analisa", analisa))
app.run_polling()
