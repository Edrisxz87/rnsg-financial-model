import math
import pandas as pd
import streamlit as st
import plotly.express as px
from termcolor import colored
from tabulate import tabulate

# ------------------------------------------------------------------
# 1. Interest Calculation Functions
# (Homeowners: compound; Investors: simple)
# ------------------------------------------------------------------

def compound_interest(principal, annual_rate, years):
    """Calculate compound interest for homeowners."""
    return round(principal * (1 + annual_rate/100)**years - principal, 2)

def simple_interest(principal, rate, time):
    """Calculate simple interest for investors."""
    return round(principal * (rate / 100) * time, 2)

def monthly_installment_compound(principal, annual_rate, term_years):
    """Calculate monthly installment (compound interest) for homeowners."""
    monthly_rate = annual_rate / 100 / 12
    num_payments = term_years * 12
    if monthly_rate == 0:
        return principal / num_payments
    return round(principal * monthly_rate * (1 + monthly_rate)**num_payments / 
                 ((1 + monthly_rate)**num_payments - 1), 2)

def monthly_investor_payout(total_investor_interest, term_years):
    """Calculate monthly payout for investors (simple interest)."""
    return round(total_investor_interest / (term_years * 12), 2)

def renosage_profit(homeowner_interest, contractor_share, investor_interest):
    """Calculate RenoSage's annual profit."""
    return round((homeowner_interest + contractor_share) - investor_interest, 2)

def homeowner_investor_surplus(homeowner_interest, investor_interest):
    """Calculate surplus/shortage between homeowner inflow and investor outflow."""
    return round(homeowner_interest - investor_interest, 2)

def renosage_profit_margin_percentage(renosage_profit, loan_amount):
    """Calculate RenoSage's profit margin percentage."""
    return round((renosage_profit / loan_amount) * 100, 2)

# ------------------------------------------------------------------
# 2. Project Count Function
# (Months 1–6 fixed; then growth: 20% for months 7–12, 10% for 13–24, 5% for 25–36)
# ------------------------------------------------------------------

def get_projects_count(month):
    """
    Returns the number of projects launched in a given month.
    Fixed:
      - Months 1 & 2: 0 projects
      - Month 3: 1 project
      - Month 4: 2 projects
      - Month 5: 4 projects
      - Month 6: 5 projects
    Then:
      - Months 7–12: floor(1.2 × previous) [20% growth]
      - Months 13–24: floor(1.1 × previous) [10% growth]
      - Months 25–36: floor(1.05 × previous) [5% growth]
    """
    if not hasattr(get_projects_count, "memo"):
        get_projects_count.memo = {}
    if month in get_projects_count.memo:
        return get_projects_count.memo[month]
    if month in [1, 2]:
        result = 0
    elif month == 3:
        result = 1
    elif month == 4:
        result = 2
    elif month == 5:
        result = 4
    elif month == 6:
        result = 5
    elif 7 <= month <= 12:
        result = int(math.floor(get_projects_count(month - 1) * 1.2))
    elif 13 <= month <= 24:
        result = int(math.floor(get_projects_count(month - 1) * 1.1))
    elif 25 <= month <= 36:
        result = int(math.floor(get_projects_count(month - 1) * 1.05))
    else:
        result = int(math.floor(get_projects_count(month - 1) * 1.05))
    get_projects_count.memo[month] = result
    return result

# ------------------------------------------------------------------
# 3. User Input (Sidebar)
# ------------------------------------------------------------------

