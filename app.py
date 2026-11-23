import time
import streamlit as st
from google import genai

st.set_page_config(page_title="Refinery AI GRM Optimizer", page_icon="🛢️", layout="wide")
st.title("🛢️ Indian Refinery Crude Assay & AI GRM Optimizer")
st.write("Select a crude slate and market prices to calculate GRM and get operational/corrosion insights.")

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

crude_grades = {
    "Arab_Heavy_Sour": {
        "crude_cost_usd": 92.0,
        "yields": {"Diesel (HSD)": 0.40, "Petrol (MS)": 0.20, "ATF (Jet Fuel)": 0.09, "Naphtha": 0.08, "LPG": 0.05, "Petcoke/FO": 0.13, "Fuel & Loss": 0.05}
    },
    "Brent_Light_Sweet": {
        "crude_cost_usd": 98.5,
        "yields": {"Diesel (HSD)": 0.44, "Petrol (MS)": 0.26, "ATF (Jet Fuel)": 0.12, "Naphtha": 0.07, "LPG": 0.05, "Petcoke/FO": 0.02, "Fuel & Loss": 0.04}
    },
    "Arabian_Light": {
        "crude_cost_usd": 96.0,
        "yields": {"Diesel (HSD)": 0.37, "Petrol (MS)": 0.21, "ATF (Jet Fuel)": 0.13, "Naphtha": 0.13, "LPG": 0.06, "Petcoke/FO": 0.05, "Fuel & Loss": 0.05}
    },
    "Russian_Urals_Medium_Sour": {
        "crude_cost_usd": 82.50,
        "yields": {"Diesel (HSD)": 0.42, "Petrol (MS)": 0.21, "ATF (Jet Fuel)": 0.10, "Naphtha": 0.08, "LPG": 0.05, "Petcoke/FO": 0.09, "Fuel & Loss": 0.05}
    },
    "Basrah_Heavy_Iraq": {
        "crude_cost_usd": 88.00,
        "yields": {"Diesel (HSD)": 0.36, "Petrol (MS)": 0.18, "ATF (Jet Fuel)": 0.08, "Naphtha": 0.07, "LPG": 0.04, "Petcoke/FO": 0.21, "Fuel & Loss": 0.06}
    },
    "Nigerian_Bonny_Light": {
        "crude_cost_usd": 99.50,
        "yields": {"Diesel (HSD)": 0.46, "Petrol (MS)": 0.27, "ATF (Jet Fuel)": 0.13, "Naphtha": 0.06, "LPG": 0.03, "Petcoke/FO": 0.01, "Fuel & Loss": 0.04}
    },
    "Mumbai_High_Indian_Sweet": {
        "crude_cost_usd": 95.00,
        "yields": {"Diesel (HSD)": 0.43, "Petrol (MS)": 0.25, "ATF (Jet Fuel)": 0.11, "Naphtha": 0.09, "LPG": 0.05, "Petcoke/FO": 0.03, "Fuel & Loss": 0.04}
    }
}

product_prices_inr = {
    "Diesel (HSD)": 70.50, "Petrol (MS)": 70.00, "ATF (Jet Fuel)": 73.00,
    "Naphtha": 53.00, "LPG": 35.80, "Petcoke/FO": 42.00, "Fuel & Loss": 0.00
}

col1, col2 = st.columns(2)
with col1:
    crude_name = st.selectbox("Select Crude Grade", list(crude_grades.keys()))
    default_cost = crude_grades[crude_name]["crude_cost_usd"]
    crude_price_usd = st.number_input("Landed Crude Cost ($ / bbl)", value=float(default_cost), step=0.5)
    usd_to_inr = st.number_input("Exchange Rate (₹ per $)", value=94.5, step=0.1)
    diesel_price = st.number_input("Diesel Gate Price (₹ / Litre)", value=70.5, step=0.5)
    petrol_price = st.number_input("Petrol Gate Price (₹ / Litre)", value=70.0, step=0.5)
    run_btn = st.button("Calculate GRM & Ask AI Economist", type="primary")

with col2:
    if run_btn:
        LITRES_PER_BARREL = 159.0
        crude = crude_grades[crude_name]
        prices = product_prices_inr.copy()
        prices["Diesel (HSD)"] = diesel_price
        prices["Petrol (MS)"] = petrol_price

        crude_cost_inr = crude_price_usd * usd_to_inr
        total_revenue_inr = 0.0
        breakdown = []

        for product, yield_pct in crude["yields"].items():
            litres = LITRES_PER_BARREL * yield_pct
            rate = prices.get(product, 0.0)
            val = litres * rate
            total_revenue_inr += val
            breakdown.append(f"- **{product}**: {yield_pct*100:.0f}% ({litres:.1f} L) @ ₹{rate:.2f}/L = **₹{val:,.2f}**")

        grm_inr = total_revenue_inr - crude_cost_inr
        grm_usd = grm_inr / usd_to_inr

        st.subheader(f"Gross Refining Margin: ₹{grm_inr:,.2f} / bbl (${grm_usd:.2f} / bbl)")
        st.markdown("\n".join(breakdown))

        prompt = f"""
        You are a senior Indian refinery LP & crude economist.
        Crude: {crude_name} | Cost: ${crude_price_usd}/bbl | FX: ₹{usd_to_inr}/$
        Calculated GRM: ₹{grm_inr:,.2f}/bbl (${grm_usd:.2f}/bbl).
        In 3 short bullet points, comment on:
        1. Whether this GRM covers typical Indian complex refinery OpEx (~$2.50-$3.50/bbl) to yield a healthy Net Margin.
        2. Key operational/metallurgical watchouts (e.g., sulfur/TAN corrosion in CDU/VDU or hydrotreating load) for {crude_name}.
        """

        with st.spinner("Consulting AI Refinery Economist..."):
            for model_name in ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemma-4-31b-it"]:
                try:
                    ai_response = client.models.generate_content(model=model_name, contents=prompt)
                    st.info(f"**AI Economist Notes *(via {model_name})*:**\n\n{ai_response.text}")
                    break
                except Exception as e:
                    time.sleep(2)
