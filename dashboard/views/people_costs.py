import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

t = u.t
u.header(t('🧑‍💼 People & Costs', '🧑‍💼 الموظفين والمصاريف'),
         t('Can we manage staff and costs with this data?', 'نقدر ندير الموظفين والمصاريف بالداتا دي؟'), '11_card08_people_costs')

pf = u.people_facts()
k = st.columns(4)
u.kpi(k[0], t('Employees', 'الموظفين'), f"{pf['employees']}", help=t('exactly 8 per branch', '8 بالظبط في كل فرع'))
u.kpi(k[1], t('Branches without a manager', 'فروع من غير مدير'), f"{pf['no_manager']}", inverse=True)
u.kpi(k[2], t('Branches without a cashier', 'فروع من غير كاشير'), f"{pf['no_cashier']}", inverse=True)
u.kpi(k[3], t('Payroll FY2026 vs salaries on the list', 'مرتبات FY2026 مقابل المرتبات المسجلة'), f"{pf['payroll_fy26'] / 1e6:.1f}M / {pf['base_list_year'] / 1e6:.0f}M", inverse=True)

left, right = st.columns(2)
with left:
    pm = pf['paid_per_month']
    fig = go.Figure(go.Scatter(x=pm.index, y=pm.values, mode='lines', line=dict(color=u.ORANGE, width=2.5), name=t('employees paid', 'موظفين اتقبضوا')))
    fig.add_hline(y=pf['employees'], line=dict(color=u.GREY, dash='dash'))
    fig.update_yaxes(title=t('employees paid in the month', 'موظفين اتقبضوا في الشهر'), range=[0, 700])
    u.show(u.style(fig, t(f"Payroll never covers more than {pm.max()} of {pf['employees']} – only {pm.iloc[-1]} in the last month",
                          f"المرتبات عمرها ما غطّت أكتر من {pm.max()} من {pf['employees']} – و {pm.iloc[-1]} بس آخر شهر")))
with right:
    s = pf['salary_by_role']
    fig = go.Figure(go.Bar(x=s.index, y=s.values, marker_color=u.GREY, text=[f'{v:,.0f}' for v in s.values], textposition='outside'))
    fig.update_yaxes(title=t('average base salary 2026, EGP', 'متوسط المرتب 2026، جنيه'), range=[0, s.max() * 1.25])
    u.show(u.style(fig, t('Salary does not depend on the job (cashier ≈ area manager)', 'المرتب مالوش علاقة بالوظيفة (الكاشير ≈ مدير المنطقة)')))

u.honest(t(f"Roles are assigned in rotation (cashier, associate, associate, store manager, clerk, area manager, repeat): "
           f"{pf['no_manager']} branches have no store manager, {pf['no_cashier']} have no cashier, and there are {pf['area_managers']} area managers for 80 branches. "
           "So a workforce-productivity app would give wrong answers – we list the HR data to collect instead.",
           f"الوظايف متوزعة بالتناوب (كاشير، مندوب، مندوب، مدير فرع، أمين مخزن، مدير منطقة، وتتكرر): "
           f"{pf['no_manager']} فرع من غير مدير، و {pf['no_cashier']} من غير كاشير، و {pf['area_managers']} مدير منطقة لـ 80 فرع. "
           "يعني أي تطبيق لإنتاجية الموظفين هيطلع إجابات غلط – فبنكتب داتا الموارد البشرية اللي محتاجين نجمعها."))

op = pf['opex_pct']
fig = go.Figure(go.Bar(x=op.index, y=op.values, marker_color=u.BLUE, text=[f'{v:.0f}%' for v in op.values], textposition='outside'))
fig.update_yaxes(title=t('operating expenses, % of sales', 'المصاريف % من المبيعات'), range=[0, op.max() * 1.25])
u.show(u.style(fig, t('Expenses fall from 31% to 13% of sales – because prices rose faster', 'المصاريف نزلت من 31% لـ 13% من المبيعات – لأن الأسعار زادت أسرع'), height=330))
st.markdown(t(f"- Rent is recorded in only **{pf['rent_months_avg']:.0f} of {pf['months']} months** per branch on average → the rent ledger is incomplete.\n"
              f"- Marketing: **{pf['marketing_ledger'] / 1e6:.1f}M** in the expense ledger vs **{pf['marketing_campaigns'] / 1e6:.1f}M** in the campaign table.",
              f"- الإيجار متسجل في **{pf['rent_months_avg']:.0f} شهر بس من {pf['months']}** لكل فرع في المتوسط → دفتر الإيجار ناقص.\n"
              f"- التسويق: **{pf['marketing_ledger'] / 1e6:.1f} مليون** في دفتر المصاريف مقابل **{pf['marketing_campaigns'] / 1e6:.1f} مليون** في جدول الحملات."))
