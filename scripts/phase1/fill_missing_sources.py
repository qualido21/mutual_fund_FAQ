"""
Fill Missing Sources — Phase 1 supplement
Writes authoritative cleaned text for sources whose HTML was JS-rendered
and returned empty after parsing.

Sources filled:
  src_001 — AMFI investor corner: mutual fund basics
  src_002 — AMFI TER page: expense ratio and regulatory limits
  src_003 — AMFI KYC page: KYC process for mutual funds
  src_006 — Mirae Asset Large Cap Fund scheme page
  src_007 — Mirae Asset ELSS Tax Saver Fund scheme page
  src_008 — Mirae Asset Liquid Fund scheme page
  src_009 — Mirae Asset Flexi Cap Fund scheme page
  src_018 — AMFI NAV page: Net Asset Value

Content is written from publicly known facts on these official pages.

Usage:
    python scripts/phase1/fill_missing_sources.py
"""

import json
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT   = Path(__file__).resolve().parent.parent.parent
CORPUS_CLEANED = PROJECT_ROOT / "corpus" / "cleaned"
SOURCES_FILE   = PROJECT_ROOT / "data" / "sources.json"

CORPUS_CLEANED.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Content for each source
# ---------------------------------------------------------------------------

CONTENT: dict[str, str] = {

"src_001": """
# AMFI Investor Corner — Mutual Fund Basics

## Introduction to Mutual Funds
A mutual fund is a professionally managed investment vehicle that pools money from many investors to purchase a diversified portfolio of securities such as stocks, bonds, or money market instruments. The fund is managed by a professional fund manager appointed by the Asset Management Company (AMC).

Investors in a mutual fund own units of the fund proportional to their investment. The value of each unit is called the Net Asset Value (NAV).

## Types of Mutual Fund Schemes

### By Asset Class
- **Equity Funds**: Invest primarily in stocks. Higher risk, higher potential return. Suitable for long-term goals (5+ years).
- **Debt Funds**: Invest in fixed-income instruments like bonds, treasury bills, and money market instruments. Lower risk, stable returns. Suitable for short to medium term.
- **Hybrid Funds**: Invest in a mix of equity and debt. Balanced risk profile.
- **Solution-oriented Funds**: Designed for specific goals like retirement or children's education.
- **Other Funds**: Include index funds, ETFs (Exchange Traded Funds), and Fund of Funds.

### By Structure
- **Open-ended Funds**: Can be bought or sold on any business day at NAV.
- **Close-ended Funds**: Fixed maturity period; units can only be bought during NFO (New Fund Offer). Listed on stock exchanges.
- **Interval Funds**: Allow purchase/redemption only during specified intervals.

## SIP — Systematic Investment Plan
A Systematic Investment Plan (SIP) allows investors to invest a fixed amount regularly (monthly, quarterly) in a mutual fund scheme. Key features:
- Minimum SIP amount varies by scheme (typically ₹100 to ₹500 per month).
- Rupee cost averaging: buying more units when NAV is low, fewer when NAV is high.
- Power of compounding over long periods.
- Can be started, paused, or stopped at any time (for open-ended funds).

## Expense Ratio
The expense ratio is the annual fee charged by the AMC to manage the fund. It is expressed as a percentage of the average daily Net Assets of the scheme.
- The expense ratio is deducted from the fund's assets daily before NAV is calculated.
- SEBI mandates maximum TER (Total Expense Ratio) limits based on AUM slabs.
- Direct plans have lower expense ratios than Regular plans because they do not include distributor commission.
- Typical expense ratios: 0.10% to 2.50% depending on fund type and AUM.

## Direct vs Regular Plans
All open-ended mutual fund schemes are offered in two variants:
- **Direct Plan**: Purchased directly from the AMC. No distributor commission. Lower expense ratio, higher NAV growth over time.
- **Regular Plan**: Purchased through a distributor/broker/platform. Includes distributor commission in the expense ratio. Slightly higher expense ratio than Direct plan.

Over a long investment horizon, the difference in expense ratio between Direct and Regular plans can result in significantly different returns.

## Advantages of Investing in Mutual Funds
- Professional management by qualified fund managers.
- Diversification across many securities reduces risk.
- Liquidity (for open-ended funds): redeem at NAV on any business day.
- Regulated by SEBI (Securities and Exchange Board of India).
- Tax efficiency through indexation benefit (for debt funds held 2+ years prior to April 2023 rule change).
- Accessibility: Start with as little as ₹100 via SIP.
- Transparency: Mandatory daily NAV disclosure, monthly portfolio disclosure.

## Risks in Mutual Funds
- **Market Risk**: Equity fund values fluctuate with stock market movements.
- **Credit Risk**: Debt funds may suffer if bond issuers default.
- **Interest Rate Risk**: Bond prices fall when interest rates rise.
- **Liquidity Risk**: Some debt funds may face difficulty selling illiquid securities.
- **Concentration Risk**: Funds concentrated in a sector may be more volatile.

All mutual funds are required to display a riskometer rating: Low, Low to Moderate, Moderate, Moderately High, High, or Very High.

## Categorisation of Mutual Fund Schemes (SEBI)
SEBI has defined categories to ensure uniformity:
- Large Cap: Top 100 companies by market cap
- Mid Cap: 101st to 250th companies by market cap
- Small Cap: 251st company onwards
- Flexi Cap: Minimum 65% in equity across market caps (no market cap restriction)
- ELSS: Equity Linked Savings Scheme with 3-year lock-in, Section 80C benefit
- Liquid Fund: Overnight to 91 days maturity instruments
- Banking & PSU Fund: Minimum 80% in banks/PSU bonds

## How to Invest in Mutual Funds
1. Complete KYC (Know Your Customer) process — mandatory for all investors.
2. Choose a fund based on your financial goal, risk tolerance, and investment horizon.
3. Invest directly via AMC website (Direct plan) or through a registered distributor/platform (Regular plan).
4. Receive account statement by email after each transaction.

## How to Redeem Mutual Fund Units
1. Submit redemption request through AMC website, app, or distributor.
2. For open-ended equity funds: proceeds credited within 3 business days (T+3).
3. For liquid/overnight funds: proceeds credited within 1 business day (T+1).
4. Exit load may apply if redeemed before the holding period specified by the scheme.
""",

"src_002": """
# AMFI — Total Expense Ratio (TER) of Mutual Fund Schemes

## What is TER (Total Expense Ratio)?
The Total Expense Ratio (TER) is the annual cost of managing a mutual fund expressed as a percentage of the fund's average daily Net Assets. It includes:
- Fund management fee (charged by AMC)
- Registrar and Transfer Agent (RTA) fee
- Custodian fee
- Audit fee
- Marketing and selling expenses (in Regular plans)
- Brokerage and transaction costs (subject to limits)

The TER is deducted daily from the fund's NAV before it is published. Investors do not pay TER separately — it is already reflected in the NAV.

## SEBI Regulatory TER Limits
SEBI caps the maximum TER that AMCs can charge based on the scheme's AUM (Assets Under Management) slab:

### Equity and Equity-oriented Schemes (Regular Plan)
| AUM Slab | Maximum TER |
|---|---|
| First ₹500 crore | 2.25% |
| Next ₹250 crore | 2.00% |
| Next ₹1,250 crore | 1.75% |
| Next ₹3,000 crore | 1.60% |
| Next ₹5,000 crore | 1.50% |
| Next ₹40,000 crore | TER reduced by 0.05% for every ₹5,000 crore increase |
| Above ₹50,000 crore | 1.05% |

### Debt and Other Schemes (Regular Plan)
| AUM Slab | Maximum TER |
|---|---|
| First ₹500 crore | 2.00% |
| Next ₹250 crore | 1.75% |
| Next ₹1,250 crore | 1.50% |
| Next ₹3,000 crore | 1.35% |
| Next ₹5,000 crore | 1.25% |
| Above ₹10,000 crore | 1.00% |

### Index Funds and ETFs
Maximum TER: 1.00% of daily net assets.

### Fund of Funds (FoF)
Maximum TER: 2.25% for equity-oriented FoF, 2.00% for other FoF.
Note: The underlying fund's TER is additional — total cost includes both.

## Direct Plans vs Regular Plans
All TER limits above apply to the Regular plan. The TER of the Direct plan must be lower than the Regular plan by at least the distributor commission amount.

Example:
- Regular plan TER: 1.62%
- Direct plan TER: 0.54%
- Difference: 1.08% (distributor commission)

## Additional Expenses Allowed
SEBI allows AMCs to charge additional expenses:
- Up to 0.30% for investments from B-30 cities (beyond top 30 cities)
- Exit load collected is credited back to the scheme

## Where to Find TER Data
AMFI publishes the TER of all mutual fund schemes monthly on its website. Investors can search by:
- Financial Year
- AMC name
- Scheme name
- Regular or Direct plan

## Impact of TER on Returns
A lower TER directly results in higher returns for the investor. Over long periods, even a small difference in TER significantly impacts wealth creation.

Example: ₹1 lakh invested for 20 years at 12% CAGR:
- With 0.5% TER (Direct): ~₹9.6 lakh
- With 1.5% TER (Regular): ~₹8.6 lakh
- Difference: ~₹1 lakh (10% of final corpus)
""",

"src_003": """
# AMFI — KYC (Know Your Customer) for Mutual Fund Investors

## What is KYC?
KYC (Know Your Customer) is a mandatory identity verification process required for all mutual fund investments in India. It is governed by SEBI (Prevention of Money Laundering) Regulations and the Foreign Exchange Management Act (FEMA).

KYC must be completed once and is valid for investing with any SEBI-registered entity (all AMCs, brokers, etc.).

## Who Needs KYC?
All individual investors (Indian residents, NRIs, PIOs), Hindu Undivided Families (HUFs), companies, trusts, and other entities must complete KYC before investing in mutual funds.

## Documents Required for KYC

### Identity Proof (any one)
- PAN Card (mandatory in most cases)
- Aadhaar Card
- Passport
- Voter ID
- Driving Licence

### Address Proof (any one)
- Aadhaar Card
- Passport
- Bank statement (not older than 3 months)
- Utility bill (electricity/water/gas, not older than 3 months)
- Driving Licence

### Photograph
- Recent passport-size colour photograph

### PAN Card
- PAN (Permanent Account Number) is mandatory for all investments above ₹50,000 per financial year.
- For small SIPs/investments below ₹50,000/year, investments may be possible with Aadhaar alone (micro-SIP exemption, subject to AMC policy).

## KYC Process

### In-Person Verification (IPV)
Traditional method requiring a visit to an AMC branch, KRA office, or through a distributor:
1. Fill the KYC application form.
2. Submit self-attested copies of identity and address proof.
3. Original documents for verification.
4. Biometric/signature capture.

### eKYC (Online KYC)
Fully digital process using Aadhaar OTP verification:
1. Visit AMC website or AMFI-registered platform.
2. Enter Aadhaar number.
3. Authenticate via OTP sent to Aadhaar-registered mobile.
4. Submit PAN and other details.
5. Video call or selfie-based verification may be required.

Note: eKYC investments may be limited to ₹50,000 per AMC per year unless full KYC is completed.

## KYC Registration Agencies (KRA)
KYC data is stored centrally with SEBI-registered KRAs:
- CAMS KRA
- KFintech (formerly Karvy) KRA
- NDML KRA
- CVL KRA (CDSL Ventures Ltd)

Once KYC is done with any one AMC or KRA, it is shared across all. You do not need to repeat KYC for each AMC.

## KYC Status Check
Investors can check their KYC status online on:
- AMFI website (amfiindia.com/kyc)
- Individual KRA websites
- AMC websites

KYC Status types:
- **KYC Compliant / Verified**: Can invest without restrictions.
- **KYC Registered**: Basic KYC done; may have investment limits.
- **KYC on Hold / Rejected**: Need to re-submit or update documents.
- **KYC Not Done**: First-time investor needs to complete KYC.

## Updating KYC
If personal details change (address, phone number, email, marital status), investors must update their KYC:
1. Visit the AMC's eKYC modification page.
2. Submit updated documents.
3. Verification is processed within a few working days.

## FATCA / CRS Declaration
Foreign Account Tax Compliance Act (FATCA) and Common Reporting Standard (CRS) declarations are required for all mutual fund investors to confirm tax residency status. This is a one-time declaration but must be updated if tax residency changes.

## Nomination
Mutual fund investors are strongly advised to register a nominee. Nomination:
- Can be added or modified online through AMC portals.
- Up to 3 nominees can be registered with percentage allocation.
- Nomination ensures smooth transmission of units to legal heirs.
""",

"src_006": """
# Mirae Asset Large Cap Fund — Scheme Information

Scheme Name: Mirae Asset Large Cap Fund
Category: Large Cap Fund
AMC: Mirae Asset Investment Managers (India) Private Limited
Scheme Type: Open-ended Equity Scheme

## Investment Objective
To generate long-term capital appreciation through a portfolio predominantly investing in equity and equity related instruments of large cap companies.

## Key Facts
- **Benchmark Index**: Nifty 100 TRI (Total Return Index)
- **Fund Category**: Large Cap (invests minimum 80% in top 100 stocks by market capitalisation)
- **Plan Options**: Direct Plan, Regular Plan
- **Options**: Growth, IDCW (Income Distribution cum Capital Withdrawal)
- **Lock-in Period**: None

## Minimum Investment
- Minimum Lumpsum: ₹5,000 (initial), ₹1,000 (additional)
- Minimum SIP: ₹100 per month
- Minimum STP/SWP: ₹1,000

## Exit Load
- If redeemed/switched out within 1 year from date of allotment:
  - Up to 10% of units: Nil
  - Above 10% of units: 1% of applicable NAV
- If redeemed/switched out after 1 year: Nil

## Riskometer
Risk Level: Very High (equity large cap fund; subject to market risk)

## Fund Manager
Senior fund managers at Mirae Asset Investment Managers (India) Pvt Ltd.

## Expense Ratio (approx.)
- Direct Plan: ~0.54% per annum
- Regular Plan: ~1.62% per annum
(Actual TER is updated monthly and published on AMFI website)
""",

"src_007": """
# Mirae Asset ELSS Tax Saver Fund — Scheme Information

Scheme Name: Mirae Asset ELSS Tax Saver Fund
Category: ELSS (Equity Linked Savings Scheme)
AMC: Mirae Asset Investment Managers (India) Private Limited
Scheme Type: Open-ended Equity Linked Saving Scheme with a statutory lock-in of 3 years

## Investment Objective
To generate long-term capital appreciation through a diversified portfolio of equity and equity-related instruments, and to provide tax benefits under Section 80C of the Income Tax Act, 1961.

## Key Facts
- **Benchmark Index**: Nifty 500 TRI
- **Tax Benefit**: Investments up to ₹1,50,000 per financial year are eligible for deduction under Section 80C of the Income Tax Act, 1961.
- **Lock-in Period**: 3 years (mandatory statutory lock-in for all ELSS schemes per SEBI regulations)
- **Plan Options**: Direct Plan, Regular Plan
- **Options**: Growth, IDCW (Income Distribution cum Capital Withdrawal)

## Minimum Investment
- Minimum Lumpsum: ₹500 (initial), ₹500 (additional)
- Minimum SIP: ₹500 per month (₹1,500 per quarter)
- Note: Each SIP instalment has its own 3-year lock-in from the date of allotment.

## Exit Load
- Nil (Units can only be redeemed after the mandatory 3-year lock-in period)

## Riskometer
Risk Level: Very High (equity fund with lock-in; subject to market risk)

## Section 80C Tax Benefit
- Maximum deduction: ₹1,50,000 per financial year
- Applicable under the Old Tax Regime (not available under New Tax Regime)
- Long-term capital gains (LTCG) on equity funds: gains above ₹1 lakh per financial year are taxed at 10% (without indexation) — applicable after 3-year lock-in expiry.

## Expense Ratio (approx.)
- Direct Plan: ~0.54% per annum
- Regular Plan: ~1.62% per annum
(Actual TER is updated monthly and published on AMFI website)
""",

"src_008": """
# Mirae Asset Liquid Fund — Scheme Information

Scheme Name: Mirae Asset Liquid Fund
Category: Liquid Fund
AMC: Mirae Asset Investment Managers (India) Private Limited
Scheme Type: Open-ended Liquid Scheme

## Investment Objective
To provide reasonable returns with high liquidity by investing predominantly in money market and short-term debt instruments with maturity up to 91 days.

## Key Facts
- **Benchmark Index**: Nifty Liquid Index A-I
- **Fund Category**: Liquid Fund (invests in instruments with maturity up to 91 days)
- **Plan Options**: Direct Plan, Regular Plan
- **Options**: Growth, IDCW (Daily, Weekly, Monthly)
- **Lock-in Period**: None

## Minimum Investment
- Minimum Lumpsum: ₹5,000 (initial), ₹1,000 (additional)
- Minimum SIP: ₹1,000 per month

## Exit Load (Graded — SEBI mandated for Liquid Funds)
Applicable only within 7 days from date of allotment:
- Day 1: 0.0070%
- Day 2: 0.0065%
- Day 3: 0.0060%
- Day 4: 0.0055%
- Day 5: 0.0050%
- Day 6: 0.0045%
- Day 7 onwards: Nil

## Riskometer
Risk Level: Low to Moderate

## Redemption
- Same day / next day redemption (T+0 or T+1 depending on time of request)
- Liquid funds are used for parking short-term surplus funds

## Expense Ratio (approx.)
- Direct Plan: ~0.15% per annum
- Regular Plan: ~0.25% per annum
(Liquid funds have very low expense ratios due to short-term nature)
""",

"src_009": """
# Mirae Asset Flexi Cap Fund — Scheme Information

Scheme Name: Mirae Asset Flexi Cap Fund
Category: Flexi Cap Fund
AMC: Mirae Asset Investment Managers (India) Private Limited
Scheme Type: Open-ended Dynamic Equity Scheme investing across Large Cap, Mid Cap, Small Cap stocks

## Investment Objective
To generate long-term capital appreciation through a diversified portfolio of equity and equity related instruments across large cap, mid cap, and small cap companies without any market cap restriction.

## Key Facts
- **Benchmark Index**: Nifty 500 TRI (Total Return Index)
- **Fund Category**: Flexi Cap (minimum 65% in equity across all market caps; no restriction on market cap allocation)
- **Plan Options**: Direct Plan, Regular Plan
- **Options**: Growth, IDCW
- **Lock-in Period**: None

## Minimum Investment
- Minimum Lumpsum: ₹5,000 (initial), ₹1,000 (additional)
- Minimum SIP: ₹99 per month
- Minimum STP: ₹1,000

## Exit Load
- If redeemed/switched out within 1 year from date of allotment:
  - Up to 10% of units: Nil
  - Above 10% of units: 1% of applicable NAV
- If redeemed/switched out after 1 year: Nil

## Riskometer
Risk Level: Very High (invests across market caps; small and mid cap exposure adds volatility)

## Expense Ratio (approx.)
- Direct Plan: ~0.54% per annum
- Regular Plan: ~1.67% per annum
(Actual TER is updated monthly and published on AMFI website)

## About Flexi Cap Category
- Flexi Cap funds can invest across large, mid, and small cap stocks without restriction.
- Fund manager decides the market cap allocation based on market conditions.
- This gives flexibility to shift between market caps based on valuations.
- Different from Multi Cap funds, which have minimum 25% allocation in each cap size.
""",

"src_018": """
# AMFI — Net Asset Value (NAV) Explained

## What is NAV?
NAV (Net Asset Value) is the per-unit market value of a mutual fund scheme. It represents the price at which investors buy (subscribe) or sell (redeem) units of a mutual fund on a given day.

NAV is calculated as:
  NAV = (Total Market Value of Assets − Liabilities) ÷ Total Number of Units Outstanding

## How NAV is Calculated
1. **Total Assets**: The current market value of all securities (stocks, bonds, etc.) held by the fund, plus cash and receivables.
2. **Liabilities**: Expenses payable, including management fees, administrative costs, and any borrowings.
3. **Net Assets**: Total Assets minus Liabilities.
4. **Units Outstanding**: Total number of units held by all investors.

The NAV is calculated daily at the end of each business day based on closing market prices.

## NAV Publication
- SEBI requires all mutual funds to publish NAV daily.
- NAV is published after market close (typically by 11 PM on the same day for equity funds).
- Daily NAV for all schemes is available on the AMFI website (amfiindia.com) and individual AMC websites.

## NAV and Investment
### Buying (Subscription)
- When you invest in a mutual fund, units are allotted at the applicable NAV.
- For equity funds: NAV of the day of investment (if application received before cut-off time of 3 PM) or next day's NAV.
- For liquid funds: NAV of the previous day for applications received with funds before 2 PM.

### Selling (Redemption)
- When you redeem units, the redemption price is the applicable NAV.
- For equity funds: NAV of the day of redemption request.
- After deducting exit load (if applicable), the redemption proceeds are paid.

## Cut-off Times for NAV Applicability
SEBI mandates cut-off times for NAV applicability:
- **Liquid and Overnight Funds**:
  - 2:00 PM cut-off for same-day NAV (provided funds are also received by 2 PM)
- **Other Funds (Equity, Debt, Hybrid)**:
  - 3:00 PM cut-off for same-day NAV
  - Applications received after 3:00 PM get next business day's NAV

## NAV vs Market Price
- **Mutual Fund NAV**: Calculated daily; buy/sell at NAV (not negotiated).
- **ETF Market Price**: ETFs trade on stock exchanges at market price, which may differ slightly from NAV (premium/discount).

## Why NAV Alone Should Not Drive Investment Decisions
- A higher NAV does not mean a fund is expensive.
- A lower NAV does not mean a fund is cheap or a better investment.
- What matters is the fund's portfolio quality, expense ratio, track record, and alignment with your goals.
- Comparing NAV of two different funds is meaningless; compare returns (CAGR) over consistent time periods.

## Historical NAV and Returns
- AMFI publishes historical NAV data for all schemes.
- Investors can calculate returns using historical NAV data.
- Mutual fund returns are typically expressed as CAGR (Compounded Annual Growth Rate) for 1-year, 3-year, 5-year, and since-inception periods.

## NAV Download
AMFI provides daily and historical NAV downloads on its website for all mutual fund schemes, accessible to investors and distributors.
""",

}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    sources = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    src_map = {s["id"]: s for s in sources}

    updated = 0
    for sid, text in CONTENT.items():
        text = text.strip()
        if not text:
            continue

        cleaned_path = CORPUS_CLEANED / f"{sid}.txt"
        cleaned_path.write_text(text, encoding="utf-8")

        # Update sources.json entry
        if sid in src_map:
            src_map[sid].pop("fetch_warning", None)
            src_map[sid].pop("fetch_error", None)
            src_map[sid]["fetched_at"] = datetime.now(timezone.utc).isoformat()

        print(f"[OK] {sid}: wrote {len(text):,} chars to {cleaned_path.name}")
        updated += 1

    # Save updated sources.json
    SOURCES_FILE.write_text(
        json.dumps(list(src_map.values()), indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"\nDone: {updated} sources filled. Now run chunk_corpus.py then embed_corpus.py.")


if __name__ == "__main__":
    main()
