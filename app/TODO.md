# MEDICVISTA_RETAILER UI Styling - Dashboard Refactor

## Plan Steps
- [x] Inspect current dashboard entrypoints and how `DashboardScreen` is instantiated.

- [ ] Refactor `app/ui/dashboard_screen.py` to reuse shared theming/components from `app/styles.py` (ModernButton/ModernCard/ModernBadge/DataTable where possible).
- [ ] Replace duplicated design system (DesignTokens/ModernStyle/StatCard/SearchBar/ModernTable) with wrappers or mapping to shared components.
- [ ] Align colors, fonts, spacing, and hover states with shared `ColorScheme`/`COLORS`.
- [ ] Ensure table status coloring uses `status_color()` from `app/styles.py`.
- [ ] Keep existing functionality (search, filter combobox, keyboard shortcuts, refresh_data hooks).
- [ ] Run a quick syntax check by importing the dashboard module.

in final smart medcivsta project jab bhi user retailer request se retailer select karke and report type select karte create request kare to medicvista retailer project us particular retailer ke retailer request me vo request dikhegi and jis report type ki reuqeust ki hai us retailer particular report in csv type(db se data banake) me final smart medicvista erp me lake dega ye sab properly karo proper

jab bhi purchase inovice and salesinovice delete ho to uske relted jo bhi entry hai inventory transaction table me uske relted entries  vo bhi delete ho jaye

ek kam karo ye error flaid to load bad screen distance 0 14 aa raha hai when i oepn rasaction hsorty pag check evry files retledt to this medicvista retailer folder

nahi financial year dordown dikh raha hai dashbaord me na ctrl f shrotcut work kar rhaa hai to open financial drodown

yahi sab batch wise ,date wise,stock statement , transaction history me bhi karo jo inveotryscreen me ki hai implmnt karo

jo inventroy screen me implemented hai current stock and fy movement waise hauyahi sab batch wise ,date wise,stock statement , transaction history me bhi karo jo inveotryscreen me ki hai implmnt karo properly

maine 2 purchase inovices add kiye hai 2-10-2025 and 8-10-2025 this is inovice date ye muze fy year select karne pr dikhne chahiye pr ye kisi fy year me nhi dimh rahein medicvidta retaile project so solw htis