def get_user_inputs():
    st.sidebar.header("Input Parameters")
    st.sidebar.markdown("### ASSUMPTIONS")
    st.sidebar.markdown(
        """
- **Term:** 3 years (36 months)
- **Project Counts:**
  - Months 1–2: 0 projects  
  - Month 3: 1 project  
  - Month 4: 2 projects  
  - Month 5: 4 projects  
  - Month 6: 5 projects  
  - Months 7–12: 20% monthly growth  
  - Months 13–24: 10% monthly growth  
  - Months 25–36: 5% monthly growth  
- **FPN:** Fresh Projects Number  
- **OPN:** Ongoing Projects Number  
- **Homeowner Interest:** Compound basis  
- **Investor Interest:** Simple basis
        """
    )
    rbc_rate = st.sidebar.number_input("RBC 5-year Fixed Closed Mortgage Rate (%)", value=5.0, min_value=0.0, step=0.1)
    homeowner_rate = rbc_rate + 1
    st.sidebar.write(f"**Homeowner Interest Rate:** {homeowner_rate} (RBC Rate + 1%)")
    boc_yield = st.sidebar.number_input("BoC 10-Year Bond Yield (%)", value=3.0, min_value=0.0, step=0.1)
    investor_rate = boc_yield + (boc_yield / 2)
    st.sidebar.write(f"**Investor Interest Rate:** {investor_rate} (BoC Yield + BoC Yield/2)")
    loan_amount = st.sidebar.number_input("Loan Amount (CAD $)", value=100000.0, min_value=1000.0, step=1000.0)
    homeowner_term = st.sidebar.slider("Homeowners' Loan Term (Years)", 1, 10, 5)
    investor_term = st.sidebar.slider("Investors' Interest Term (Years)", 1, 10, 5)
    contractor_profit_percentage = st.sidebar.number_input("Contractor Profit Percentage (% of total loan)", value=10.0, min_value=0.0, step=0.1)
    renosage_share = st.sidebar.number_input("RenoSage's Share of Contractor Profit (%)", value=50.0, min_value=0.0, step=1.0)
    reinvest_profit_percentage = st.sidebar.number_input("Reinvestment Profit Percentage per $15k (%)", value=5.0, min_value=0.0, step=0.1)
    reinvest_return_period = st.sidebar.slider("Reinvestment Return Period (Months)", 1, 36, 12)
    return (loan_amount, homeowner_term, investor_term, homeowner_rate,
            investor_rate, contractor_profit_percentage, renosage_share, boc_yield,
            reinvest_profit_percentage, reinvest_return_period)

# ------------------------------------------------------------------
# 4. Scenario Table Generation
# ------------------------------------------------------------------

def generate_scenario(loan_amount, homeowner_term, investor_term, homeowner_rate, investor_rate,
                      contractor_profit_percentage, renosage_share):
    homeowner_interest = compound_interest(loan_amount, homeowner_rate, homeowner_term)
    investor_interest = simple_interest(loan_amount, investor_rate, investor_term)
    m_inst = monthly_installment_compound(loan_amount, homeowner_rate, homeowner_term)
    m_inv = monthly_investor_payout(investor_interest, investor_term)
    contractor_profit = round(loan_amount * (contractor_profit_percentage / 100), 2)
    renosage_share_profit = round(contractor_profit * (renosage_share / 100), 2)
    annual_profit = renosage_profit(homeowner_interest, renosage_share_profit, investor_interest)
    surplus = homeowner_investor_surplus(homeowner_interest, investor_interest)
    results = {
        "Loan (CAD $)": loan_amount,
        "Homeowner Term (Yrs)": homeowner_term,
        "Investor Term (Yrs)": investor_term,
        "Homeowner Rate": homeowner_rate,
        "Investor Rate": investor_rate,
        "Homeowner Monthly Installment": m_inst,
        "Investor Monthly Payment": m_inv,
        "Monthly Surplus": f"{(m_inst - m_inv):+,.0f}",
        "Total Investor Interest": investor_interest,
        "Total Surplus": f"{surplus:+,.0f}",
        "RenoSage Annual Profit ($)": annual_profit,
        "RenoSage Profit (%)": renosage_profit_margin_percentage(annual_profit, loan_amount)
    }
    return pd.DataFrame([results])

