from datetime import datetime

print('Current Date:', datetime.now().strftime('%Y-%m-%d'))
print('')

# Your invoice dates
invoice_dates = ['2025-10-02', '2025-10-08']
print('Your Invoice Dates:', invoice_dates)
print('')

# Calculate FY years
fy_years = []
current_year = datetime.now().year
current_month = datetime.now().month
end_year = current_year + 1 if current_month >= 4 else current_year

for year in range(2024, end_year + 2):
    fy_years.append(f'{year}-{year+1}')

print('Available FY Years:')
for fy in reversed(fy_years):
    start = f'{fy.split("-")[0]}-04-01'
    end = f'{fy.split("-")[1]}-03-31'
    print(f'  FY {fy}: {start} to {end}')
    
    # Check if invoices fall in this FY
    for inv_date in invoice_dates:
        if start <= inv_date <= end:
            print(f'    ✓ Invoice {inv_date} falls in this FY')

print('')
print('Problem: October 2025 falls in FY 2025-2026 (Apr 2025 to Mar 2026)')
print('Check if FY 2025-2026 is available in dropdown!')
