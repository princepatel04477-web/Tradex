# Tradly Domain Math Specification & Worked Examples

**Project:** Tradly — AI/ML-Powered Forex Market Intelligence Platform  
**Standard:** IEEE Std 830-1998  
**Domain Invariant:** Money is never a float (`decimal.Decimal` and PostgreSQL `numeric`).

---

## 1. Pip Sizing & Pip Value Formulas

### Definitions
- **Standard Pair (4 decimal places):** $1 \text{ pip} = 0.0001$
- **JPY Pair (2 decimal places):** $1 \text{ pip} = 0.01$
- **1 Standard Lot:** $100,000 \text{ units}$
- **1 Mini Lot:** $10,000 \text{ units}$
- **1 Micro Lot:** $1,000 \text{ units}$

### Formula
$$\text{Pip Value in Quote Currency} = \text{Units} \times \text{Pip Size}$$

If Account Currency == Quote Currency:
$$\text{Pip Value in Account} = \text{Pip Value in Quote}$$

If Account Currency == Base Currency:
$$\text{Pip Value in Account} = \frac{\text{Pip Value in Quote}}{\text{Current Exchange Rate}}$$

---

### Worked Examples (SRS TC-1)

#### Example 1: EUR/USD, 1.0 Standard Lot, USD Account
- $\text{Units} = 100,000$
- $\text{Pip Size} = 0.0001$
- $\text{Pip Value} = 100,000 \times 0.0001 = \$10.0000 / \text{pip}$

#### Example 2: USD/JPY, 0.1 Mini Lot, Rate = 154.50, USD Account
- $\text{Units} = 10,000$
- $\text{Pip Size} = 0.01$
- $\text{Value in JPY} = 10,000 \times 0.01 = 100 \text{ JPY}$
- $\text{Value in USD} = \frac{100 \text{ JPY}}{154.50} = \$0.647249... \approx \$0.6472 / \text{pip}$

#### Example 3: GBP/JPY, 1.0 Standard Lot, Rate = 196.50, USD/JPY = 154.50, USD Account
- $\text{Units} = 100,000$
- $\text{Pip Size} = 0.01$
- $\text{Value in JPY} = 100,000 \times 0.01 = 1,000 \text{ JPY}$
- $\text{Value in USD} = \frac{1,000 \text{ JPY}}{154.50} = \$6.4725 / \text{pip}$

---

## 2. Margin Accounting Formulas

### Required Margin
$$\text{Required Margin} = \frac{\text{Units} \times \text{Entry Price} \times \text{Base-to-Account Rate}}{\text{Leverage}}$$

#### Example: Long 1.0 lot EUR/USD at 1.0850, Leverage = 1:100
- $\text{Required Margin} = \frac{100,000 \times 1.0850}{100} = \$1,085.00$

#### Example: Long 1.0 lot EUR/USD at 1.0850, Leverage = 1:30
- $\text{Required Margin} = \frac{100,000 \times 1.0850}{30} = \$3,616.67$

---

## 3. Account Capital & Risk Triggers

1. **Account Equity (Derived per ADR-0006):**
   $$\text{Equity} = \text{Balance} + \sum \text{Floating P\&L}$$
2. **Used Margin:**
   $$\text{Used Margin} = \sum \text{Required Margin of Open Positions}$$
3. **Free Margin:**
   $$\text{Free Margin} = \max(0, \text{Equity} - \text{Used Margin})$$
4. **Margin Level Percentage:**
   $$\text{Margin Level \%} = \left(\frac{\text{Equity}}{\text{Used Margin}}\right) \times 100$$
5. **Margin Call Warning:** Triggered when $\text{Margin Level \%} < 100\%$
6. **Auto-Liquidation (SRS TC-3):** Triggered when $\text{Margin Level \%} < 50\%$