def generate_default_scenario(loan_amount, homeowner_term, investor_term, homeowner_rate, investor_rate,
                              contractor_profit_percentage, renosage_share):
    homeowner_interest = compound_interest(loan_amount, homeowner_rate, homeowner_term)
    investor_interest = simple_interest(loan_amount, investor_rate, investor_term)
    m_inst = monthly_installment_compound(loan_amount, homeowner_rate, homeowner_term)
    m_inv = monthly_investor_payout(investor_interest, investor_term)
    contractor_profit = round(loan_amount * (contractor_profit_percentage / 100), 2)
    renosage_share_profit = round(contractor_profit * (renosage_share / 100), 2)
    homeowner_interest_default = 0.75 * homeowner_interest
    m_inst_default = 0.75 * m_inst
    surplus_default = homeowner_investor_surplus(homeowner_interest_default, investor_interest)
    annual_profit_default = renosage_profit(homeowner_interest_default, renosage_share_profit, investor_interest)
    results_default = {
        "Loan (CAD $)": loan_amount,
        "Homeowner Term (Yrs)": homeowner_term,
        "Investor Term (Yrs)": investor_term,
        "Homeowner Rate": homeowner_rate,
        "Investor Rate": investor_rate,
        "Homeowner Monthly Installment": m_inst_default,
        "Investor Monthly Payment": m_inv,
        "Monthly Surplus": f"{(m_inst_default - m_inv):+,.0f}",
        "Total Investor Interest": investor_interest,
        "Total Surplus": f"{surplus_default:+,.0f}",
        "RenoSage Annual Profit ($)": annual_profit_default,
        "RenoSage Profit (%)": renosage_profit_margin_percentage(annual_profit_default, loan_amount)
    }
    return pd.DataFrame([results_default])

# ------------------------------------------------------------------
# 5. Cashflow Calculation (36 Months)
# ------------------------------------------------------------------

def calculate_cashflow_36_grouped(loan_amount, homeowner_rate, investor_rate,
                                  homeowner_term, investor_term,
                                  contractor_profit_percentage, renosage_share,
                                  default=False):
    investor_term_months = investor_term * 12
    homeowner_interest = compound_interest(loan_amount, homeowner_rate, homeowner_term)
    investor_interest = simple_interest(loan_amount, investor_rate, investor_term)
    m_inst = monthly_installment_compound(loan_amount, homeowner_rate, homeowner_term)
    if default:
        m_inst *= 0.75
    m_inv = monthly_investor_payout(investor_interest, investor_term)
    net_per_project = m_inst - m_inv

    running_total = 0
    lump_schedule = {}
    lump_events = []
    data = []

    for month in range(1, 37):
        fpn = get_projects_count(month)
        extra_profit = fpn * (renosage_share/100) * (contractor_profit_percentage/100) * loan_amount
        lump_month = month + investor_term_months
        if lump_month <= 36 and fpn > 0:
            lump_schedule[lump_month] = lump_schedule.get(lump_month, 0) + (fpn * loan_amount)
            lump_events.append({
                "event": "lump_schedule",
                "project_launch_month": month,
                "lump_month": lump_month,
                "amount": fpn * loan_amount
            })
        monthly_inflow = fpn * net_per_project + extra_profit
        running_total += monthly_inflow
        if month in lump_schedule:
            running_total -= lump_schedule[month]
            lump_events.append({
                "event": "lump_repayment",
                "month": month,
                "amount": lump_schedule[month]
            })
        opn = sum(get_projects_count(i) for i in range(1, month + 1))
        data.append({
            "Month": month,
            "Cashflow": running_total,
            "FPN": fpn,
            "OPN": opn
        })
    return pd.DataFrame(data), lump_events

