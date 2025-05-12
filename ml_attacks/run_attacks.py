from ml_attacks import weak_attack, medium_attack, strong_attack, extreme_attack

def main():
    print("Running PUF Security Analysis...")
    
    results = {
        "Weak": weak_attack.weak_attack(),
        "Medium": medium_attack.medium_attack(),
        "Strong": strong_attack.strong_attack(),
        "Extreme": extreme_attack.extreme_attack()
    }
    
    print("\n=== Final Results ===")
    for name, acc in results.items():
        resilience = "HIGH" if acc < 0.55 else "MEDIUM" if acc < 0.6 else "LOW"
        print(f"{name:<8}: {acc*100:.2f}% Accuracy ({resilience} resilience)")

if __name__ == "__main__":
    main()