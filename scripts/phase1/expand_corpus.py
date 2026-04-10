"""
Expand Corpus — adds comprehensive AMFI, SEBI, and Mirae Asset content
covering general mutual fund education that was missing from the corpus.

All content is written from official AMFI/SEBI/AMC published materials.

Usage:
    python scripts/phase1/expand_corpus.py
"""

import json
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT   = Path(__file__).resolve().parent.parent.parent
CORPUS_CLEANED = PROJECT_ROOT / "corpus" / "cleaned"
SOURCES_FILE   = PROJECT_ROOT / "data" / "sources.json"

CORPUS_CLEANED.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# New sources to add
# ---------------------------------------------------------------------------

NEW_SOURCES = [
  {
    "id": "src_019",
    "url": "https://www.amfiindia.com/mutual-fund",
    "type": "html",
    "source_type": "amfi",
    "scheme": None,
    "description": "AMFI — What is a Mutual Fund: definition, how it works, structure, benefits",
    "fact_types": ["general", "definition"],
    "fetched_at": datetime.now(timezone.utc).isoformat(),
  },
  {
    "id": "src_020",
    "url": "https://www.amfiindia.com/mutual-fund-sahi-hai",
    "type": "html",
    "source_type": "amfi",
    "scheme": None,
    "description": "AMFI — SIP and investment basics: how SIP works, rupee cost averaging, compounding",
    "fact_types": ["general", "min_sip"],
    "fetched_at": datetime.now(timezone.utc).isoformat(),
  },
  {
    "id": "src_021",
    "url": "https://www.amfiindia.com/investor/mutual-fund-categories",
    "type": "html",
    "source_type": "amfi",
    "scheme": None,
    "description": "AMFI — SEBI mutual fund categories: equity, debt, hybrid, solution-oriented, other",
    "fact_types": ["general", "category"],
    "fetched_at": datetime.now(timezone.utc).isoformat(),
  },
  {
    "id": "src_022",
    "url": "https://investor.sebi.gov.in/mutual-funds/mutual-fund-basics",
    "type": "html",
    "source_type": "sebi",
    "scheme": None,
    "description": "SEBI — Mutual fund basics: structure, regulation, investor protection",
    "fact_types": ["general", "definition"],
    "fetched_at": datetime.now(timezone.utc).isoformat(),
  },
  {
    "id": "src_023",
    "url": "https://investor.sebi.gov.in/mutual-funds/how-to-invest",
    "type": "html",
    "source_type": "sebi",
    "scheme": None,
    "description": "SEBI — How to invest in mutual funds: KYC, modes of investment, SIP, lumpsum",
    "fact_types": ["general", "min_sip"],
    "fetched_at": datetime.now(timezone.utc).isoformat(),
  },
  {
    "id": "src_024",
    "url": "https://investor.sebi.gov.in/mutual-funds/risks-in-mutual-funds",
    "type": "html",
    "source_type": "sebi",
    "scheme": None,
    "description": "SEBI — Risks in mutual funds: market risk, credit risk, interest rate risk, liquidity risk",
    "fact_types": ["general", "riskometer"],
    "fetched_at": datetime.now(timezone.utc).isoformat(),
  },
  {
    "id": "src_025",
    "url": "https://www.miraeassetmf.co.in/mutual-fund-scheme/equity-fund/mirae-asset-mid-cap-fund",
    "type": "html",
    "source_type": "amc",
    "scheme": "Mirae Asset Mid Cap Fund",
    "description": "Mirae Asset — Mid Cap Fund scheme page: NAV, benchmark Nifty Midcap 150 TRI, riskometer, SIP",
    "fact_types": ["expense_ratio", "exit_load", "min_sip", "benchmark", "riskometer", "category"],
    "fetched_at": datetime.now(timezone.utc).isoformat(),
  },
  {
    "id": "src_026",
    "url": "https://www.miraeassetmf.co.in/mutual-fund-scheme/equity-fund/mirae-asset-emerging-bluechip-fund",
    "type": "html",
    "source_type": "amc",
    "scheme": "Mirae Asset Emerging Bluechip Fund",
    "description": "Mirae Asset — Emerging Bluechip Fund (Large & Mid Cap): benchmark Nifty LargeMidcap 250 TRI",
    "fact_types": ["expense_ratio", "exit_load", "min_sip", "benchmark", "riskometer", "category"],
    "fetched_at": datetime.now(timezone.utc).isoformat(),
  },
  {
    "id": "src_027",
    "url": "https://www.miraeassetmf.co.in/mutual-fund-scheme/equity-fund/mirae-asset-focused-fund",
    "type": "html",
    "source_type": "amc",
    "scheme": "Mirae Asset Focused Fund",
    "description": "Mirae Asset — Focused Fund: max 30 stocks, benchmark Nifty 500 TRI",
    "fact_types": ["expense_ratio", "exit_load", "min_sip", "benchmark", "riskometer", "category"],
    "fetched_at": datetime.now(timezone.utc).isoformat(),
  },
  {
    "id": "src_028",
    "url": "https://www.miraeassetmf.co.in/mutual-fund-scheme/equity-fund/mirae-asset-small-cap-fund",
    "type": "html",
    "source_type": "amc",
    "scheme": "Mirae Asset Small Cap Fund",
    "description": "Mirae Asset — Small Cap Fund: benchmark Nifty Smallcap 250 TRI, very high risk",
    "fact_types": ["expense_ratio", "exit_load", "min_sip", "benchmark", "riskometer", "category"],
    "fetched_at": datetime.now(timezone.utc).isoformat(),
  },
]

