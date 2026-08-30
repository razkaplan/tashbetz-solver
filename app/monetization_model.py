#!/usr/bin/env python3
"""Revenue scenarios for the site, so the numbers in
marketing_kb/DOMAIN_AND_MONETIZATION.md are reproducible and re-runnable with
real Analytics data instead of guesses.

Everything here is a MODEL, not a measurement. The only inputs that matter are
pageviews (GA4) and, later, real observed RPM from the ad network's own report.
Replace the assumptions at the top the moment you have live numbers.

    python3 app/monetization_model.py            # all tables
    python3 app/monetization_model.py --pv 40000 # your actual monthly pageviews
"""
import argparse

# --- assumptions (edit as reality arrives) ---------------------------------
ILS_PER_USD = 3.4          # rough; only affects the shekel-priced products

# Display RPM = USD per 1,000 pageviews, net to the publisher.
# Israel is a mid-tier ad market and crossword help is a low-intent vertical
# (nobody bids on "5-letter kibbutz"), so these sit well below the US content
# averages you will read in ad-network marketing.
RPM = {
    'adsense (self-serve, IL/Hebrew, low intent)': 1.5,
    'adsense (good layout, high sessions)': 3.0,
    'managed network (Mediavine/Raptive tier)': 6.0,
}
VERCEL_PRO_YEAR = 20 * 12  # ads = commercial use = Hobby is not allowed

PV_LADDER = [5_000, 10_000, 25_000, 50_000, 100_000, 250_000, 500_000, 1_000_000]


def ads_annual(pv_month, rpm):
    """Gross ad revenue per year at a given monthly pageview count."""
    return pv_month / 1000 * rpm * 12


def subs_annual(mau, conv, price_ils):
    """Annual revenue from a monthly subscription at a conversion rate."""
    return mau * conv * price_ils * 12 / ILS_PER_USD


def table_ads(ladder):
    head = ['pageviews/mo'] + [f'${r:.2f} RPM' for r in RPM.values()]
    rows = []
    for pv in ladder:
        cells = [f'{pv:,}']
        for rpm in RPM.values():
            gross = ads_annual(pv, rpm)
            cells.append(f'${gross:,.0f}/yr (${gross/12:,.0f}/mo)')
        rows.append(cells)
    return head, rows


def table_subs():
    head = ['monthly actives', '1% convert', '2% convert', '3% convert']
    rows = []
    for mau in (5_000, 20_000, 50_000):
        cells = [f'{mau:,}']
        for conv in (0.01, 0.02, 0.03):
            v = subs_annual(mau, conv, 15)   # 15 ILS/mo, no-ads + archive tier
            cells.append(f'${v:,.0f}/yr')
        rows.append(cells)
    return head, rows


def md(head, rows):
    out = ['| ' + ' | '.join(head) + ' |',
           '|' + '|'.join(['---'] * len(head)) + '|']
    out += ['| ' + ' | '.join(r) + ' |' for r in rows]
    return '\n'.join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pv', type=int, help='your real monthly pageviews')
    a = ap.parse_args()
    ladder = sorted(set(PV_LADDER + ([a.pv] if a.pv else [])))

    print('## Display ads, gross revenue by traffic\n')
    print(md(*table_ads(ladder)))
    print(f'\nHosting floor once ads are on: ${VERCEL_PRO_YEAR}/yr '
          '(Vercel Pro; ads make the project commercial, Hobby forbids it).')
    for label, rpm in RPM.items():
        be = VERCEL_PRO_YEAR / 12 * 1000 / rpm
        print(f'  break-even at {label}: {be:,.0f} pageviews/mo')

    print('\n## Daily-game subscription (15 ILS/mo: no ads + puzzle archive)\n')
    print(md(*table_subs()))

    print('\n## One direct sponsor vs programmatic, same traffic\n')
    for pv in (50_000, 150_000):
        prog = ads_annual(pv, 3.0)
        print(f'  {pv:,} pv/mo: programmatic ~${prog:,.0f}/yr; '
              f'a direct sponsor at 3,000 ILS/mo = '
              f'${3000 * 12 / ILS_PER_USD:,.0f}/yr '
              f'({3000 * 12 / ILS_PER_USD / prog:.1f}x)')


if __name__ == '__main__':
    main()
