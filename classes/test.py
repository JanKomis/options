from option import Option

opt = Option(S=142.27, K=142, T_days=25, r=0.0175, sigma=0.2269, dividend= 0.016 ,option_type='call')
print(f"Option price: {opt.price}")