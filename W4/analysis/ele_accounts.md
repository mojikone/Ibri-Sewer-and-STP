# Electricity accounts -> properties per plot

Source: `IBRI ELE ACCOUNTS.kmz` — **33,970 accounts**, EPSG:32640.

## Accounts by category

| Category | Accounts | Share |
|---|---|---|
| domestic | 16,244 | 47.8 % |
| commercial | 9,392 | 27.6 % |
| domestic_additional | 6,344 | 18.7 % |
| government | 967 | 2.8 % |
| agricultural | 523 | 1.5 % |
| crt | 499 | 1.5 % |
| industrial | 1 | 0.0 % |

**24,762 accounts (72.9 %) fall inside a cadastral plot**; 9,208 fall outside (unparceled buildings, road-side services, or cadastre gaps).

## Accounts per plot (agricultural excluded)

- plots with at least one account: **12,523**
- mean **1.95**, median **1**, max **87**
- domestic only: mean **1.46**, median **1**, max **64**

| Accounts on the plot | Plots | Share |
|---|---|---|
| 1 | 9,407 | 75.1 % |
| 2 | 1,556 | 12.4 % |
| 3 | 387 | 3.1 % |
| 4 | 262 | 2.1 % |
| 5 | 134 | 1.1 % |
| 6 or more | 777 | 6.2 % |

## By plot class

| CLASS | Plots with accounts | Mean accounts | Max |
|---|---|---|---|
| B | 9,859 | 1.94 | 87 |
| P | 549 | 1.52 | 19 |
| A | 2,115 | 2.12 | 79 |

## Against the current assumption

The pipeline assumes `PROPS_PER_PLOT = 1.0` for every plot [GAP-5]. Measured on built plots, the mean is **1.94** accounts per plot that has any account.

- built plots in the cadastre: 17,961
- built plots carrying at least one account: 9,859 (54.9 %)

## Inside the W4 test boundary

- accounts: **3,885**

| Category | Accounts |
|---|---|
| domestic | 1,875 |
| commercial | 916 |
| domestic_additional | 893 |
| government | 122 |
| crt | 65 |
| agricultural | 14 |

- plots with accounts: **1,331** (the design currently loads 2,987 units)
- mean accounts per plot **1.93**, max **51**
- plots with 2 or more accounts: **352** (26.4 %) — these are the plots needing more than one connection
