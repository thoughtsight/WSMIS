import pandas as pd
import numpy as np
import time

from exp_report import prepare_exp_data, generate_alerts, MONTH_ORDER

MOM_SPIKE_THRESHOLD   = 30.0   # %
SUSTAINED_MONTHS      = 3
HIGH_SHARE_THRESHOLD  = 0.35   # > 35%
NEGATIVE_ALERT        = -40.0  # %

def get_available_months(df):
    return [m for m in MONTH_ORDER if m in df['Month Name'].values]

def precompute_alerts(df):
    alerts_dict = {loc: [] for loc in df['Location'].unique()}
    
    global_months = get_available_months(df)
    if len(global_months) < 2:
        return alerts_dict
        
    sub = df[df['Month Name'].isin(global_months)].copy()
    
    # Identify available months per location to match old behavior
    # Old code: months = get_available_months(sub_loc)
    loc_months_dict = {}
    for loc, grp in sub.groupby('Location'):
        m_list = [m for m in global_months if m in grp['Month Name'].values]
        loc_months_dict[loc] = m_list
        
    amt_pvt = sub.pivot_table(index=['Location', 'Expenses Name'], columns='Month Name', values='Expenses Rs.', aggfunc='sum')
    mom_pvt = sub.pivot_table(index=['Location', 'Expenses Name'], columns='Month Name', values='MoM_Calc', aggfunc='mean')
    
    # Sparse existence mask (did the row explicitly exist in the raw dataframe?)
    exists_mask = ~amt_pvt.isna()
    amt_pvt = amt_pvt.fillna(0)
    
    # Extract location-specific metrics via fast lookup dictionaries
    for loc in amt_pvt.index.levels[0]:
        loc_m = loc_months_dict.get(loc, [])
        if len(loc_m) < 2:
            continue
            
        l_m = loc_m[-1]
        p_m = loc_m[-2]
        
        # Get data for this location only
        try:
            loc_amt = amt_pvt.loc[loc]
            loc_mom = mom_pvt.loc[loc]
            loc_exist = exists_mask.loc[loc]
        except KeyError:
            continue
            
        last_amt = loc_amt[l_m] if l_m in loc_amt.columns else pd.Series(0, index=loc_amt.index)
        prev_amt = loc_amt[p_m] if p_m in loc_amt.columns else pd.Series(0, index=loc_amt.index)
        last_mom = loc_mom[l_m] if l_m in loc_mom.columns else pd.Series(np.nan, index=loc_mom.index)
        
        # 1. Spike Alert
        spike_mask = (last_mom >= MOM_SPIKE_THRESHOLD) & (last_amt > 5000) & last_mom.notna()
        for exp_name, is_true in spike_mask.items():
            if is_true:
                mom_val = last_mom.loc[exp_name]
                amt_val = last_amt.loc[exp_name]
                alerts_dict[loc].append({
                    'type': 'spike', 'icon': '⚠️',
                    'head': f'{exp_name} — Expense Spike in {l_m}',
                    'detail': f'Rose {mom_val:+.1f}% vs {p_m}. Amount: ₹{amt_val:,.0f}',
                    'badge_text': f'+{mom_val:.0f}%', 'badge_cls': 'red'
                })
                
        # 2. Sustained growth
        if len(loc_m) >= SUSTAINED_MONTHS:
            last_n_months = loc_m[-SUSTAINED_MONTHS:]
            mom_last_n = loc_mom[last_n_months]
            valid_sustained = mom_last_n.dropna(how='any')
            all_positive = (valid_sustained > 0).all(axis=1)
            
            first_of_last_n = last_n_months[0]
            amt_last_n = loc_amt[last_n_months]
            
            for exp_name, is_pos in all_positive.items():
                if is_pos:
                    end_amt = amt_last_n.loc[exp_name, l_m]
                    start_amt = amt_last_n.loc[exp_name, first_of_last_n]
                    if start_amt != 0:
                        total_growth = ((end_amt / start_amt) - 1) * 100
                        if total_growth > 10:
                            alerts_dict[loc].append({
                                'type': 'sustained', 'icon': '📈',
                                'head': f'{exp_name} — Rising for {SUSTAINED_MONTHS} Consecutive Months',
                                'detail': f'Grew {total_growth:.1f}% over last {SUSTAINED_MONTHS} months. Review if controllable.',
                                'badge_text': f'↑ {SUSTAINED_MONTHS}m streak', 'badge_cls': 'amber'
                            })
                            
        # 3. High share
        loc_total = last_amt.sum()
        if loc_total > 0:
            for exp_name, amt in last_amt.items():
                share = amt / loc_total
                if share >= HIGH_SHARE_THRESHOLD and amt > 10000:
                    alerts_dict[loc].append({
                        'type': 'share', 'icon': '🔍',
                        'head': f'{exp_name} — High Expense Share in {l_m}',
                        'detail': f'Represents {share*100:.1f}% of total location expenses (₹{amt:,.0f} of ₹{loc_total:,.0f})',
                        'badge_text': f'{share*100:.0f}% share', 'badge_cls': 'amber'
                    })
                    
        # 4. Sudden large drop
        drop_mask = (last_mom <= NEGATIVE_ALERT) & (prev_amt > 50000) & last_mom.notna()
        for exp_name, is_true in drop_mask.items():
            if is_true:
                mom_val = last_mom.loc[exp_name]
                p_amt = prev_amt.loc[exp_name]
                alerts_dict[loc].append({
                    'type': 'drop', 'icon': '📉',
                    'head': f'{exp_name} — Large Drop in {l_m}',
                    'detail': f'Fell {mom_val:.1f}% vs {p_m}. Prev: ₹{p_amt:,.0f}. Verify data.',
                    'badge_text': f'{mom_val:.0f}%', 'badge_cls': 'blue'
                })
                
        # 5. Zero-expense months
        last_2_months = loc_m[-2:]
        for exp_name in loc_amt.index:
            l_amt = last_amt.loc[exp_name]
            l_exist = loc_exist.loc[exp_name, l_m] if l_m in loc_exist.columns else False
            
            # The old code check: len(last_amt) and last_amt[0] == 0
            # Meaning it must explicitly exist in the raw data, and be 0
            if l_exist and l_amt == 0:
                p_amts = loc_amt.loc[exp_name, last_2_months]
                if any(p_amts > 20000):
                    max_p = max(p_amts)
                    alerts_dict[loc].append({
                        'type': 'zero', 'icon': '🔶',
                        'head': f'{exp_name} — Zero in {l_m}',
                        'detail': f'Was ₹{max_p:,.0f} recently. May be missing entry.',
                        'badge_text': '₹0 posted', 'badge_cls': 'amber'
                    })

    return alerts_dict

