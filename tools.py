# ===== الأدوات المحاسبية =====

def calculate_vat(amount: float) -> dict:
    """حاسبة ضريبة القيمة المضافة المصرية 14%"""
    vat = amount * 0.14
    total = amount + vat
    return {
        "amount": amount,
        "vat": round(vat, 2),
        "total": round(total, 2)
    }

def calculate_depreciation(cost: float, salvage: float, years: int) -> dict:
    """حاسبة الاستهلاك بطريقة القسط الثابت"""
    if years <= 0:
        return {"error": "عدد السنوات يجب أن يكون أكبر من صفر"}
    annual = (cost - salvage) / years
    return {
        "cost": cost,
        "salvage": salvage,
        "years": years,
        "annual_depreciation": round(annual, 2),
        "monthly_depreciation": round(annual / 12, 2)
    }

def calculate_gross_profit(revenue: float, cogs: float) -> dict:
    """حاسبة مجمل الربح ونسبته"""
    gross_profit = revenue - cogs
    margin = (gross_profit / revenue * 100) if revenue > 0 else 0
    return {
        "revenue": revenue,
        "cogs": cogs,
        "gross_profit": round(gross_profit, 2),
        "margin_percent": round(margin, 2)
    }

def calculate_break_even(fixed_costs: float, price: float, variable_cost: float) -> dict:
    """حاسبة نقطة التعادل"""
    contribution = price - variable_cost
    if contribution <= 0:
        return {"error": "سعر البيع يجب أن يكون أكبر من التكلفة المتغيرة"}
    units = fixed_costs / contribution
    revenue = units * price
    return {
        "fixed_costs": fixed_costs,
        "contribution_margin": round(contribution, 2),
        "break_even_units": round(units, 2),
        "break_even_revenue": round(revenue, 2)
    }
