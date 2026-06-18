import re

def rewrite_app_py():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Define the new PAGE_CAPABILITIES
    page_capabilities_code = """
PAGE_CAPABILITIES = {
    "Overview": {"default_period": "1M", "comparison_mode": False, "show_period_filter": True, "show_comparison_filter": False, "show_service_type_filter": False, "additional_module_filters": []},
    "Executive": {"default_period": "1M", "comparison_mode": False, "show_period_filter": True, "show_comparison_filter": False, "show_service_type_filter": False, "additional_module_filters": []},
    "Cockpit": {"default_period": "1M", "comparison_mode": False, "show_period_filter": True, "show_comparison_filter": False, "show_service_type_filter": False, "additional_module_filters": []},
    "Profit & Loss": {"default_period": "1M", "comparison_mode": False, "show_period_filter": True, "show_comparison_filter": False, "show_service_type_filter": False, "additional_module_filters": []},
    "Expense Analysis": {"default_period": "1M", "comparison_mode": False, "show_period_filter": True, "show_comparison_filter": False, "show_service_type_filter": False, "additional_module_filters": []},
    "Labour": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": []},
    "Parts": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": []},
    "Advisors": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": ["Advisor"]},
    "Advisor MoM": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": ["Advisor"]},
    "Discounts": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": []},
    "Leakage Center": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": []},
    "Margin": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": []},
    "Sales Mix": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": []},
    "Locations": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": []},
    "Trends": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": []},
    "Targets": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": []},
    "Reports": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": []},
    "System Health": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": []},
}
"""
    # Insert it near the top
    content = content.replace("from config.settings import HIGH_DISC_ALERT, YOY_DECLINE_ALERT, VOR_ALERT_THRESHOLD", 
                              "from config.settings import HIGH_DISC_ALERT, YOY_DECLINE_ALERT, VOR_ALERT_THRESHOLD\n" + page_capabilities_code)

    # I'll just write the entire script safely in the next steps, to avoid corrupting app.py
    
    pass

if __name__ == '__main__':
    rewrite_app_py()