def test_parity():
    from utils.loaders import load_raw_expense
    df_raw = load_raw_expense("1RUodK2UyYlG86DyGV3-0iyR7bdvkPLgeJJ0VlReHG_A")
    df = prepare_exp_data(df_raw)
    
    t0 = time.time()
    old_alerts = {}
    for loc in df['Location'].unique():
        old_alerts[loc] = generate_alerts(df, loc)
    t1 = time.time()
    
    t2 = time.time()
    new_alerts = precompute_alerts(df)
    t3 = time.time()
    
    print(f"Old time: {t1-t0:.4f}s")
    print(f"New time: {t3-t2:.4f}s")
    
    with open("diffs.txt", "w", encoding="utf-8") as f:
        diff_found = False
        for loc in df['Location'].unique():
            old = old_alerts.get(loc, [])
            new = new_alerts.get(loc, [])
            if len(old) != len(new):
                f.write(f"[{loc}] Count mismatch: Old={len(old)}, New={len(new)}\n")
                # write out the alerts
                f.write(f"Old: {old}\n")
                f.write(f"New: {new}\n")
                diff_found = True
            else:
                for i in range(len(old)):
                    if old[i] != new[i]:
                        f.write(f"[{loc}] Mismatch at index {i}:\n")
                        f.write(f"  Old: {old[i]}\n")
                        f.write(f"  New: {new[i]}\n")
                        diff_found = True
                        
        if not diff_found:
            f.write("✅ 100% PARITY ACHIEVED!\n")
            f.write(f"Performance Improvement: {(t1-t0)/(t3-t2):.1f}x faster\n")
            print("✅ 100% PARITY ACHIEVED!")
        else:
            print("❌ Mismatches found! Check diffs.txt")

if __name__ == "__main__":
    test_parity()