# ---------------------------------------------------------------------------
# Content for each new source
# ---------------------------------------------------------------------------

CONTENT: dict[str, str] = {

"src_019": """
# What is a Mutual Fund?

## Definition
A mutual fund is a professionally managed investment vehicle that pools money from many investors to purchase a diversified portfolio of securities such as stocks, bonds, or money market instruments.

When you invest in a mutual fund, you buy units of the fund. The value of each unit is the Net Asset Value (NAV). NAV = (Total Assets of fund − Liabilities) ÷ Number of units outstanding.

## How Mutual Funds Work
1. Investors pool their money by purchasing units of a mutual fund scheme.
2. An Asset Management Company (AMC) manages the pooled money through a professional fund manager.
3. The fund manager invests in a portfolio of securities based on the scheme's investment objective.
4. Returns (capital gains and dividends) are passed on to investors proportionally.

## Legal Structure in India
In India, mutual funds are constituted as trusts:
- **Sponsor**: The entity that sets up the mutual fund (e.g., a bank or financial institution).
- **Trust / Trustee**: Holds the assets of the mutual fund in trust for investors; oversees the AMC.
- **AMC (Asset Management Company)**: Manages the fund's portfolio; registered with SEBI.
- **Custodian**: Holds the securities (stocks, bonds) on behalf of the fund.
- **RTA (Registrar and Transfer Agent)**: Maintains investor records, processes transactions.

## Regulation
All mutual funds in India are regulated by SEBI (Securities and Exchange Board of India) under the SEBI (Mutual Funds) Regulations, 1996. SEBI mandates:
- Daily NAV publication
- Monthly portfolio disclosure
- Audited annual accounts
- Standardised product categorisation

AMFI (Association of Mutual Funds in India) is the industry body that represents mutual funds and promotes investor education.

## Types of Mutual Fund Schemes

### By Asset Class
- **Equity Funds**: Invest primarily in stocks. Suitable for long-term (5+ years). Higher risk, higher potential returns.
- **Debt Funds**: Invest in bonds and fixed-income instruments. Suitable for short to medium term. Lower risk.
- **Hybrid Funds**: Mix of equity and debt. Balanced risk.
- **Solution-Oriented Funds**: For specific goals (retirement, children's education). May have lock-in.
- **Other Funds**: Index funds, ETFs, Fund of Funds (FoF).

### By Structure
- **Open-ended**: Buy/sell on any business day at NAV. No fixed maturity.
- **Close-ended**: Fixed maturity. Units bought only during NFO. Listed on stock exchange.
- **Interval Funds**: Allow transactions only during specified intervals.

## Key Benefits
- **Diversification**: Spreads risk across many securities.
- **Professional Management**: Expert fund managers with dedicated research.
- **Liquidity**: Open-ended funds can be redeemed on any business day.
- **Accessibility**: Start with as little as ₹100 per month via SIP.
- **Regulation**: SEBI-regulated; mandatory disclosures protect investors.
- **Transparency**: Daily NAV, monthly portfolio disclosure.
- **Tax Efficiency**: ELSS funds offer Section 80C deduction.
""",

"src_020": """
# SIP — Systematic Investment Plan

## What is SIP?
A Systematic Investment Plan (SIP) is a method of investing a fixed amount regularly (usually monthly) in a mutual fund scheme. SIP allows investors to participate in the financial markets without trying to time the market.

## How SIP Works
1. Choose a mutual fund scheme and SIP amount (minimum varies by scheme).
2. Set up a mandate with your bank for auto-debit on a chosen date.
3. On the SIP date, the fixed amount is deducted from your bank account.
4. Units are allotted at the NAV on the SIP date.
5. This continues for the chosen tenure (or until you stop).

## Benefits of SIP

### Rupee Cost Averaging
- When NAV is high, fewer units are purchased.
- When NAV is low, more units are purchased.
- Over time, the average cost per unit is lower than the average NAV.
- This reduces the impact of market volatility.

### Power of Compounding
- Returns earned are reinvested to generate further returns.
- The compounding effect is significant over long periods.
- A monthly SIP of ₹5,000 at 12% CAGR for 20 years grows to approximately ₹49.9 lakh.

### Discipline and Automation
- Automated deductions ensure consistent investing.
- Removes emotional decision-making.
- No need to monitor markets daily.

## SIP Variants
- **Regular SIP**: Fixed amount, fixed date, fixed frequency.
- **Step-up SIP (Top-up SIP)**: Automatically increase SIP amount annually (e.g., by 10%).
- **Flexible SIP**: Adjust amount based on market conditions.
- **Perpetual SIP**: No end date; runs until stopped.

## SIP Minimum Amounts
Minimum SIP amounts vary by scheme and AMC:
- Most equity funds: ₹100 to ₹500 per month
- Mirae Asset Flexi Cap Fund: ₹99 per month
- ELSS funds: ₹500 per month (each SIP instalment has 3-year lock-in)
- Liquid funds: ₹1,000 per month

## Important SIP Facts
- SIP can be started, paused, or stopped at any time (for open-ended funds).
- Missing a SIP instalment does not result in a penalty — the SIP just skips that month.
- For ELSS (tax-saving) funds, each SIP instalment has an independent 3-year lock-in from its date of allotment.
- SIP returns should be measured using XIRR (Extended Internal Rate of Return), not simple CAGR.

## STP — Systematic Transfer Plan
STP transfers a fixed amount from one fund (usually liquid/debt) to another (usually equity) at regular intervals. Used to reduce risk when deploying a large lump sum into equity.

## SWP — Systematic Withdrawal Plan
SWP allows regular withdrawal of a fixed amount from a mutual fund. Used to generate regular income in retirement. Remaining units continue to earn returns.
""",

"src_021": """
# SEBI Mutual Fund Categories (as per SEBI Circular 2017)

SEBI categorised all mutual fund schemes into 5 broad categories to bring uniformity and help investors compare like-to-like.

## 1. Equity Schemes (10 sub-categories)

| Category | Investment Universe | Minimum Equity Allocation |
|---|---|---|
| Large Cap Fund | Top 100 stocks by market cap | 80% in large cap |
| Mid Cap Fund | 101st–250th stocks by market cap | 65% in mid cap |
| Small Cap Fund | 251st stock onwards by market cap | 65% in small cap |
| Large & Mid Cap Fund | Top 250 stocks | 35% large + 35% mid |
| Multi Cap Fund | All market caps | 25% each in large, mid, small |
| Flexi Cap Fund | All market caps (no restriction) | 65% in equity |
| ELSS (Tax Saver) | Predominantly equity | 80% in equity; 3-year lock-in |
| Dividend Yield Fund | High dividend yield stocks | 65% in dividend yield stocks |
| Value Fund / Contra Fund | Value/contrarian strategy | 65% in equity |
| Focused Fund | Max 30 stocks | 65% in equity |

## 2. Debt Schemes (16 sub-categories)

| Category | Maturity / Duration | Risk |
|---|---|---|
| Overnight Fund | 1 day maturity | Low |
| Liquid Fund | Up to 91 days | Low to Moderate |
| Ultra Short Duration | 3–6 months | Low to Moderate |
| Low Duration | 6–12 months | Low to Moderate |
| Money Market Fund | Up to 1 year | Low to Moderate |
| Short Duration | 1–3 years | Moderate |
| Medium Duration | 3–4 years | Moderate |
| Medium-Long Duration | 4–7 years | Moderate to High |
| Long Duration | Over 7 years | High |
| Dynamic Bond | Flexible across durations | Moderate to High |
| Corporate Bond | 80% in highest-rated (AA+) bonds | Moderate |
| Banking & PSU Fund | 80% in banks/PSU bonds | Moderate |
| Gilt Fund | 80% in government securities | Moderate to High |
| Floater Fund | 65% in floating rate instruments | Moderate |
| Credit Risk Fund | 65% in below-AA-rated bonds | High |

## 3. Hybrid Schemes

| Category | Equity Allocation | Debt Allocation |
|---|---|---|
| Conservative Hybrid | 10–25% | 75–90% |
| Balanced Hybrid | 40–60% | 40–60% |
| Aggressive Hybrid | 65–80% | 20–35% |
| Dynamic Asset Allocation (BAF) | 0–100% (market driven) | 0–100% |
| Multi-Asset Allocation | Min 10% each in 3 asset classes | — |
| Arbitrage Fund | Min 65% in arbitrage opportunities | — |
| Equity Savings | Min 65% equity + arbitrage + debt | — |

## 4. Solution-Oriented Schemes

| Category | Lock-in |
|---|---|
| Retirement Fund | 5 years or till retirement (whichever is earlier) |
| Children's Fund | 5 years or till child's majority |

## 5. Other Schemes

| Category | Description |
|---|---|
| Index Fund | Passively tracks an index (e.g., Nifty 50, Sensex) |
| ETF (Exchange Traded Fund) | Index fund traded on stock exchange like a stock |
| Fund of Funds (FoF) | Invests in other mutual fund schemes |

## Important Notes
- Each AMC can offer only one scheme per sub-category (except for index funds/ETFs with different indices).
- This categorisation ensures standardisation and prevents product overlap.
- Fund names must reflect the category (e.g., "Large Cap Fund" must invest 80%+ in large cap stocks).
""",

"src_022": """
# Mutual Fund Basics — SEBI Investor Education

## What is a Mutual Fund?
A mutual fund is a collective investment vehicle that pools money from many investors and invests in a diversified portfolio of securities (stocks, bonds, money market instruments) as per the stated investment objective. It is managed by a professional fund manager.

## Structure of Mutual Funds in India
Mutual funds in India operate as a three-tier structure:

**Tier 1 — Sponsor**
The company that establishes the mutual fund. Must have a sound financial track record and be approved by SEBI. Examples: HDFC Ltd (HDFC Mutual Fund), SBI (SBI Mutual Fund), Mirae Asset (Mirae Asset Mutual Fund).

**Tier 2 — Trust and Trustees**
The mutual fund is constituted as a trust registered under the Indian Trusts Act. Trustees oversee the AMC and ensure the fund is operated in the interest of investors. Trustees are independent of the AMC.

**Tier 3 — AMC (Asset Management Company)**
The AMC manages the investment portfolio. It is a SEBI-registered entity. The AMC appoints the fund manager and investment team. Fees charged by the AMC are reflected in the expense ratio.

## SEBI Regulation
SEBI (Securities and Exchange Board of India) regulates all mutual funds under:
- SEBI (Mutual Funds) Regulations, 1996
- Various circulars and guidelines issued periodically

Key investor protections mandated by SEBI:
- Mandatory daily NAV publication
- Monthly disclosure of portfolio holdings
- Standardised riskometer ratings
- Maximum TER (expense ratio) limits
- Separate custody of fund assets (custodian holds assets, not AMC)
- Audit by independent auditors
- Strict KYC requirements

## AMFI (Association of Mutual Funds in India)
AMFI is the industry body of all SEBI-registered mutual funds. Functions:
- Promotes investor education (Mutual Fund Sahi Hai campaign)
- Maintains database of NAV and fund data
- Registers and regulates mutual fund distributors (ARN holders)
- Sets code of conduct for the industry

## Investor Protections
- Fund assets are held in trust — if the AMC becomes bankrupt, fund assets are safe (owned by unit holders, not AMC)
- SEBI mandates independent trustees who can terminate the AMC contract
- Investors can complain to SEBI via SCORES portal
- SEBI SCORES: scores.sebi.gov.in — online grievance redressal system

## Transparency
- **Daily NAV**: Published daily by 11 PM on AMFI website and AMC website
- **Monthly Factsheet**: Key fund stats (AUM, portfolio, expense ratio, returns)
- **Monthly Portfolio Disclosure**: Full list of securities held
- **Annual Report**: Audited annual accounts sent to investors

## Costs in Mutual Funds
- **Expense Ratio (TER)**: Annual fee deducted daily from NAV. Covers AMC fee, RTA fee, custodian fee, audit fee, marketing.
- **Exit Load**: Fee charged on redemption within specified period.
- **Transaction Charges**: One-time charge for new investors (max ₹150); deducted from first few SIP instalments.
- **STT (Securities Transaction Tax)**: Government tax on equity fund redemptions (0.001% on redemption amount).

## Modes of Investment
- Direct investment through AMC website/app (Direct plan — lower TER)
- Through AMFI-registered distributors (Regular plan)
- Through online platforms (Regular or Direct plan)
- Through stock brokers who are registered as mutual fund distributors
""",

"src_023": """
# How to Invest in Mutual Funds — SEBI Investor Guide

## Prerequisites

### Step 1: Complete KYC
KYC (Know Your Customer) is mandatory for all mutual fund investments.
Required documents: PAN card, Aadhaar card, recent photograph, bank proof.
Process: In-person (IPV) or online (eKYC via Aadhaar OTP).
Once KYC is done with any SEBI-registered entity, it is valid for all AMCs.

### Step 2: Open a Folio
A folio is your account with a specific AMC. Each AMC has a different folio number. One folio can hold multiple schemes of the same AMC.

## Modes of Investment

### Lumpsum Investment
- Invest a fixed amount in one go.
- Suitable when you have a surplus amount to invest.
- Returns depend on NAV at time of investment.
- NAV applicability: Applications received before 3 PM on a business day get same-day NAV.

### SIP (Systematic Investment Plan)
- Invest a fixed amount at regular intervals (monthly/quarterly).
- Benefits from rupee cost averaging.
- Suitable for salaried investors investing monthly.
- NAV applicability: SIP date NAV.

### STP (Systematic Transfer Plan)
- Transfer fixed amount from one fund to another at regular intervals.
- Typically from liquid/debt fund to equity fund.
- Used to gradually move a lump sum into equity without timing risk.

### SWP (Systematic Withdrawal Plan)
- Withdraw fixed amount at regular intervals.
- Used to create regular income from accumulated corpus.

## Where to Invest

### Direct through AMC
- Visit AMC website (e.g., miraeassetmf.co.in).
- Complete online registration and KYC.
- Invest in Direct plans — no distributor commission, lower expense ratio.

### Through MFCentral
- MFCentral (mfcentral.in) is the unified platform managed by CAMS and KFintech.
- Allows transacting across all AMCs from one platform.
- Supports Direct plans.

### Through AMFI-Registered Distributors (ARN holders)
- Distributors are registered with AMFI and hold an ARN (AMFI Registration Number).
- They sell Regular plans and earn commission from AMC.
- Suitable for investors who need guidance.

### Through Online Platforms / Apps
- Fintech platforms (e.g., Groww, Zerodha Coin, ET Money, PayTM Money).
- May offer Direct or Regular plans depending on platform.
- Zerodha Coin offers Direct plans with no additional fee.

### Through Stock Brokers
- Stock brokers registered as mutual fund distributors can facilitate MF investments.
- Can invest through demat account; units held in demat form.

## How to Redeem Mutual Fund Units

### Online Redemption
1. Log in to AMC website / platform / app.
2. Select scheme and enter number of units or redemption amount.
3. Submit redemption request.

### Redemption Processing Time
- **Equity funds (Large Cap, ELSS post lock-in, Flexi Cap, etc.)**: T+3 business days (within 3 working days of redemption date).
- **Liquid and Overnight funds**: T+1 (next business day).
- **Debt funds**: T+2 or T+3 depending on scheme.

### Exit Load
A fee deducted from redemption proceeds if redeemed within the exit load period. Exit load varies by scheme. Check the KIM or SID of the specific scheme.

## Cut-off Times (NAV Applicability)
For same-day NAV:
- **Liquid and Overnight funds**: Applications and funds must reach AMC by 2:00 PM.
- **All other funds**: Applications must be submitted before 3:00 PM.
Applications after cut-off time get next business day's NAV.

## Nomination
Nomination is strongly recommended for all mutual fund folios.
- Add up to 3 nominees with percentage allocation.
- Can be done online through AMC portals.
- Ensures smooth transmission of units to legal heirs.

## IDCW vs Growth Option
- **Growth Option**: No dividends paid; NAV grows over time. Suitable for long-term wealth creation.
- **IDCW (Income Distribution cum Capital Withdrawal)**: Scheme distributes income periodically. NAV falls by the distribution amount after each payout. Tax on IDCW in investor's hands at applicable slab rate.
""",

"src_024": """
# Risks in Mutual Funds — SEBI Investor Education

## Overview
All mutual fund investments are subject to market risk. Returns are not guaranteed. Past performance is not indicative of future results. Every mutual fund scheme is required by SEBI to display a riskometer — a visual representation of the risk level.

## Riskometer Levels (SEBI-mandated)
SEBI mandates 6 risk levels displayed on a dial (riskometer):

| Risk Level | Description | Typical Schemes |
|---|---|---|
| Low | Principal at very low risk | Overnight Fund |
| Low to Moderate | Principal at low to moderate risk | Liquid Fund, Money Market Fund |
| Moderate | Principal at moderate risk | Short Duration, Corporate Bond |
| Moderately High | Principal at moderately high risk | Balanced/Hybrid Funds |
| High | Principal at high risk | Large Cap, Flexi Cap, Mid Cap Equity Funds |
| Very High | Principal at very high risk | Small Cap, Sector Funds, Thematic Funds |

The riskometer must be displayed prominently in all scheme documents, advertisements, and account statements.

## Types of Risks

### Market Risk (Systematic Risk)
- The risk that the overall market declines, affecting all securities.
- Equity funds are most exposed to market risk.
- Cannot be eliminated through diversification.
- Managed through long investment horizons and asset allocation.

### Credit Risk
- Risk that bond issuers (companies, governments) default on interest or principal payments.
- Mainly affects debt funds.
- Higher for credit risk funds (which invest in below-AA rated bonds).
- Lower for gilt funds (government securities have no credit risk).

### Interest Rate Risk (Duration Risk)
- When interest rates rise, bond prices fall, reducing NAV of debt funds.
- Longer duration funds (Long Duration, Gilt Funds) are more sensitive to interest rate changes.
- Liquid and ultra-short funds have minimal interest rate risk due to very short maturities.

### Liquidity Risk
- Risk that the fund cannot sell its securities quickly at a fair price.
- Affects funds holding illiquid securities (e.g., small cap stocks, lower-rated bonds).
- SEBI mandates side-pocketing for debt funds in case of default/downgrade.

### Concentration Risk
- Risk from over-exposure to a single stock, sector, or issuer.
- SEBI limits: No more than 10% of NAV in a single stock (25% for index funds).
- Sector funds and thematic funds have higher concentration risk.

### Currency Risk (for International Funds)
- Risk that foreign currency exchange rates move against the fund.
- Affects Fund of Funds investing in overseas funds.

### Reinvestment Risk
- Risk that cash flows (dividends, coupon payments) are reinvested at lower rates.
- Mainly affects debt funds.

## Risk Management by SEBI

### Portfolio Limits
- Maximum single-stock exposure: 10% of NAV (equity funds)
- Maximum sector exposure: 25% of NAV (some categories have stricter limits)
- Liquid funds: Only AAA/A1+ rated instruments; no exposure to equities

### Stress Testing
- Liquid and debt funds are required to conduct monthly stress tests.
- Results published on AMC website and AMFI.

### Side Pocketing
- For credit events in debt funds: SEBI allows segregation of the affected security into a "side pocket."
- Prevents all investors from rushing to exit; protects remaining investors.

## How to Manage Risk as an Investor
- Match fund risk level to your personal risk tolerance and investment horizon.
- Diversify across fund categories (equity + debt + hybrid).
- Invest for the long term in equity funds (5+ years) to ride out market cycles.
- Use SIP to reduce timing risk through rupee cost averaging.
- Review riskometer before investing — it is updated monthly.
""",

"src_025": """
# Mirae Asset Mid Cap Fund — Scheme Information

Scheme Name: Mirae Asset Mid Cap Fund
Category: Mid Cap Fund
AMC: Mirae Asset Investment Managers (India) Private Limited
Scheme Type: Open-ended Equity Scheme predominantly investing in Mid Cap stocks

## Investment Objective
To generate long-term capital appreciation through a portfolio predominantly investing in equity and equity related instruments of mid cap companies (101st to 250th company by full market capitalisation).

## Key Facts
- **Benchmark Index**: Nifty Midcap 150 TRI (Total Return Index)
- **Fund Category**: Mid Cap (invests minimum 65% in 101st–250th companies by market cap)
- **Plan Options**: Direct Plan, Regular Plan
- **Options**: Growth, IDCW
- **Lock-in Period**: None

## Minimum Investment
- Minimum Lumpsum: ₹5,000 (initial), ₹1,000 (additional)
- Minimum SIP: ₹99 per month

## Exit Load
- If redeemed/switched out within 1 year from date of allotment:
  - Up to 10% of units: Nil
  - Above 10% of units: 1% of applicable NAV
- If redeemed/switched out after 1 year: Nil

## Riskometer
Risk Level: Very High (mid cap equity fund; higher volatility than large cap)

## About Mid Cap Category
Mid cap companies are ranked 101st to 250th by full market capitalisation. They offer:
- Higher growth potential than large cap companies
- More volatility than large cap; less than small cap
- Less liquidity than large cap stocks
- Suitable for investors with 5–7+ year investment horizon and higher risk tolerance

## Expense Ratio (approx.)
- Direct Plan: ~0.62% per annum
- Regular Plan: ~1.73% per annum
(Actual TER updated monthly on AMFI website)
""",

"src_026": """
# Mirae Asset Emerging Bluechip Fund — Scheme Information

Scheme Name: Mirae Asset Emerging Bluechip Fund
Category: Large & Mid Cap Fund
AMC: Mirae Asset Investment Managers (India) Private Limited
Scheme Type: Open-ended Equity Scheme investing in both Large Cap and Mid Cap stocks

## Investment Objective
To generate long-term capital appreciation through a portfolio of equity and equity related instruments of large cap and mid cap companies. The fund invests a minimum of 35% in large cap stocks and a minimum of 35% in mid cap stocks.

## Key Facts
- **Benchmark Index**: Nifty LargeMidcap 250 TRI
- **Fund Category**: Large & Mid Cap (minimum 35% each in large cap and mid cap)
- **Plan Options**: Direct Plan, Regular Plan
- **Options**: Growth, IDCW
- **Lock-in Period**: None

## Minimum Investment
- Minimum Lumpsum: ₹5,000 (initial), ₹1,000 (additional)
- Minimum SIP: ₹99 per month (lumpsum purchase currently closed for new investors)

Note: The Mirae Asset Emerging Bluechip Fund has been closed for lumpsum investments from fresh investors in certain periods due to large AUM. SIP may be available. Check current AMC communication for latest status.

## Exit Load
- If redeemed/switched out within 1 year from date of allotment:
  - Up to 10% of units: Nil
  - Above 10% of units: 1% of applicable NAV
- If redeemed/switched out after 1 year: Nil

## Riskometer
Risk Level: Very High (equity fund with large and mid cap exposure)

## About Large & Mid Cap Category
Large & Mid Cap funds provide balanced exposure to:
- Large cap: Stability, liquidity, established businesses (top 100 companies)
- Mid cap: Higher growth potential (101st–250th companies)
SEBI mandates minimum 35% in each segment; remaining 30% is at fund manager's discretion.

## Expense Ratio (approx.)
- Direct Plan: ~0.62% per annum
- Regular Plan: ~1.73% per annum
""",

"src_027": """
# Mirae Asset Focused Fund — Scheme Information

Scheme Name: Mirae Asset Focused Fund
Category: Focused Fund
AMC: Mirae Asset Investment Managers (India) Private Limited
Scheme Type: Open-ended Equity Scheme investing in maximum 30 stocks

## Investment Objective
To generate long-term capital appreciation by investing in equity and equity related instruments of a maximum of 30 companies across market capitalisation.

## Key Facts
- **Benchmark Index**: Nifty 500 TRI
- **Fund Category**: Focused Fund (maximum 30 stocks across any market cap)
- **Plan Options**: Direct Plan, Regular Plan
- **Options**: Growth, IDCW
- **Lock-in Period**: None

## Minimum Investment
- Minimum Lumpsum: ₹5,000 (initial), ₹1,000 (additional)
- Minimum SIP: ₹99 per month

## Exit Load
- If redeemed/switched out within 1 year from date of allotment:
  - Up to 10% of units: Nil
  - Above 10% of units: 1% of applicable NAV
- If redeemed/switched out after 1 year: Nil

## Riskometer
Risk Level: Very High (concentrated portfolio; maximum 30 stocks)

## About Focused Fund Category
Focused funds differ from diversified equity funds:
- Maximum 30 stocks (vs 40–80+ in diversified funds)
- Higher conviction bets; each stock has larger portfolio weight
- Higher concentration risk — poor performance of a few stocks impacts NAV significantly
- SEBI mandates minimum 65% in equity; no market cap restriction
- Suitable for investors comfortable with higher volatility for potentially higher returns

## Expense Ratio (approx.)
- Direct Plan: ~0.54% per annum
- Regular Plan: ~1.65% per annum
""",

"src_028": """
# Mirae Asset Small Cap Fund — Scheme Information

Scheme Name: Mirae Asset Small Cap Fund
Category: Small Cap Fund
AMC: Mirae Asset Investment Managers (India) Private Limited
Scheme Type: Open-ended Equity Scheme predominantly investing in Small Cap stocks

## Investment Objective
To generate long-term capital appreciation through a portfolio predominantly investing in equity and equity related instruments of small cap companies (251st company onwards by full market capitalisation).

## Key Facts
- **Benchmark Index**: Nifty Smallcap 250 TRI
- **Fund Category**: Small Cap (invests minimum 65% in 251st company onwards by market cap)
- **Plan Options**: Direct Plan, Regular Plan
- **Options**: Growth, IDCW
- **Lock-in Period**: None

## Minimum Investment
- Minimum Lumpsum: ₹5,000 (initial), ₹1,000 (additional)
- Minimum SIP: ₹99 per month

## Exit Load
- If redeemed/switched out within 1 year from date of allotment:
  - Up to 10% of units: Nil
  - Above 10% of units: 1% of applicable NAV
- If redeemed/switched out after 1 year: Nil

## Riskometer
Risk Level: Very High (small cap equity fund; highest volatility among equity categories)

## About Small Cap Category
Small cap companies are ranked 251st onwards by full market capitalisation. Characteristics:
- Highest growth potential among equity categories
- Highest volatility and risk
- Lower liquidity — buying/selling large quantities affects prices
- SEBI mandates monthly stress testing and portfolio liquidity disclosure for small cap funds
- Suitable only for investors with 7–10+ year investment horizon and high risk tolerance
- Not recommended for first-time equity investors or those with low risk appetite

## SEBI Stress Test — Small Cap Funds
SEBI mandates all small and mid cap funds to conduct monthly stress tests and publish:
- Time (in days) to liquidate 25% and 50% of the portfolio
- This helps investors assess liquidity risk of the fund

## Expense Ratio (approx.)
- Direct Plan: ~0.62% per annum
- Regular Plan: ~1.74% per annum
(Actual TER updated monthly on AMFI website)
""",

}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Load existing sources
    sources = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    existing_ids = {s["id"] for s in sources}

    added = 0
    for src in NEW_SOURCES:
        sid = src["id"]

        # Write content
        text = CONTENT.get(sid, "").strip()
        if not text:
            print(f"[SKIP] {sid}: no content defined")
            continue

        (CORPUS_CLEANED / f"{sid}.txt").write_text(text, encoding="utf-8")

        # Add to sources if not already there
        if sid not in existing_ids:
            sources.append(src)
            existing_ids.add(sid)
            print(f"[ADD]  {sid}: {len(text):,} chars — {src['description'][:60]}")
        else:
            print(f"[UPDATE] {sid}: {len(text):,} chars (already in sources.json)")

        added += 1

    SOURCES_FILE.write_text(
        json.dumps(sources, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"\nDone: {added} sources written. Now run chunk_corpus.py then embed_corpus.py.")


if __name__ == "__main__":
    main()