def calculate_reinvestment_cashflow_36(loan_amount, homeowner_rate, investor_rate,
                                       homeowner_term, investor_term, boc_yield,
                                       reinvest_profit_percentage, reinvest_return_period,
                                       contractor_profit_percentage, renosage_share):
    investor_term_months = investor_term * 12
    homeowner_interest = compound_interest(loan_amount, homeowner_rate, homeowner_term)
    investor_interest = simple_interest(loan_amount, investor_rate, investor_term)
    m_inst = monthly_installment_compound(loan_amount, homeowner_rate, homeowner_term)
    m_inv = monthly_investor_payout(investor_interest, investor_term)
    net_per_project = m_inst - m_inv

    balance = 0
    lump_schedule = {}
    lump_events = []
    reinvest_list = []
    investment_queue = {}
    data = []

    for month in range(1, 37):
        if month in investment_queue:
            deposit_amount = investment_queue[month]
            balance += deposit_amount
            reinvest_list.append({
                "event": "reinvest_deposit",
                "month": month,
                "amount": deposit_amount
            })
            del investment_queue[month]
        fpn = get_projects_count(month)
        extra_profit = fpn * (renosage_share/100) * (contractor_profit_percentage/100) * loan_amount
        lump_month = month + investor_term_months
        if lump_month <= 36 and fpn > 0:
            lump_schedule[lump_month] = lump_schedule.get(lump_month, 0) + (fpn * loan_amount)
            lump_events.append({
                "event": "lump_schedule",
                "project_launch_month": month,
                "lump_month": lump_month,
                "amount": fpn * loan_amount
            })
        monthly_inflow = fpn * net_per_project + extra_profit
        balance += monthly_inflow
        if month in lump_schedule:
            balance -= lump_schedule[month]
            lump_events.append({
                "event": "lump_repayment",
                "month": month,
                "amount": lump_schedule[month]
            })
        if month < 34:
            multiples = int(balance // 15000)
            if multiples > 0:
                invest_amount = multiples * 15000
                balance -= invest_amount
                maturity_month = month + reinvest_return_period
                maturity_amount = invest_amount * (1 + reinvest_profit_percentage/100)
                reinvest_list.append({
                    "event": "reinvest_withdraw",
                    "month": month,
                    "amount": invest_amount,
                    "maturity_month": maturity_month,
                    "maturity_amount": maturity_amount
                })
                if maturity_month <= 36:
                    investment_queue[maturity_month] = investment_queue.get(maturity_month, 0) + maturity_amount
                else:
                    balance += maturity_amount
        opn = sum(get_projects_count(i) for i in range(1, month + 1))
        data.append({
            "Month": month,
            "Cashflow": balance,
            "FPN": fpn,
            "OPN": opn
        })

    all_events = {"lump": lump_events, "reinvest": reinvest_list}
    return pd.DataFrame(data), all_events

# ------------------------------------------------------------------
# 6b. Group Cashflow into Horizontal Format (3 rows x 4 columns per year)
# ------------------------------------------------------------------

def chunk_12_months_horizontally(df12, lumpset):
    """
    For a 12-month DataFrame (df12), returns a 3x4 DataFrame.
    Each cell is formatted as: "<Cashflow> (FPN: <FPN>, OPN: <OPN>)" with integer values.
    The month number is shown as [M: X] (with X in red if the month is in lumpset).
    """
    df12 = df12.sort_values("Month")
    lines = []
    for _, row in df12.iterrows():
        m = row["Month"]
        if m in lumpset:
            month_str = colored(str(m), "red")
        else:
            month_str = str(m)
        cell = f"{int(row['Cashflow']):,} (FPN: {int(row['FPN'])}, OPN: {int(row['OPN'])}) [M: {month_str}]"
        lines.append(cell)
    row1 = lines[0:4]
    row2 = lines[4:8]
    row3 = lines[8:12]
    start = df12["Month"].min()
    label1 = f"Months {start} - {start+3}"
    label2 = f"Months {start+4} - {start+7}"
    label3 = f"Months {start+8} - {start+11}"
    table = pd.DataFrame([row1, row2, row3],
                         index=[label1, label2, label3],
                         columns=["", "", "", ""])
    return table

def group_cashflow_by_year(df):
    """
    Splits a 36-month cashflow DataFrame into a dictionary with keys 1, 2, 3,
    each containing a 3x4 horizontal table for that year.
    """
    groups = {}
    for year in range(1, 4):
        start = (year - 1) * 12 + 1
        end = year * 12
        subset = df[(df["Month"] >= start) & (df["Month"] <= end)]
        # Determine lumpset for this subset (only include months that had lump repayments)
        lumpset = set(subset["Month"]).intersection({e["month"] for e in subset["Month"]})
        # Here, we pass lumpset from outside; for simplicity, we leave lumpset as the entire set for that subset.
        groups[year] = chunk_12_months_horizontally(subset, lumpset)
    return groups

# ------------------------------------------------------------------
# 7. Print Two Tables Side by Side (for Console Output)
# ------------------------------------------------------------------

def print_side_by_side(left_str, right_str, pad=4):
    lines1 = left_str.splitlines()
    lines2 = right_str.splitlines()
    max_lines = max(len(lines1), len(lines2))
    lines1 += [""] * (max_lines - len(lines1))
    lines2 += [""] * (max_lines - len(lines2))
    for l1, l2 in zip(lines1, lines2):
        print(l1.ljust(80 + pad) + l2)

# ------------------------------------------------------------------
# 8. Main Streamlit App
# ------------------------------------------------------------------

def main():
    st.title("Interactive Web Interface for RenoSage Financial Model")
    st.write("This dashboard enables investors to input parameters and view scenario-based cashflow projections. Homeowner interest is computed on a compound basis, while investor interest uses simple interest.")
    
    # Get inputs
    (loan_amount, homeowner_term, investor_term, homeowner_rate,
     investor_rate, contractor_profit_percentage, renosage_share, boc_yield,
     reinvest_profit_percentage, reinvest_return_period) = get_user_inputs()

    # Generate scenario tables
    df_base = generate_scenario(loan_amount, homeowner_term, investor_term, homeowner_rate, investor_rate,
                                contractor_profit_percentage, renosage_share)
    df_default = generate_default_scenario(loan_amount, homeowner_term, investor_term, homeowner_rate, investor_rate,
                                           contractor_profit_percentage, renosage_share)

    # Calculate cashflow for 36 months
    base_cf, base_lump_events = calculate_cashflow_36_grouped(loan_amount, homeowner_rate, investor_rate,
                                                              homeowner_term, investor_term,
                                                              contractor_profit_percentage, renosage_share,
                                                              default=False)
    default_cf, default_lump_events = calculate_cashflow_36_grouped(loan_amount, homeowner_rate, investor_rate,
                                                                    homeowner_term, investor_term,
                                                                    contractor_profit_percentage, renosage_share,
                                                                    default=True)
    reinvest_cf, all_events = calculate_reinvestment_cashflow_36(
        loan_amount, homeowner_rate, investor_rate, homeowner_term, investor_term, boc_yield,
        reinvest_profit_percentage, reinvest_return_period, contractor_profit_percentage, renosage_share
    )

    # Build lumpsets for coloring
    lumpset_base = {e["month"] for e in base_lump_events if e.get("event") == "lump_repayment"}
    lumpset_def = {e["month"] for e in default_lump_events if e.get("event") == "lump_repayment"}
    lumpset_reinv = {e["month"] for e in all_events["lump"] if e.get("event") == "lump_repayment"}

    # Split cashflow into yearly subsets
    base_y1 = base_cf[(base_cf["Month"] >= 1) & (base_cf["Month"] <= 12)]
    base_y2 = base_cf[(base_cf["Month"] >= 13) & (base_cf["Month"] <= 24)]
    base_y3 = base_cf[(base_cf["Month"] >= 25) & (base_cf["Month"] <= 36)]
    
    def_y1 = default_cf[(default_cf["Month"] >= 1) & (default_cf["Month"] <= 12)]
    def_y2 = default_cf[(default_cf["Month"] >= 13) & (default_cf["Month"] <= 24)]
    def_y3 = default_cf[(default_cf["Month"] >= 25) & (default_cf["Month"] <= 36)]
    
    re_y1 = reinvest_cf[(reinvest_cf["Month"] >= 1) & (reinvest_cf["Month"] <= 12)]
    re_y2 = reinvest_cf[(reinvest_cf["Month"] >= 13) & (reinvest_cf["Month"] <= 24)]
    re_y3 = reinvest_cf[(reinvest_cf["Month"] >= 25) & (reinvest_cf["Month"] <= 36)]
    
    df_base_y1 = chunk_12_months_horizontally(base_y1, lumpset_base)
    df_base_y2 = chunk_12_months_horizontally(base_y2, lumpset_base)
    df_base_y3 = chunk_12_months_horizontally(base_y3, lumpset_base)
    
    df_def_y1 = chunk_12_months_horizontally(def_y1, lumpset_def)
    df_def_y2 = chunk_12_months_horizontally(def_y2, lumpset_def)
    df_def_y3 = chunk_12_months_horizontally(def_y3, lumpset_def)
    
    df_re_y1 = chunk_12_months_horizontally(re_y1, lumpset_reinv)
    df_re_y2 = chunk_12_months_horizontally(re_y2, lumpset_reinv)
    df_re_y3 = chunk_12_months_horizontally(re_y3, lumpset_reinv)
    
    # Display in tabs
    tab1, tab2, tab3 = st.tabs(["Base Scenario", "Default Scenario", "Reinvestment Scenario"])
    
    with tab1:
        st.subheader("Base Scenario Calculations")
        st.dataframe(df_base)
        st.markdown("### Cashflow Calculations for Base Scenario (3-Year Term)")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**First Year**")
            st.dataframe(df_base_y1)
        with col2:
            st.markdown("**Second Year**")
            st.dataframe(df_base_y2)
        with col3:
            st.markdown("**Third Year**")
            st.dataframe(df_base_y3)
        st.plotly_chart(px.line(base_cf, x="Month", y="Cashflow", title="Base Cashflow Over 36 Months"))
    
    with tab2:
        st.subheader("Default Scenario Calculations")
        st.dataframe(df_default)
        st.markdown("### Cashflow Calculations for Default Scenario (3-Year Term)")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**First Year**")
            st.dataframe(df_def_y1)
        with col2:
            st.markdown("**Second Year**")
            st.dataframe(df_def_y2)
        with col3:
            st.markdown("**Third Year**")
            st.dataframe(df_def_y3)
        st.plotly_chart(px.line(default_cf, x="Month", y="Cashflow", title="Default Cashflow Over 36 Months"))
    
    with tab3:
        st.subheader("Reinvestment Loop Scenario")
        st.markdown("### Cashflow Calculations for Reinvestment Scenario (3-Year Term)")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**First Year**")
            st.dataframe(df_re_y1)
        with col2:
            st.markdown("**Second Year**")
            st.dataframe(df_re_y2)
        with col3:
            st.markdown("**Third Year**")
            st.dataframe(df_re_y3)
        st.plotly_chart(px.line(reinvest_cf, x="Month", y="Cashflow", title="Reinvestment Cashflow Over 36 Months"))
        
        st.markdown("#### Event Logs")
        def format_lump_events_html(events):
            html = ""
            if not events:
                return "No lump-sum repayment events in this period."
            for idx, event in enumerate(events, 1):
                if event.get("event") == "lump_schedule":
                    html += f"<p>Event {idx} (Lump-Schedule): Projects launched in month {event['project_launch_month']} → lump repayment of ${int(event['amount']):,} in month <span style='color:red;'>{event['lump_month']}</span>.</p>"
                elif event.get("event") == "lump_repayment":
                    html += f"<p>Event {idx} (Lump-Repayment): In month {event['month']}, a lump-sum of ${int(event['amount']):,} was repaid.</p>"
            return html

        def format_reinvest_events_html(events):
            html = ""
            if not events:
                return "No reinvestment events in this period."
            for idx, event in enumerate(all_events["reinvest"], 1):
                if event.get("event") == "reinvest_withdraw":
                    html += f"<p style='color:red;'>Event {idx} (Reinvest-Withdraw): In month {event['month']}, ${int(event['amount']):,} was withdrawn for reinvestment (matures in month {event['maturity_month']} → ${int(event['maturity_amount']):,}).</p>"
                elif event.get("event") == "reinvest_deposit":
                    html += f"<p style='color:green;'>Event {idx} (Reinvest-Deposit): In month {event['month']}, a reinvestment matured, depositing ${int(event['amount']):,}.</p>"
            return html

        lump_html = format_lump_events_html(all_events["lump"])
        reinvest_html = format_reinvest_events_html(all_events["reinvest"])
        st.markdown(lump_html, unsafe_allow_html=True)
        st.markdown(reinvest_html, unsafe_allow_html=True)
        st.markdown("<p>Note: For each project, after the Interest Distribution Term ends, an amount equal to the loan is distributed to investors in a lump sum.</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
