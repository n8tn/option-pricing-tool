import pandas as pd
import numpy as np
from pprint import pprint
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import norm
import streamlit as st

#Creates a wide layout and title for the Streamlit app
st.set_page_config(layout="wide")

st.title('Options Pricing & PnL Tool 💵')

#Provides a description on the app and how to use it
st.write(
        f"This tool performs two key functions: **(1)** It calculates option prices using the five factors in the Black-Scholes pricing model—**Stock Price, Strike Price, Risk-Free Interest Rate, Volatility, & Time To Expiration**; **(2)** It computes Profit and Loss (PnL) based on user-selected naked strategies and input parameters. A practical use case for this tool would be initializing your strategy and inputs at time **(_T0_)**, then adjusting parameters at time **(_T1_)** to simulate potential payoffs under different scenarios."
        )

st.latex(r'''
         *Call Formula: C(S_{t},K,t)=S_{t}\Phi (d_{1})-Ke^{-r(T-t)}\Phi (d_{2}), *Put Formula: P(S_{t},K,t)=Ke^{-r(T-t)}\Phi (-d_{2})-S_{t}\Phi (-d_{1}), *Parameters: d_{1}=\frac{\ln\frac{S_{t}}{K} + (r + \frac{\sigma^2}{2})\tau}{\sigma\sqrt{\tau}}, d_{2}=d_{1}-\sigma\sqrt{\tau}
         ''')

#Creates sections for user parameters
st.subheader("Choose Your :red[Parameters] 🎯")
K = st.slider('Strike Price', min_value=50, max_value=200, value=95, step=1, format = "$%d")

col1, col2, col3 = st.columns([1,1,1.5])

with st.container():
    st.text("") # Adds space

    with col1:
        type = st.selectbox("Choose a naked option:", ("Call", "Put"))
    with col2:
        position = st.selectbox("Choose a position:", ("Long", "Short"))

with st.container():    
    with col1:
        st.text("") # Adds space
        st.subheader("At Time _T0_")
        S1 = st.slider('Underlying Stock Price at _T0_', min_value=50, max_value=200, value=100, step=1, format = "$%d")
        r1 = st.slider('Risk Free Rate at _T0_', min_value=0.01, max_value=0.10, value=0.03, step=0.01)
        v1 = st.slider('Volatility at _T0_', min_value=0.01, max_value=1.0, value=0.20, step=0.01)
        t1 = st.slider('Days to Expiration at _T0_', min_value=1, max_value=730, value=60, step=1)/365

with st.container():
    with col2:
        st.text("") # Adds space
        st.subheader("At Time _T1_")
        S2 = st.slider('Underlying Stock Price at _T1_', min_value=50, max_value=200, value=101, step=1, format = "$%d")
        r2 = st.slider('Risk Free Rate at _T1_', min_value=0.01, max_value=1.00, value=0.03, step=0.01)
        v2 = st.slider('Volatility at _T1_', min_value=0.01, max_value=1.0, value=0.20, step=0.01)
        t2 = st.slider('Days to Expiration at _T1_', min_value=1, max_value=730, value=40, step=1)/365

# A function for calculating ranges for prices
def ranges(x):
    upper_bound = x + 4
    lower_bound = x - 4
    ranges = np.linspace(lower_bound, upper_bound, 9)
    return(pd.Series(ranges.astype(int)))

# A function for deriving Black-Scholes prices
def BlackScholes(S, K, r, t, v, type = "Call"):
    "Calculate Black-Scholes option price for a call/put"
    d1 = (np.log(S/K) + (r + (v**2)/2)*t) / (v*(t)**0.5)
    d2 = d1 - (v*(t)**0.5)
    try:
        if type == "Call":
            # Call Option Price
            Price = round(norm.cdf(d1, 0, 1)*S - norm.cdf(d2, 0, 1)*K*np.exp(-r*t), 2)
        elif type == "Put":
            # Put Option Price
            Price = round(norm.cdf(-d2, 0, 1)*K*np.exp(-r*t) - norm.cdf(-d1, 0, 1)*S, 2)
        return Price
    except:
        print("Please confirm all option parameters above")

# A function for calculating option payoffs
def calculate_payoff(S1, K, r1, t1, v1, S2, r2, t2, v2, option="Call", position="Long"):
    # Determine option type (Call or Put)
    entry = BlackScholes(S1, K, r1, t1, v1, option)
    exit = BlackScholes(S2, K, r2, t2, v2, option)
    # Calculate net profit or loss
    net = round((exit - entry) * 100, 2) if position == "Long" else round((entry - exit) * 100, 2)
    # Print the result
    return net

#Calculating ranges for spot and strike prices
spot_range = ranges(S2)
strike_range = ranges(K)

#Creates a dataframe of spots and stikes
df = pd.DataFrame(
    [(spot, strike) for spot in spot_range for strike in strike_range],
    columns=['Spot Prices', 'Strike Prices']
)

#Calculates payoffs on a range of spos and strikes
df['P&L'] = df.apply(lambda row: calculate_payoff(S1, row['Strike Prices'], r1, t1, v1, row['Spot Prices'], r2, t2, v2, type, position), axis=1)

# Pivot DataFrame
heatmap_data = df.pivot(index='Spot Prices', columns='Strike Prices', values='P&L')

# Create a custom colormap
c = ["darkred","red","white","green","darkgreen"]
v = [0, .25, .5, .75, 1.]
l = list(zip(v,c))
cmap=LinearSegmentedColormap.from_list('rg',l, N=256)

#Creates a section for creating and displaying the heatmap
with st.container():
    with col3:
        st.subheader(f'A Heatmap of Spot Prices Against Strike Prices 👇')

        #Conditionally format the string result
        net_return = round(calculate_payoff(S1, K, r1, t1, v1, S2, r2, t2, v2, type, position))
        color = "green" if net_return >= 0 else "red"
        emoji = "👍" if net_return >= 0 else "👎"

        st.caption(f"If you went :red[**{position} on a ${K} {type} Strike at _T0_**] & the underlying reached :red[**${S2} at _T1_**], your net return would be :{color}[**${net_return}**{emoji}].")
        # Create an annotated heatmap
        plt.figure(figsize=(10,8))
        plt.rcParams.update({'font.size': 10})
        sns.heatmap(
            heatmap_data,
            cmap=cmap,
            vmin=df['P&L'].min(),
            vmax=df['P&L'].max(),
            annot=True,
            fmt=".0f",
            square=False,
            linewidths=3,
            center=0,
            cbar_kws={'label': 'PnL ($)'}
        )
        st.pyplot(plt)

#Formats the title to be placed higher on the app
st.markdown(
    """
        <style>
            .appview-container .main .block-container {{
                padding-top: {padding_top}rem;
                padding-bottom: {padding_bottom}rem;
                }}

        </style>""".format(
        padding_top=2, padding_bottom=2
    ),
    unsafe_allow_html=True,
)
