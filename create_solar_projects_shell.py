# Odoo Shell Script to create Solar Projects for Sale Orders
# Usage:
#   python odoo-bin shell -c odoo.conf -d <dbname> < create_solar_projects_shell.py

orders = env['sale.order'].search([('solar_project_id', '=', False)])
print(f"Found {len(orders)} orders without Solar Project.")

for order in orders:
    project_type = 'ground_mounted'
    if order.opportunity_id and getattr(order.opportunity_id, 'solar_lead_type', False):
        if order.opportunity_id.solar_lead_type in ('ground_mounted', 'commercial'):
            project_type = order.opportunity_id.solar_lead_type
    elif order.opportunity_id and order.opportunity_id.tag_ids:
        tag_names = [t.name.upper().strip() for t in order.opportunity_id.tag_ids]
        if 'COMMERCIAL' in tag_names or 'COMMERCIAL / INDUSTRIAL' in tag_names:
            project_type = 'commercial'

    project = env['solar.project'].create({
        'partner_id': order.partner_id.id,
        'sale_order_id': order.id,
        'kw_capacity': getattr(order, 'solar_kw_capacity', 0.0),
        'discom_id': order.solar_discom_id.id if getattr(order, 'solar_discom_id', False) else False,
        'date_start': order.date_order.date() if order.date_order else fields.Date.context_today(order),
        'project_type': project_type,
        'state': 'loa',
    })
    order.with_context(bypass_edit_restriction=True).write({'solar_project_id': project.id})
    print(f"-> Created Solar Project '{project.name}' for Sale Order {order.name}")

env.cr.commit()
print("All projects created and linked successfully!")
