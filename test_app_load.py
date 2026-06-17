from streamlit.testing.v1 import AppTest
import traceback

def run_tests():
    pages = [
        "Cockpit", "Overview", "Labour", "Parts", "Margin", "Discounts", 
        "Leakage Center", "Sales Mix", "Advisors", "Advisor MoM", "Locations", 
        "Trends", "Targets", "Reports", "Executive", "Expense Analysis", 
        "Profit & Loss", "Internal Audit"
    ]
    
    print("Initializing AppTest for app.py...")
    try:
        at = AppTest.from_file("app.py", default_timeout=60)
        
        for page in pages:
            print(f"Testing page: {page}...")
            at.session_state["current_page"] = page
            at.run(timeout=300)
            
            if at.exception:
                print(f"Exception encountered while rendering '{page}':")
                for e in at.exception:
                    print(e)
                return False
                
        print("All pages rendered successfully without exceptions.")
        return True
    except Exception as e:
        print(f"Test framework failed with: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_tests()
    if not success:
        exit(1)
    else:
        print("All tests passed.")
